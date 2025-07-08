# main.py
# Ponto de entrada e lógica central (orquestrador) do robô de trading.
# Esta versão é multithread para analisar múltiplos ativos simultaneamente.

import time
import threading

# Importando as funções dos nossos módulos especialistas (CORRIGIDO)
from exchange_setup import create_exchange_connection, setup_leverage_for_symbol
from data import fetch_data
from analysis import find_momentum_signal, find_exhaustion_signal
from orders import open_long_position, open_short_position, close_position

# =============================================================================
# 1. CONFIGURAÇÃO GERAL E RECURSOS COMPARTILHADOS
# =============================================================================

LISTA_DE_ATIVOS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'BNB/USDT:USDT', 'XRP/USDT:USDT', 'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'MATIC/USDT:USDT', 
                  'DOT/USDT:USDT', 'LTC/USDT:USDT', 'AVAX/USDT:USDT', 'LINK/USDT:USDT', 'UNI/USDT:USDT', 'SHIB/USDT:USDT', 'TRX/USDT:USDT', 'ATOM/USDT:USDT']
TRADE_VALUE_USD = 10.00
STOP_LOSS_PCT = 1.5
LEVERAGE_LEVEL = 10

# RECURSOS COMPARTILHADOS:
posicoes_info = {symbol: 'MONITORING' for symbol in LISTA_DE_ATIVOS}
lock_posicoes = threading.Lock() 

# =============================================================================
# 2. A LÓGICA DO WORKER (O QUE CADA THREAD FAZ)
# =============================================================================

def processar_ativo(symbol, exchange):
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
                market_data = fetch_data(exchange, symbol, timeframe='1m', limit=100)
                if market_data is None:
                    time.sleep(5)
                    continue

                sinal_entrada = find_momentum_signal(market_data)
                
                if sinal_entrada == 'COMPRAR':
                    print(f"🚨 SINAL DE COMPRA DETECTADO PARA {symbol}! 🚨")
                    sucesso = open_long_position(exchange, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT)
                    if sucesso:
                        print(f"Posição LONG para {symbol} aberta com sucesso.")
                        with lock_posicoes:
                            posicoes_info[symbol] = 'IN_LONG'
                
                elif sinal_entrada == 'VENDER':
                    print(f"🚨 SINAL DE VENDA DETECTADO PARA {symbol}! 🚨")
                    sucesso = open_short_position(exchange, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT)
                    if sucesso:
                        print(f"Posição SHORT para {symbol} aberta com sucesso.")
                        with lock_posicoes:
                            posicoes_info[symbol] = 'IN_SHORT'

            elif status_atual in ['IN_LONG', 'IN_SHORT']:
                print(f"({symbol}) Posição {status_atual} ativa. Monitorando para um sinal de SAÍDA...")
                market_data = fetch_data(exchange, symbol, timeframe='1m', limit=100)
                if market_data is None:
                    time.sleep(10)
                    continue

                position_side = 'LONG' if status_atual == 'IN_LONG' else 'SHORT'
                sinal_saida = find_exhaustion_signal(market_data, position_side)

                if sinal_saida:
                    print(f"🚪 SINAL DE SAÍDA DETECTADO PARA {symbol}! Fechando posição... 🚪")
                    sucesso = close_position(exchange, symbol)
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

def main():
    """
    Função principal que prepara o ambiente e dispara as threads de análise.
    """
    print("--- INICIANDO O ROBÔ DE TRADING MULTITHREAD (v2.1 - Integração Corrigida) ---")
    
    # 1. Inicializa a conexão única com a exchange (CHAMADA CORRIGIDA)
    exchange = create_exchange_connection()
    if not exchange:
        print("Falha na inicialização da exchange. Encerrando o bot.")
        return

    # 2. Cria e inicia uma thread para cada ativo na watchlist
    threads = []
    for symbol in LISTA_DE_ATIVOS:
        # A configuração de alavancagem deve ser feita para cada símbolo antes de iniciar
        print(f"Preparando thread para {symbol}...")
        if setup_leverage_for_symbol(exchange, symbol, LEVERAGE_LEVEL):
            thread = threading.Thread(target=processar_ativo, args=(symbol, exchange))
            threads.append(thread)
            thread.start()
            time.sleep(1) # Pequena pausa para não sobrecarregar a API na inicialização
        else:
            print(f"Falha ao configurar alavancagem para {symbol}. Esta thread não será iniciada.")


    print(f"\n✅ {len(threads)} threads de análise estão rodando em paralelo.")
    print("O bot está operacional. Pressione Ctrl+C para encerrar.")

    # 3. Mantém a thread principal viva
    for thread in threads:
        thread.join()

# =============================================================================
# PONTO DE ENTRADA DO PROGRAMA
# =============================================================================

if __name__ == '__main__':
    main()