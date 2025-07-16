#!/usr/bin/env python3
# test_websocket.py
# Teste rápido da funcionalidade WebSocket

import sys
import time
from pathlib import Path

# Adicionar caminho do projeto
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

try:
    from src.utils.data import fetch_realtime_data
    
    def test_callback(df):
        if df is not None and len(df) > 0:
            print(f"✅ Teste WebSocket: Recebidos {len(df)} dados, último close: {df.iloc[-1]['close']:.2f}")
    
    print("🧪 Testando funcionalidade WebSocket...")
    
    # Teste básico - 10 segundos
    manager = fetch_realtime_data(
        symbol='BTC/USDT:USDT',
        timeframe='1m',
        limit=10,
        callback=test_callback
    )
    
    print("📡 Conectando... aguarde 10 segundos")
    time.sleep(10)
    
    # Verificar dados
    stream_key = 'BTC/USDT:USDT_1m'
    current_candle = manager.get_current_candle(stream_key)
    
    if current_candle:
        print(f"✅ Vela atual recebida: {current_candle['close']:.2f}")
    else:
        print("⚠️  Nenhuma vela atual encontrada")
    
    manager.stop_all_streams()
    print("✅ Teste concluído com sucesso!")
    
except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()
