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
    PRIMARY_TIMEFRAME, SECONDARY_TIMEFRAME, CONFIRMATION_TIMEFRAME, RSI_PERIOD, MACD_FAST, MACD_SLOW, BB_PERIOD
)

# Importando as funções dos nossos módulos especialistas
from utils.exchange_setup import create_exchange_connection, setup_leverage_for_symbol, test_api_connection, check_account_mode
from utils.data import fetch_data, RealTimeDataManager
from analysis.analysis import find_comprehensive_signal, find_comprehensive_exit_signal

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

def processar_ativo(symbol, client):
    """
    Função principal que cada thread executa para um único ativo.
    Gerencia o ciclo de vida completo de uma operação: entrar, monitorar e sair.
    """
    print(f"✅ Thread para {symbol} iniciada.")
    
    while True:
        try:
            with lock_posicoes:
                status_atual = posicoes_info.get(symbol, 'MONITORING')

            if status_atual == 'MONITORING':
                print(f"({symbol}) Monitorando para um sinal de ENTRADA...")
                market_data = fetch_data(client, symbol, timeframe='1m', limit=100)
                if market_data is None:
                    time.sleep(5)
                    continue

                # Usar análise multi-timeframe passando client e symbol
                sinal_entrada = find_comprehensive_signal(market_data, client=client, symbol=symbol)
                
                if sinal_entrada == 'COMPRAR':
                    print(f"🚨 SINAL DE COMPRA DETECTADO PARA {symbol}! 🚨")
                    sucesso = open_long_position(client, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT)
                    if sucesso:
                        print(f"Posição LONG para {symbol} aberta com sucesso.")
                        with lock_posicoes:
                            posicoes_info[symbol] = 'IN_LONG'
                
                elif sinal_entrada == 'VENDER':
                    print(f"🚨 SINAL DE VENDA DETECTADO PARA {symbol}! 🚨")
                    sucesso = open_short_position(client, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT)
                    if sucesso:
                        print(f"Posição SHORT para {symbol} aberta com sucesso.")
                        with lock_posicoes:
                            posicoes_info[symbol] = 'IN_SHORT'

            elif status_atual in ['IN_LONG', 'IN_SHORT']:
                print(f"({symbol}) Posição {status_atual} ativa. Monitorando para um sinal de SAÍDA...")
                market_data = fetch_data(client, symbol, timeframe='1m', limit=100)
                if market_data is None:
                    time.sleep(10)
                    continue

                position_side = 'LONG' if status_atual == 'IN_LONG' else 'SHORT'
                sinal_saida = find_comprehensive_exit_signal(market_data, position_side)

                if sinal_saida:
                    print(f"🚪 SINAL DE SAÍDA DETECTADO PARA {symbol}! Fechando posição... 🚪")
                    sucesso = close_position(client, symbol)
                    if sucesso:
                        print(f"Posição para {symbol} fechada com sucesso.")
                        with lock_posicoes:
                            posicoes_info[symbol] = 'MONITORING'
                    else:
                        print(f"ERRO ao tentar fechar a posição de {symbol}. Manterá o estado para nova tentativa.")

            time.sleep(5)

        except Exception as e:
            print(f"ERRO CRÍTICO na thread de {symbol}: {e}")
            with lock_posicoes:
                posicoes_info[symbol] = 'MONITORING'
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
            realtime_data_manager.start_stream(symbol, tf, limit=300)
    print("✅ Todos os streams foram iniciados.")

    # 4. Cria e inicia uma thread para cada ativo na watchlist
    threads = []
    if not PAPER_TRADING_MODE:
        print(f"📋 Configurando alavancagem para {len(FORMATTED_ASSETS)} símbolos...")
        for symbol in FORMATTED_ASSETS:
            print(f"🔧 Preparando {symbol}...")
            setup_leverage_for_symbol(client, symbol, LEVERAGE_LEVEL)  # Sempre continua
            thread = threading.Thread(target=processar_ativo, args=(symbol, client))
            threads.append(thread)
            thread.start()
            time.sleep(0.2)  # Pausa reduzida para inicialização mais rápida
    else:
        print(f"🧪 Iniciando simulação com {len(FORMATTED_ASSETS)} símbolos...")
        for symbol in FORMATTED_ASSETS:
            thread = threading.Thread(target=processar_ativo, args=(symbol, client))
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