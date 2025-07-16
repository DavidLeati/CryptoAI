#!/usr/bin/env python3
"""
Script de teste para verificar se a correção do WebSocket está funcionando.
Testa a funcionalidade de pré-população com dados históricos e aguarda dados suficientes.
"""

import time
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.exchange_setup import create_exchange_connection
from src.utils.data import RealTimeDataManager

def test_websocket_fix():
    """Testa a correção do WebSocket com pré-população de dados históricos"""
    
    print("🧪 TESTE DA CORREÇÃO DO WEBSOCKET")
    print("=" * 50)
    
    # 1. Criar conexão com a exchange
    print("1. Criando conexão com a exchange...")
    client = create_exchange_connection()
    if not client:
        print("❌ Falha na conexão com a exchange")
        return False
    print("✅ Conexão estabelecida")
    
    # 2. Criar manager e iniciar stream com dados históricos
    print("\n2. Iniciando WebSocket com pré-população...")
    manager = RealTimeDataManager()
    
    symbol = "BTC/USDT:USDT"
    timeframe = "1m"
    
    # Callback para mostrar quando nova vela chega
    def on_new_candle(df):
        print(f"📊 Nova vela recebida! Total de velas: {len(df)}, Último preço: ${df.iloc[-1]['close']:.2f}")
    
    stream_key = manager.start_stream(
        symbol=symbol, 
        timeframe=timeframe, 
        limit=500, 
        callback=on_new_candle,
        client=client,
        populate_historical=True
    )
    
    # 3. Verificar status inicial
    print(f"\n3. Verificando status do stream {stream_key}...")
    time.sleep(2)  # Dar tempo para dados históricos carregarem
    
    status = manager.get_stream_status(stream_key)
    print(f"📋 Status do stream:")
    print(f"   - Conectado: {status['is_connected']}")
    print(f"   - Tamanho do buffer: {status['buffer_size']}")
    print(f"   - Tem vela atual: {status['has_current_candle']}")
    print(f"   - Tem callback: {status['has_callback']}")
    
    if status['buffer_size'] > 0:
        print(f"   - Vela mais antiga: {status.get('oldest_candle', 'N/A')}")
        print(f"   - Vela mais recente: {status.get('newest_candle', 'N/A')}")
    
    # 4. Testar get_dataframe
    print(f"\n4. Testando obtenção de DataFrame...")
    df = manager.get_dataframe(stream_key)
    
    if df is not None:
        print(f"✅ DataFrame obtido com sucesso!")
        print(f"   - Número de velas: {len(df)}")
        print(f"   - Período: {df.index[0]} até {df.index[-1]}")
        print(f"   - Último preço: ${df.iloc[-1]['close']:.2f}")
        print(f"   - Colunas: {list(df.columns)}")
        
        # Mostrar algumas estatísticas
        print(f"\n📊 Estatísticas dos dados:")
        print(f"   - Preço mínimo: ${df['close'].min():.2f}")
        print(f"   - Preço máximo: ${df['close'].max():.2f}")
        print(f"   - Volume médio: {df['volume'].mean():.2f}")
        
    else:
        print("❌ Falha ao obter DataFrame")
        return False
    
    # 5. Testar aguardar dados suficientes
    print(f"\n5. Testando função de aguardar dados suficientes...")
    min_required = 100  # Requer 100 velas
    
    if manager.wait_for_sufficient_data(stream_key, min_required, timeout=30):
        print(f"✅ Dados suficientes obtidos ({min_required}+ velas)")
        final_df = manager.get_dataframe(stream_key)
        print(f"   - Total final de velas: {len(final_df)}")
    else:
        print(f"⚠️  Timeout aguardando {min_required} velas")
    
    # 6. Aguardar algumas velas em tempo real
    print(f"\n6. Aguardando velas em tempo real por 30 segundos...")
    print("   (Observe as mensagens de callback acima)")
    
    start_time = time.time()
    while time.time() - start_time < 30:
        current_candle = manager.get_current_candle(stream_key)
        if current_candle:
            print(f"   Vela atual: {current_candle['timestamp']} - ${current_candle['close']:.2f}", end='\r')
        time.sleep(1)
    
    print(f"\n\n7. Finalizando teste...")
    manager.stop_all_streams()
    print("✅ Teste concluído com sucesso!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_websocket_fix()
        if success:
            print("\n🎉 TESTE PASSOU! A correção do WebSocket está funcionando.")
        else:
            print("\n❌ TESTE FALHOU! Verifique os logs acima.")
    except KeyboardInterrupt:
        print("\n⏹️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro inesperado no teste: {e}")
        import traceback
        traceback.print_exc()
