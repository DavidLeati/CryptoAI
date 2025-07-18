# main.py
# Ponto de entrada e lógica central (orquestrador) do robô de trading.
# Esta versão é multithread para analisar múltiplos ativos simultaneamente.

import time
import threading

# Importar configurações centralizadas
import sys
from pathlib import Path
config_path = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_path))

from settings import (
    PAPER_TRADING_MODE, TRADE_VALUE_USD, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    LEVERAGE_LEVEL, LISTA_DE_ATIVOS, INITIAL_BALANCE, UPDATE_INTERVAL, MAX_CONCURRENT_TRADES,
    PRIMARY_TIMEFRAME, SECONDARY_TIMEFRAME, CONFIRMATION_TIMEFRAME, RSI_PERIOD, MACD_FAST, MACD_SLOW, BB_PERIOD,
    PERMITIR_REVERSAO_POSICAO, LOW_QUALITY_TRADES_LIMIT
)

# Importando as funções dos nossos módulos especialistas
from utils.exchange_setup import create_exchange_connection, setup_leverage_for_symbol, test_api_connection, check_account_mode
from utils.data import fetch_data, RealTimeDataManager
from analysis.analysis import find_comprehensive_signal, find_comprehensive_exit_signal, find_integrated_exhaustion_signal_mta

# Importar funções de trading (real ou simulado conforme configuração)
if PAPER_TRADING_MODE:
    from trading.paper_trading import paper_open_long_position as open_long_position
    from trading.paper_trading import paper_open_short_position as open_short_position
    from trading.paper_trading import paper_close_position as close_position
    from trading.paper_trading import paper_save_results
    print("🧪 MODO PAPER TRADING ATIVADO - Nenhuma ordem real será executada!")
else:
    from trading.orders import open_long_position, open_short_position, close_position
    print("💰 MODO TRADING REAL ATIVADO - Ordens reais serão executadas!")

# =============================================================================
# 1. CONFIGURAÇÃO GERAL E RECURSOS COMPARTILHADOS
# =============================================================================

# Converter lista de ativos do settings.py para formato do ccxt
FORMATTED_ASSETS = [f"{asset.replace('USDT', '/USDT:USDT')}" for asset in LISTA_DE_ATIVOS]

# RECURSOS COMPARTILHADOS:
posicoes_info = {symbol: 'MONITORING' for symbol in FORMATTED_ASSETS}
lock_posicoes = threading.Lock() 

# =============================================================================
# 2. A LÓGICA DO WORKER (O QUE CADA THREAD FAZ)
# =============================================================================

def processar_ativo(symbol, client, manager):
    """
    Função principal que cada thread executa para um único ativo.
    VERSÃO ATUALIZADA com lógica de REVERSÃO DE POSIÇÃO.
    """
    print(f"✅ Thread para {symbol} iniciada.")
    last_candle_timestamp = None
    
    while True:
        try:
            # --- 1. Otimização: Verificar se há dados novos antes de analisar ---
            primary_stream_key = f"{symbol}_{PRIMARY_TIMEFRAME}"
            current_data = manager.get_dataframe(primary_stream_key)
            
            if current_data is None or current_data.empty:
                time.sleep(5)
                continue

            current_timestamp = current_data.index[-1]
            if current_timestamp == last_candle_timestamp:
                time.sleep(5) 
                continue

            print(f"🕯️ ({symbol}) Nova vela detectada às {current_timestamp}. Iniciando análise...")
            last_candle_timestamp = current_timestamp
            
            # --- 2. Obter o status atual da posição ---
            with lock_posicoes:
                status_atual = posicoes_info.get(symbol, 'MONITORING')

            # ==========================================================
            # LÓGICA DE ENTRADA (QUANDO NÃO HÁ POSIÇÃO)
            # ==========================================================
            if status_atual == 'MONITORING':
                sinal_info = find_comprehensive_signal(client=client, symbol=symbol, manager=manager)
                sinal_entrada = sinal_info.get('signal', 'AGUARDAR')
                sinal_fonte = sinal_info.get('source', 'NONE')

                with lock_posicoes:
                    num_posicoes_abertas = sum(1 for status in posicoes_info.values() if status != 'MONITORING')

                entrar_no_trade = False
                if sinal_entrada != 'AGUARDAR':
                    if sinal_fonte == 'MTA':
                        print(f"({symbol}) Sinal de ALTA QUALIDADE (MTA) recebido. Tentando entrada...")
                        entrar_no_trade = True
                    elif sinal_fonte == 'FALLBACK' and num_posicoes_abertas < LOW_QUALITY_TRADES_LIMIT: # Limite para trades de baixa qualidade
                        print(f"({symbol}) Sinal de BAIXA QUALIDADE (Fallback) recebido. {num_posicoes_abertas}/{LOW_QUALITY_TRADES_LIMIT} posições de fallback. Tentando entrada...")
                        entrar_no_trade = True
                    elif sinal_fonte == 'FALLBACK':
                        print(f"({symbol}) Sinal de BAIXA QUALIDADE (Fallback) ignorado. Limite de posições de fallback ({num_posicoes_abertas}/{LOW_QUALITY_TRADES_LIMIT}) atingido.")

                if entrar_no_trade:
                    if sinal_entrada == 'COMPRAR':
                        print(f"🚨 ({symbol}) SINAL DE COMPRA DETECTADO! 🚨")
                        if open_long_position(client, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT):
                            with lock_posicoes: posicoes_info[symbol] = 'IN_LONG'
                    
                    elif sinal_entrada == 'VENDER':
                        print(f"🚨 ({symbol}) SINAL DE VENDA DETECTADO! 🚨")
                        if open_short_position(client, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT):
                            with lock_posicoes: posicoes_info[symbol] = 'IN_SHORT'

            # ==========================================================
            # LÓGICA DE POSIÇÃO ATIVA (SAÍDA OU REVERSÃO)
            # ==========================================================
            elif status_atual in ['IN_LONG', 'IN_SHORT']:
                print(f"({symbol}) Posição {status_atual} ativa. Verificando...")
                
                sinal_reversao_detectado = False
                if PERMITIR_REVERSAO_POSICAO:
                    sinal_info = find_comprehensive_signal(client=client, symbol=symbol, manager=manager)
                    sinal_recente = sinal_info.get('signal', 'AGUARDAR')
                    fonte_recente = sinal_info.get('source', 'NONE')
                    
                    # Apenas reverter em sinais de alta qualidade (MTA) para evitar Whipsaws
                    if fonte_recente == 'MTA':
                        if status_atual == 'IN_LONG' and sinal_recente == 'VENDER':
                            print(f"🔄 ({symbol}) SINAL DE REVERSÃO DE ALTA QUALIDADE (LONG -> SHORT) DETECTADO!")
                            sinal_reversao_detectado = True
                            if close_position(client, symbol):
                                if open_short_position(client, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT):
                                    with lock_posicoes: posicoes_info[symbol] = 'IN_SHORT'
                                else:
                                    with lock_posicoes: posicoes_info[symbol] = 'MONITORING'
                        
                        elif status_atual == 'IN_SHORT' and sinal_recente == 'COMPRAR':
                            print(f"🔄 ({symbol}) SINAL DE REVERSÃO DE ALTA QUALIDADE (SHORT -> LONG) DETECTADO!")
                            sinal_reversao_detectado = True
                            if close_position(client, symbol):
                                if open_long_position(client, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT):
                                    with lock_posicoes: posicoes_info[symbol] = 'IN_LONG'
                                else:
                                    with lock_posicoes: posicoes_info[symbol] = 'MONITORING'

                if not sinal_reversao_detectado:
                    print(f"({symbol}) Nenhum sinal de reversão. Verificando saída normal...")
                    position_side = 'LONG' if status_atual == 'IN_LONG' else 'SHORT'
                    sinal_saida = find_integrated_exhaustion_signal_mta(client, symbol, manager, position_side)

                    if sinal_saida:
                        print(f"🚪 ({symbol}) SINAL DE SAÍDA DETECTADO! Fechando posição... 🚪")
                        if close_position(client, symbol):
                            with lock_posicoes:
                                posicoes_info[symbol] = 'MONITORING'
            
            time.sleep(1) # Sleep curto, pois a lógica de vela já controla o timing

        except Exception as e:
            print(f"‼️ ({symbol}) ERRO CRÍTICO na thread: {e}")
            time.sleep(15)

# =============================================================================
# 3. O MAESTRO (FUNÇÃO PRINCIPAL)
# =============================================================================

realtime_data_manager = RealTimeDataManager()

def main():
    """
    Função principal que prepara o ambiente e dispara as threads de análise.
    """
    mode_text = "PAPER TRADING (SIMULAÇÃO)" if PAPER_TRADING_MODE else "TRADING REAL"
    print(f"--- INICIANDO O ROBÔ DE TRADING MULTITHREAD - {mode_text} ---")
    
    if PAPER_TRADING_MODE:
        print("💡 Modo simulação ativo - testando capacidade de geração de lucro sem usar dinheiro real")
        print(f"📊 Saldo inicial da simulação: ${INITIAL_BALANCE}")
    
    # 1. Inicializa a conexão única com a exchange
    client = create_exchange_connection()
    if not client:
        print("Falha na inicialização da exchange. Encerrando o bot.")
        return

    # 2. Testa a conexão e permissões
    if not test_api_connection(client):
        print("Falha no teste de conexão. Encerrando o bot.")
        return

    # 3. Verifica o modo da conta (Multi-Assets vs Single-Asset)
    check_account_mode(client)

    # 4. Inicia os streams de dados em tempo real
    print("🚀 Iniciando todos os streams de dados em tempo real...")
    timeframes_necessarios = [PRIMARY_TIMEFRAME, SECONDARY_TIMEFRAME, CONFIRMATION_TIMEFRAME]
    for symbol in FORMATTED_ASSETS:
        for tf in timeframes_necessarios:
            realtime_data_manager.start_stream(symbol, tf, limit=300, client=client, populate_historical=True)
    
    # 5. Aguardar dados suficientes antes de continuar
    print("⏳ Aguardando dados suficientes para análise...")
    min_required_bars = max(14, 26, 20, 200) + 3  # RSI, MACD, BB, EMA_FILTER + buffer
    
    all_streams_ready = True
    for symbol in FORMATTED_ASSETS:
        for tf in timeframes_necessarios:
            stream_key = f"{symbol}_{tf}"
            if not realtime_data_manager.wait_for_sufficient_data(stream_key, min_required_bars, timeout=60):
                print(f"❌ Falha ao obter dados suficientes para {stream_key}")
                all_streams_ready = False
    
    if not all_streams_ready:
        print("❌ Nem todos os streams obtiveram dados suficientes. Continuando mesmo assim...")
    else:
        print("✅ Todos os streams têm dados suficientes para análise.")
    
    print("✅ Todos os streams foram iniciados.")

    # 4. Cria e inicia uma thread para cada ativo na watchlist
    threads = []
    if not PAPER_TRADING_MODE:
        print(f"📋 Configurando alavancagem para {len(FORMATTED_ASSETS)} símbolos...")
        for symbol in FORMATTED_ASSETS:
            print(f"🔧 Preparando {symbol}...")
            setup_leverage_for_symbol(client, symbol, LEVERAGE_LEVEL)  # Sempre continua
            thread = threading.Thread(target=processar_ativo, args=(symbol, client, realtime_data_manager))
            threads.append(thread)
            thread.start()
            time.sleep(0.2)  # Pausa reduzida para inicialização mais rápida
    else:
        print(f"🧪 Iniciando simulação com {len(FORMATTED_ASSETS)} símbolos...")
        for symbol in FORMATTED_ASSETS:
            thread = threading.Thread(target=processar_ativo, args=(symbol, client, realtime_data_manager))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # Inicialização ainda mais rápida para simulação


    print(f"\n✅ {len(threads)} threads de análise estão rodando em paralelo.")
    if PAPER_TRADING_MODE:
        print("🧪 Modo simulação ativo - acompanhe os resultados virtuais!")
        print("💾 Resultados serão salvos automaticamente em 'paper_trading_results.json'")
    else:
        print("💰 Bot operacional com dinheiro real!")
    
    print("Pressione Ctrl+C para encerrar.")

    # 5. Mantém a thread principal viva e salva resultados periodicamente se for simulação
    try:
        if PAPER_TRADING_MODE:
            # Salvar resultados a cada 10 minutos em modo simulação
            import signal
            
            def save_on_exit(signum, frame):
                print("\n🛑 Encerrando bot...")
                if PAPER_TRADING_MODE:
                    print("💾 Salvando resultados finais da simulação...")
                    paper_save_results()
                exit(0)
            
            signal.signal(signal.SIGINT, save_on_exit)
            
            # Loop principal com salvamento periódico
            last_save = time.time()
            while True:
                time.sleep(60)  # Verificar a cada minuto
                if time.time() - last_save > 600:  # Salvar a cada 10 minutos
                    print("💾 Salvamento automático dos resultados...")
                    paper_save_results()
                    last_save = time.time()
        else:
            # Modo normal - apenas aguardar as threads
            for thread in threads:
                thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando bot...")
        if PAPER_TRADING_MODE:
            print("💾 Salvando resultados finais da simulação...")
            paper_save_results()

# =============================================================================
# PONTO DE ENTRADA DO PROGRAMA
# =============================================================================

if __name__ == '__main__':
    main()