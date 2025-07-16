# exemplo_websocket.py
# Exemplo de uso da nova funcionalidade de dados em tempo real via WebSocket

import time
import sys
from pathlib import Path

# Adicionar caminho do projeto
project_path = Path(__file__).parent.parent
sys.path.insert(0, str(project_path))

from src.utils.data import fetch_realtime_data, RealTimeDataManager

def exemplo_callback(df):
    """
    Função de callback chamada sempre que uma nova vela é fechada.
    
    Args:
        df (pd.DataFrame): DataFrame com dados históricos atualizados
    """
    if df is not None and len(df) > 0:
        last_candle = df.iloc[-1]
        print(f"📊 Nova vela fechada!")
        print(f"   🕐 Timestamp: {df.index[-1]}")
        print(f"   💰 Close: {last_candle['close']:.4f}")
        print(f"   📈 High: {last_candle['high']:.4f}")
        print(f"   📉 Low: {last_candle['low']:.4f}")
        print(f"   📊 Volume: {last_candle['volume']:.2f}")
        print(f"   📋 Total velas: {len(df)}")
        print("-" * 50)

def exemplo_basico():
    """Exemplo básico de uso do WebSocket"""
    print("🚀 Iniciando exemplo de dados em tempo real...")
    
    # Iniciar coleta de dados em tempo real para BTC
    manager = fetch_realtime_data(
        symbol='BTC/USDT:USDT',
        timeframe='1m',
        limit=100,
        callback=exemplo_callback
    )
    
    # Aguardar conexão
    time.sleep(2)
    
    # Monitorar por 30 segundos
    print("📡 Monitorando dados em tempo real por 30 segundos...")
    
    for i in range(30):
        time.sleep(1)
        
        # Obter vela atual (ainda não fechada)
        stream_key = 'BTC/USDT:USDT_1m'
        current_candle = manager.get_current_candle(stream_key)
        
        if current_candle:
            print(f"⏱️  Vela atual - Close: {current_candle['close']:.4f} "
                  f"(Fechada: {'✅' if current_candle['is_closed'] else '❌'})")
    
    # Parar streams
    manager.stop_all_streams()
    print("✅ Exemplo concluído!")

def exemplo_multiplos_simbolos():
    """Exemplo com múltiplos símbolos e timeframes"""
    print("🚀 Iniciando exemplo com múltiplos símbolos...")
    
    manager = RealTimeDataManager()
    
    # Configurar callbacks específicos para cada símbolo
    def callback_btc(df):
        if df is not None and len(df) > 0:
            print(f"🟡 BTC: {df.iloc[-1]['close']:.2f} USDT")
    
    def callback_eth(df):
        if df is not None and len(df) > 0:
            print(f"🔵 ETH: {df.iloc[-1]['close']:.2f} USDT")
    
    # Iniciar streams para diferentes símbolos
    manager.start_stream('BTC/USDT:USDT', '1m', 50, callback_btc)
    time.sleep(1)
    manager.start_stream('ETH/USDT:USDT', '5m', 50, callback_eth)
    
    # Monitorar por 60 segundos
    print("📡 Monitorando BTC (1m) e ETH (5m) por 60 segundos...")
    time.sleep(60)
    
    # Obter dados finais
    btc_data = manager.get_dataframe('BTC/USDT:USDT_1m')
    eth_data = manager.get_dataframe('ETH/USDT:USDT_5m')
    
    if btc_data is not None:
        print(f"📊 BTC: {len(btc_data)} velas coletadas")
    if eth_data is not None:
        print(f"📊 ETH: {len(eth_data)} velas coletadas")
    
    # Parar todos os streams
    manager.stop_all_streams()
    print("✅ Exemplo com múltiplos símbolos concluído!")

if __name__ == "__main__":
    try:
        print("Escolha um exemplo:")
        print("1. Exemplo básico (BTC 1m)")
        print("2. Múltiplos símbolos (BTC 1m + ETH 5m)")
        
        escolha = input("Digite 1 ou 2: ").strip()
        
        if escolha == "1":
            exemplo_basico()
        elif escolha == "2":
            exemplo_multiplos_simbolos()
        else:
            print("Opção inválida. Executando exemplo básico...")
            exemplo_basico()
            
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
