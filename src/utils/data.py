# data.py
# Responsável por, usando uma conexão existente da exchange,
# buscar e formatar dados de mercado.

import pandas as pd
import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, Optional, Callable
import websocket
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


class RealTimeDataManager:
    """
    Gerenciador de dados em tempo real via WebSocket da Binance.
    Organiza os dados de acordo com o timeframe especificado e mantém um buffer.
    """
    
    def __init__(self):
        self.connections: Dict[str, websocket.WebSocketApp] = {}
        self.data_buffers: Dict[str, deque] = {}
        self.current_candles: Dict[str, Dict] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.timeframe_seconds = {
            '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
            '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, 
            '8h': 28800, '12h': 43200, '1d': 86400
        }
    
    def _convert_symbol_for_websocket(self, symbol: str) -> str:
        """Converte símbolo para formato WebSocket da Binance"""
        return symbol.replace('/USDT:USDT', 'usdt').replace('/', '').lower()
    
    def _create_websocket_url(self, symbol: str, timeframe: str) -> str:
        """Cria URL do WebSocket para kline/candlestick"""
        ws_symbol = self._convert_symbol_for_websocket(symbol)
        return f"wss://fstream.binance.com/ws/{ws_symbol}@kline_{timeframe}"
    
    def _on_message(self, ws, message, stream_key: str):
        """Callback para processar mensagens do WebSocket"""
        try:
            data = json.loads(message)
            kline_data = data.get('k', {})
            
            if not kline_data:
                return
            
            # Extrair dados da vela
            candle = {
                'timestamp': pd.to_datetime(kline_data['t'], unit='ms'),
                'open': float(kline_data['o']),
                'high': float(kline_data['h']),
                'low': float(kline_data['l']),
                'close': float(kline_data['c']),
                'volume': float(kline_data['v']),
                'is_closed': kline_data['x']  # True se a vela estiver fechada
            }
            
            # Atualizar vela atual
            self.current_candles[stream_key] = candle
            
            # Se a vela estiver fechada, adicionar ao buffer
            if candle['is_closed']:
                buffer = self.data_buffers.get(stream_key, deque())
                buffer.append(candle)
                self.data_buffers[stream_key] = buffer
                
                # Chamar callback se existir
                if stream_key in self.callbacks:
                    df = self.get_dataframe(stream_key)
                    if df is not None:
                        self.callbacks[stream_key](df)
            
        except Exception as e:
            print(f"Erro ao processar mensagem WebSocket para {stream_key}: {e}")
    
    def _on_error(self, ws, error, stream_key: str):
        """Callback para erros do WebSocket"""
        print(f"Erro WebSocket para {stream_key}: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg, stream_key: str):
        """Callback para fechamento do WebSocket"""
        print(f"WebSocket fechado para {stream_key}: {close_status_code} - {close_msg}")
    
    def _on_open(self, ws, stream_key: str):
        """Callback para abertura do WebSocket"""
        print(f"✅ WebSocket conectado para {stream_key}")
    
    def start_stream(self, symbol: str, timeframe: str = '1m', limit: int = 1000, 
                    callback: Optional[Callable] = None) -> str:
        """
        Inicia stream de dados em tempo real para um símbolo e timeframe.
        
        Args:
            symbol (str): Símbolo do par (ex: 'BTC/USDT:USDT')
            timeframe (str): Timeframe das velas (ex: '1m', '5m', '1h')
            limit (int): Número máximo de velas no buffer
            callback (Callable): Função a ser chamada quando nova vela for fechada
            
        Returns:
            str: Chave do stream para controle
        """
        stream_key = f"{symbol}_{timeframe}"
        
        # Inicializar buffer com tamanho limitado
        self.data_buffers[stream_key] = deque(maxlen=limit)
        
        # Registrar callback se fornecido
        if callback:
            self.callbacks[stream_key] = callback
        
        # Criar URL do WebSocket
        ws_url = self._create_websocket_url(symbol, timeframe)
        
        # Criar e configurar WebSocket
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=lambda ws, msg: self._on_message(ws, msg, stream_key),
            on_error=lambda ws, error: self._on_error(ws, error, stream_key),
            on_close=lambda ws, c1, c2: self._on_close(ws, c1, c2, stream_key),
            on_open=lambda ws: self._on_open(ws, stream_key)
        )
        
        # Armazenar conexão
        self.connections[stream_key] = ws
        
        # Iniciar WebSocket em thread separada
        def run_websocket():
            ws.run_forever()
        
        thread = threading.Thread(target=run_websocket, daemon=True)
        thread.start()
        
        print(f"🚀 Iniciando stream em tempo real para {symbol} ({timeframe})")
        return stream_key
    
    def stop_stream(self, stream_key: str):
        """Para um stream específico"""
        if stream_key in self.connections:
            self.connections[stream_key].close()
            del self.connections[stream_key]
            
        if stream_key in self.data_buffers:
            del self.data_buffers[stream_key]
            
        if stream_key in self.current_candles:
            del self.current_candles[stream_key]
            
        if stream_key in self.callbacks:
            del self.callbacks[stream_key]
            
        print(f"🛑 Stream parado para {stream_key}")
    
    def get_dataframe(self, stream_key: str) -> Optional[pd.DataFrame]:
        """
        Retorna DataFrame com os dados históricos do buffer.
        
        Args:
            stream_key (str): Chave do stream
            
        Returns:
            pd.DataFrame: DataFrame com dados OHLCV ou None se não houver dados
        """
        if stream_key not in self.data_buffers:
            return None
        
        buffer = self.data_buffers[stream_key]
        if not buffer:
            return None
        
        # Converter buffer para DataFrame
        data = []
        for candle in buffer:
            data.append({
                'timestamp': candle['timestamp'],
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle['volume']
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def get_current_candle(self, stream_key: str) -> Optional[Dict]:
        """
        Retorna a vela atual (ainda não fechada) para um stream.
        
        Args:
            stream_key (str): Chave do stream
            
        Returns:
            dict: Dados da vela atual ou None
        """
        return self.current_candles.get(stream_key)
    
    def stop_all_streams(self):
        """Para todos os streams ativos"""
        stream_keys = list(self.connections.keys())
        for stream_key in stream_keys:
            self.stop_stream(stream_key)
        
        print("🛑 Todos os streams foram parados")


def fetch_realtime_data(symbol: str, timeframe: str = '1m', limit: int = 1000, 
                       callback: Optional[Callable] = None) -> RealTimeDataManager:
    """
    Função de conveniência para iniciar coleta de dados em tempo real.
    
    Args:
        symbol (str): Símbolo do par (ex: 'BTC/USDT:USDT')
        timeframe (str): Timeframe das velas (ex: '1m', '5m', '1h')
        limit (int): Número máximo de velas no buffer
        callback (Callable): Função a ser chamada quando nova vela for fechada
        
    Returns:
        RealTimeDataManager: Instância do gerenciador para controle
        
    Example:
        # Exemplo de uso básico
        def on_new_candle(df):
            print(f"Nova vela fechada! Última close: {df.iloc[-1]['close']}")
        
        manager = fetch_realtime_data('BTC/USDT:USDT', '1m', 500, on_new_candle)
        
        # Para obter dados atuais
        stream_key = 'BTC/USDT:USDT_1m'
        current_data = manager.get_dataframe(stream_key)
        current_candle = manager.get_current_candle(stream_key)
        
        # Para parar
        manager.stop_all_streams()
    """
    manager = RealTimeDataManager()
    manager.start_stream(symbol, timeframe, limit, callback)
    return manager