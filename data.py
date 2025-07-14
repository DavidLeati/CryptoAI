# data.py
# Responsável por, usando uma conexão existente da exchange,
# buscar e formatar dados de mercado.

import pandas as pd
from binance.client import Client
from binance.enums import *

def fetch_data(client, symbol, timeframe='1m', limit=100):
    """
    Busca os dados de velas (OHLCV) mais recentes para um símbolo.
    Recebe um objeto de conexão 'client' já inicializado.

    Args:
        client (binance.client.Client): O objeto de conexão da Binance já instanciado.
        symbol (str): O símbolo do par de negociação (ex: 'BTC/USDT:USDT').
        timeframe (str): O intervalo de tempo das velas (ex: '1m', '5m', '1h').
        limit (int): O número de velas a serem buscadas.

    Returns:
        pandas.DataFrame: Um DataFrame com os dados OHLCV, ou None se ocorrer um erro.
    """
    # Verificação de segurança: garante que um objeto de client foi passado
    if not client:
        print("Erro: O objeto de conexão da exchange não foi fornecido.")
        return None

    print(f"Buscando {limit} velas de {timeframe} para o símbolo {symbol}...")
    
    try:
        # Converter símbolo para formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # Mapear timeframes para o formato da Binance
        timeframe_map = {
            '1m': Client.KLINE_INTERVAL_1MINUTE,
            '3m': Client.KLINE_INTERVAL_3MINUTE,
            '5m': Client.KLINE_INTERVAL_5MINUTE,
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '30m': Client.KLINE_INTERVAL_30MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR,
            '2h': Client.KLINE_INTERVAL_2HOUR,
            '4h': Client.KLINE_INTERVAL_4HOUR,
            '6h': Client.KLINE_INTERVAL_6HOUR,
            '8h': Client.KLINE_INTERVAL_8HOUR,
            '12h': Client.KLINE_INTERVAL_12HOUR,
            '1d': Client.KLINE_INTERVAL_1DAY,
            '3d': Client.KLINE_INTERVAL_3DAY,
            '1w': Client.KLINE_INTERVAL_1WEEK,
            '1M': Client.KLINE_INTERVAL_1MONTH
        }
        
        interval = timeframe_map.get(timeframe, Client.KLINE_INTERVAL_1MINUTE)
        
        # Buscar dados de klines (velas) dos futuros
        klines = client.futures_klines(symbol=binance_symbol, interval=interval, limit=limit)
        
        if not klines:
            print(f"Nenhum dado retornado para {symbol}.")
            return None

        # Converter para DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Converter timestamps para datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Converter colunas OHLCV para float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Retornar apenas as colunas OHLCV
        return df[['open', 'high', 'low', 'close', 'volume']]

    except Exception as e:
        print(f"Ocorreu um erro inesperado ao buscar os dados para {symbol}: {e}")
        return None

if __name__ == '__main__':
    # Criamos uma conexão local SOMENTE para fins de teste
    # test_client = Client('api_key', 'api_secret', testnet=True)
    print("Para testar, descomente a linha acima e forneça suas credenciais de API.")
    
    # Passamos a conexão de teste para a função
    # btc_data = fetch_data(client=test_client, symbol='BTC/USDT:USDT', timeframe='1m', limit=5)
    
    # if btc_data is not None:
    #     print("\nÚltimas 5 velas de 1 minuto para BTC/USDT:")
    #     print(btc_data)
        
    print("\n--- TESTE DO MÓDULO data.py CONCLUÍDO ---")