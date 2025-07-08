# main.py
# Ponto de entrada e lógica central (orquestrador) do robô de trading.
# Esta versão é multithread para analisar múltiplos ativos simultaneamente.

import time
import threading

# Importando as funções dos nossos módulos especialistas (acessórios)
from exchange_setup import initialize_exchange
from data import fetch_data
from analysis import find_momentum_signal
from orders import open_long_position, open_short_position, close_position

# =============================================================================
# 1. CONFIGURAÇÃO GERAL E RECURSOS COMPARTILHADOS
# =============================================================================

# LISTA DE ATIVOS PARA MONITORAR SIMULTANEAMENTE
LISTA_DE_ATIVOS = [
    'BTC/USDT', 
    'ETH/USDT', 
    'SOL/USDT', 
    'BNB/USDT',
    'XRP/USDT'
]

# PARÂMETROS DE TRADING
TRADE_VALUE_USD = 10.00      # Valor em USD para cada operação
STOP_LOSS_PCT = 1.5          # Stop-loss de 1.5%
LEVERAGE_LEVEL = 10           # Alavancagem de 10x

# RECURSOS COMPARTILHADOS ENTRE AS THREADS
# Usamos um 'set' para rastrear posições ativas de forma eficiente.
posicoes_ativas = set()
# Um 'Lock' é ESSENCIAL para evitar que duas threads modifiquem o 'set' ao mesmo tempo (condição de corrida).
lock_posicoes = threading.Lock()


# =============================================================================
# 2. A LÓGICA DO WORKER (O QUE CADA THREAD FAZ)
# =============================================================================

def processar_ativo(symbol, exchange):
    """
    Esta é a função principal que cada thread executa em um loop infinito
    para um único ativo.
    """
    print(f"✅ Thread para {symbol} iniciada.")
    
    # Configura a alavancagem para este símbolo específico antes de começar
    # (Supondo que a função em exchange_setup não precise ser chamada aqui, 
    # mas se precisar, a chamada seria feita aqui dentro da thread)

    while True:
        try:
            # --- VERIFICAÇÃO DE ESTADO (THREAD-SAFE) ---
            with lock_posicoes:
                if symbol in posicoes_ativas:
                    # Se já temos uma posição aberta para este ativo, pulamos a análise
                    # Em uma versão futura, aqui poderia entrar a lógica para SAIR da posição
                    # print(f"Posição já ativa para {symbol}. Apenas monitorando...")
                    time.sleep(10) # Pausa maior se já estamos em uma posição
                    continue

            # --- FLUXO DE OPERAÇÃO PADRÃO ---
            # 1. Coletar Dados
            market_data = fetch_data(exchange, symbol, timeframe='1m', limit=100)
            if market_data is None:
                time.sleep(5)
                continue

            # 2. Analisar Dados
            sinal = find_momentum_signal(market_data)
            
            # 3. Agir com Base no Sinal
            if sinal == 'COMPRAR':
                print(f"🚨 SINAL DE COMPRA DETECTADO PARA {symbol}! 🚨")
                sucesso = open_long_position(exchange, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT)
                if sucesso:
                    print(f"Posição LONG para {symbol} aberta com sucesso.")
                    with lock_posicoes:
                        posicoes_ativas.add(symbol) # Adiciona ao set de posições ativas
            
            elif sinal == 'VENDER':
                print(f"🚨 SINAL DE VENDA DETECTADO PARA {symbol}! 🚨")
                sucesso = open_short_position(exchange, symbol, TRADE_VALUE_USD, STOP_LOSS_PCT)
                if sucesso:
                    print(f"Posição SHORT para {symbol} aberta com sucesso.")
                    with lock_posicoes:
                        posicoes_ativas.add(symbol) # Adiciona ao set de posições ativas
            
            else: # Sinal de AGUARDAR
                print(f"Análise para {symbol}: Nenhum sinal claro. Aguardando...")
                
            # Pausa para evitar sobrecarga da API
            time.sleep(5)

        except Exception as e:
            print(f"ERRO na thread de {symbol}: {e}")
            time.sleep(15)


# =============================================================================
# 3. O MAESTRO (FUNÇÃO PRINCIPAL)
# =============================================================================

def main():
    """
    Função principal que prepara o ambiente e dispara as threads de análise.
    """
    print("--- INICIANDO O ROBÔ DE TRADING MULTITHREAD ---")
    
    # 1. Inicializa a conexão única e compartilhada com a exchange
    # Usamos o primeiro ativo da lista apenas como referência para o setup inicial
    exchange = initialize_exchange(LISTA_DE_ATIVOS[0], LEVERAGE_LEVEL)
    if not exchange:
        print("Falha na inicialização da exchange. Encerrando o bot.")
        return

    # 2. Cria e inicia uma thread para cada ativo na nossa watchlist
    threads = []
    for symbol in LISTA_DE_ATIVOS:
        thread = threading.Thread(target=processar_ativo, args=(symbol, exchange))
        threads.append(thread)
        thread.start()
        time.sleep(1) # Pequena pausa para não sobrecarregar a API na inicialização

    print(f"\n✅ {len(threads)} threads de análise estão rodando em paralelo.")
    print("O bot está operacional. Pressione Ctrl+C para encerrar.")

    # 3. Mantém a thread principal viva, esperando que as outras terminem
    # (o que, em nosso caso, é nunca, a menos que o programa seja interrompido)
    for thread in threads:
        thread.join()

# =============================================================================
# PONTO DE ENTRADA DO PROGRAMA
# =============================================================================

if __name__ == '__main__':
    # ATENÇÃO:
    # Antes de rodar, certifique-se de que suas variáveis de ambiente
    # BINANCE_API_KEY e BINANCE_API_SECRET estão configuradas.
    # COMECE SEMPRE NA TESTNET (sandbox mode) E COM VALORES BAIXOS!
    main()