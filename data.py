# data.py
# Responsável por, usando uma conexão existente da exchange,
# buscar e formatar dados de mercado.

import pandas as pd
import ccxt

def fetch_data(exchange, symbol, timeframe='1m', limit=100):
    """
    Busca os dados de velas (OHLCV) mais recentes para um símbolo.
    Recebe um objeto de conexão 'exchange' já inicializado.

    Args:
        exchange (ccxt.Exchange): O objeto de conexão da exchange já instanciado.
        symbol (str): O símbolo do par de negociação (ex: 'BTC/USDT').
        timeframe (str): O intervalo de tempo das velas (ex: '1m', '5m', '1h').
        limit (int): O número de velas a serem buscadas.

    Returns:
        pandas.DataFrame: Um DataFrame com os dados OHLCV, ou None se ocorrer um erro.
    """
    # Verificação de segurança: garante que um objeto de exchange foi passado
    if not exchange:
        print("Erro: O objeto de conexão da exchange não foi fornecido.")
        return None

    print(f"Buscando {limit} velas de {timeframe} para o símbolo {symbol}...")
    
    try:
        # A lógica de busca e formatação permanece a mesma
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        
        if not ohlcv:
            print(f"Nenhum dado retornado para {symbol}.")
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df

    except Exception as e:
        print(f"Ocorreu um erro inesperado ao buscar os dados para {symbol}: {e}")
        return None

if __name__ == '__main__':
    # Criamos uma conexão local SOMENTE para fins de teste
    test_exchange = ccxt.binance()
    
    # Passamos a conexão de teste para a função
    btc_data = fetch_data(exchange=test_exchange, symbol='BTC/USDT', timeframe='1m', limit=5)
    
    if btc_data is not None:
        print("\nÚltimas 5 velas de 1 minuto para BTC/USDT:")
        print(btc_data)
        
    print("\n--- TESTE DO MÓDULO data.py CONCLUÍDO ---")