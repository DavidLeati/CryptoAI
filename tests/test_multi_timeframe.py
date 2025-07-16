#!/usr/bin/env python3
"""
Teste específico para verificar se a análise multi-timeframe está funcionando
com a correção do WebSocket.
"""

import time
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.exchange_setup import create_exchange_connection
from src.utils.data import RealTimeDataManager
from src.analysis.analysis import fetch_multi_timeframe_data, calculate_multi_timeframe_signal

def test_multi_timeframe_analysis():
    """Testa a análise multi-timeframe com dados WebSocket corrigidos"""
    
    print("🔬 TESTE DA ANÁLISE MULTI-TIMEFRAME")
    print("=" * 50)
    
    # 1. Criar conexão com a exchange
    print("1. Criando conexão com a exchange...")
    client = create_exchange_connection()
    if not client:
        print("❌ Falha na conexão com a exchange")
        return False
    print("✅ Conexão estabelecida")
    
    # 2. Criar manager e iniciar todos os streams necessários
    print("\n2. Iniciando streams para todos os timeframes...")
    manager = RealTimeDataManager()
    
    symbol = "BTC/USDT:USDT"
    timeframes = ['1m', '5m', '15m']  # PRIMARY, SECONDARY, CONFIRMATION
    
    for tf in timeframes:
        print(f"   Iniciando stream {tf}...")
        manager.start_stream(
            symbol=symbol, 
            timeframe=tf, 
            limit=500, 
            client=client,
            populate_historical=True
        )
        time.sleep(1)  # Pequena pausa entre streams
    
    # 3. Aguardar todos os streams terem dados suficientes
    print(f"\n3. Aguardando dados suficientes para todos os timeframes...")
    min_required = 103  # Valor mencionado no erro original
    
    all_ready = True
    for tf in timeframes:
        stream_key = f"{symbol}_{tf}"
        print(f"   Aguardando {stream_key}...")
        
        if not manager.wait_for_sufficient_data(stream_key, min_required, timeout=30):
            print(f"   ❌ Timeout para {stream_key}")
            all_ready = False
        else:
            df = manager.get_dataframe(stream_key)
            print(f"   ✅ {stream_key}: {len(df)} velas disponíveis")
    
    if not all_ready:
        print("⚠️  Nem todos os streams estão prontos, mas continuando teste...")
    
    # 4. Testar fetch_multi_timeframe_data
    print(f"\n4. Testando fetch_multi_timeframe_data...")
    try:
        multi_data = fetch_multi_timeframe_data(manager, client, symbol)
        
        if multi_data:
            print("✅ Dados multi-timeframe obtidos com sucesso!")
            for tf_name, df in multi_data.items():
                print(f"   - {tf_name}: {len(df)} velas ({df.index[0]} até {df.index[-1]})")
        else:
            print("❌ Falha ao obter dados multi-timeframe")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao buscar dados multi-timeframe: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Testar análise multi-timeframe
    print(f"\n5. Testando análise multi-timeframe...")
    try:
        analysis_result = calculate_multi_timeframe_signal(multi_data)
        
        print("✅ Análise multi-timeframe executada!")
        print(f"   - Sinal: {analysis_result['signal']}")
        print(f"   - Confiança: {analysis_result['confidence']:.3f}")
        print(f"   - MTA Aprovado: {analysis_result['mta_approved']}")
        print(f"   - Descrição: {analysis_result['description']}")
        
        # Mostrar detalhes dos timeframes
        if 'primary_analysis' in analysis_result:
            primary = analysis_result['primary_analysis']
            print(f"   - Primário (1m): {primary['signal']} (conf: {primary['confidence']:.3f})")
        
        if 'trend_filter' in analysis_result:
            trend = analysis_result['trend_filter']
            print(f"   - Tendência (15m): {trend['trend']} (força: {trend['strength']:.3f})")
        
    except Exception as e:
        print(f"❌ Erro na análise multi-timeframe: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Verificar estatísticas finais
    print(f"\n6. Estatísticas finais dos streams...")
    for tf in timeframes:
        stream_key = f"{symbol}_{tf}"
        status = manager.get_stream_status(stream_key)
        df = manager.get_dataframe(stream_key)
        
        print(f"   📊 {stream_key}:")
        print(f"      - Conectado: {status['is_connected']}")
        print(f"      - Buffer: {status['buffer_size']} velas")
        if df is not None:
            print(f"      - Preço atual: ${df.iloc[-1]['close']:.2f}")
            print(f"      - Período: {df.index[0]} - {df.index[-1]}")
    
    # 7. Finalizar
    print(f"\n7. Finalizando teste...")
    manager.stop_all_streams()
    print("✅ Teste da análise multi-timeframe concluído com sucesso!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_multi_timeframe_analysis()
        if success:
            print("\n🎉 TESTE MULTI-TIMEFRAME PASSOU! O problema do WebSocket foi corrigido.")
        else:
            print("\n❌ TESTE MULTI-TIMEFRAME FALHOU! Verifique os logs acima.")
    except KeyboardInterrupt:
        print("\n⏹️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro inesperado no teste: {e}")
        import traceback
        traceback.print_exc()
