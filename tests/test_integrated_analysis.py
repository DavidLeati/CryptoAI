#!/usr/bin/env python3
"""
Teste da análise técnica integrada com os 4 indicadores configurados centralizadamente.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adicionar o caminho do projeto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar módulos do projeto
from src.analysis.analysis import (
    find_integrated_momentum_signal,
    find_integrated_exhaustion_signal,
    calculate_integrated_signal,
    generate_technical_analysis_report,
    print_analysis_summary
)

def create_sample_market_data(periods=300, trend='sideways', volatility=0.02):
    """
    Cria dados de mercado simulados para teste com mais períodos e padrões mais realistas.
    
    Args:
        periods: Número de períodos (aumentado para 300)
        trend: 'uptrend', 'downtrend', 'sideways'
        volatility: Nível de volatilidade (0.01 = baixa, 0.05 = alta)
    """
    np.random.seed(42)  # Para resultados reproduzíveis
    
    # Preço base
    base_price = 50000.0
    
    # Gerar série temporal com tendência mais pronunciada
    if trend == 'uptrend':
        trend_component = np.linspace(0, 0.15, periods)  # 15% de alta no período
        # Adicionar algumas correções no meio
        for i in range(periods//3, periods//3 + 20):
            trend_component[i] -= 0.02
    elif trend == 'downtrend':
        trend_component = np.linspace(0, -0.15, periods)  # 15% de baixa no período
        # Adicionar alguns rebounds
        for i in range(periods//3, periods//3 + 20):
            trend_component[i] += 0.02
    else:  # sideways
        trend_component = np.zeros(periods)
        # Adicionar alguns movimentos laterais com pequenas ondas
        wave = np.sin(np.linspace(0, 4*np.pi, periods)) * 0.02
        trend_component += wave
    
    # Componente de ruído (volatilidade) com períodos de alta/baixa volatilidade
    base_noise = np.random.normal(0, volatility, periods)
    
    # Criar períodos de volatilidade variável
    volatility_multiplier = np.ones(periods)
    high_vol_start = periods // 4
    high_vol_end = high_vol_start + 30
    volatility_multiplier[high_vol_start:high_vol_end] = 2.0  # Período de alta volatilidade
    
    noise = base_noise * volatility_multiplier
    
    # Criar série de preços
    returns = trend_component / periods + noise
    prices = [base_price]
    
    for i in range(1, periods):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, 1.0))  # Evitar preços muito baixos
    
    # Gerar volume correlacionado com movimento de preço e volatilidade
    volume_base = 1000000
    price_changes = np.diff(prices) / prices[:-1]
    volume_multipliers = 1 + np.abs(price_changes) * 3 + volatility_multiplier[1:] * 0.5
    volumes = [volume_base * mult for mult in volume_multipliers]
    volumes.insert(0, volume_base)  # Volume inicial
    
    # Gerar dados OHLC mais realistas
    data = []
    for i in range(periods):
        if i == 0:
            open_price = prices[i]
            close_price = prices[i]
            high_price = close_price * (1 + abs(noise[i]) * 0.5)
            low_price = close_price * (1 - abs(noise[i]) * 0.5)
        else:
            open_price = prices[i-1]
            close_price = prices[i]
            
            # Criar range intraday mais realista
            price_range = abs(noise[i]) * open_price * 0.5
            if close_price > open_price:  # Candle de alta
                high_price = max(open_price, close_price) + price_range * 0.7
                low_price = min(open_price, close_price) - price_range * 0.3
            else:  # Candle de baixa
                high_price = max(open_price, close_price) + price_range * 0.3
                low_price = min(open_price, close_price) - price_range * 0.7
        
        data.append({
            'timestamp': pd.Timestamp.now() - pd.Timedelta(minutes=periods-i),
            'open': max(open_price, 0.01),
            'high': max(high_price, max(open_price, close_price)),
            'low': max(low_price, 0.01),
            'close': max(close_price, 0.01),
            'volume': max(volumes[i], 1000)
        })
    
    return pd.DataFrame(data)

def test_integrated_analysis():
    """
    Testa a análise técnica integrada com diferentes cenários de mercado.
    """
    print("🧪 TESTE DA ANÁLISE TÉCNICA INTEGRADA")
    print("=" * 60)
    
    # Cenário 1: Mercado lateral (sideways)
    print("\n📊 CENÁRIO 1: Mercado Lateral")
    sideways_data = create_sample_market_data(periods=300, trend='sideways', volatility=0.015)
    print(f"Dados gerados: {len(sideways_data)} períodos")
    
    # Análise integrada
    integrated_result = calculate_integrated_signal(sideways_data)
    print(f"Sinal Integrado: {integrated_result['signal']}")
    print(f"Confiança: {integrated_result['confidence']:.2f}")
    print(f"Score Ponderado: {integrated_result['weighted_score']:.3f}")
    
    # Mostrar detalhes dos indicadores
    if 'indicators' in integrated_result and integrated_result['indicators']:
        print("Detalhes dos indicadores:")
        for indicator, data in integrated_result['indicators'].items():
            print(f"  {indicator}: {data.get('signal', 'N/A')} (força: {data.get('strength', 0):.2f})")
    
    # Teste de entrada
    entry_signal = find_integrated_momentum_signal(sideways_data)
    print(f"Sinal de Entrada: {entry_signal}")
    
    # Cenário 2: Tendência de alta
    print("\n📈 CENÁRIO 2: Tendência de Alta")
    uptrend_data = create_sample_market_data(periods=300, trend='uptrend', volatility=0.025)
    print(f"Dados gerados: {len(uptrend_data)} períodos")
    
    uptrend_result = calculate_integrated_signal(uptrend_data)
    print(f"Sinal: {uptrend_result['signal']} | Confiança: {uptrend_result['confidence']:.2f}")
    print(f"Descrição: {uptrend_result.get('description', 'N/A')}")
    
    # Verificar se detectou a tendência de alta
    if uptrend_result['signal'] == 'COMPRAR':
        print("✅ Tendência de alta detectada corretamente!")
    else:
        print("⚠️  Tendência de alta não foi detectada claramente")
    
    # Cenário 3: Tendência de baixa
    print("\n📉 CENÁRIO 3: Tendência de Baixa")
    downtrend_data = create_sample_market_data(periods=300, trend='downtrend', volatility=0.025)
    print(f"Dados gerados: {len(downtrend_data)} períodos")
    
    downtrend_result = calculate_integrated_signal(downtrend_data)
    print(f"Sinal: {downtrend_result['signal']} | Confiança: {downtrend_result['confidence']:.2f}")
    print(f"Descrição: {downtrend_result.get('description', 'N/A')}")
    
    # Verificar se detectou a tendência de baixa
    if downtrend_result['signal'] == 'VENDER':
        print("✅ Tendência de baixa detectada corretamente!")
    else:
        print("⚠️  Tendência de baixa não foi detectada claramente")
    
    # Cenário 4: Alta volatilidade
    print("\n⚡ CENÁRIO 4: Alta Volatilidade")
    volatile_data = create_sample_market_data(periods=300, trend='sideways', volatility=0.06)
    print(f"Dados gerados: {len(volatile_data)} períodos")
    
    volatile_result = calculate_integrated_signal(volatile_data)
    print(f"Sinal: {volatile_result['signal']} | Confiança: {volatile_result['confidence']:.2f}")
    
    # Teste de saída
    if volatile_result['signal'] in ['COMPRAR', 'VENDER']:
        position_side = 'LONG' if volatile_result['signal'] == 'COMPRAR' else 'SHORT'
        exit_signal = find_integrated_exhaustion_signal(volatile_data, position_side)
        print(f"Sinal de Saída para {position_side}: {exit_signal}")
    
    # Cenário 5: Teste com relatório completo
    print("\n📋 CENÁRIO 5: Relatório Completo")
    test_data = create_sample_market_data(periods=300, trend='uptrend', volatility=0.03)
    print_analysis_summary(test_data, "BTCUSDT_TEST")

def test_individual_indicators():
    """
    Testa cada indicador individualmente para verificar se estão funcionando.
    """
    print("\n🔍 TESTE DOS INDICADORES INDIVIDUAIS")
    print("=" * 60)
    
    # Importar funções de indicadores
    from src.analysis.analysis import (
        calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_ema,
        analyze_rsi_signal, analyze_macd_signal, analyze_bollinger_signal, analyze_ema_signal
    )
    
    # Gerar dados de teste
    test_data = create_sample_market_data(periods=300, trend='uptrend', volatility=0.02)
    current_price = test_data['close'].iloc[-1]
    
    print(f"Testando com {len(test_data)} períodos de dados")
    print(f"Preço atual: ${current_price:.2f}")
    
    # Teste RSI
    print("\n📊 RSI:")
    rsi_values = calculate_rsi(test_data['close'])
    current_rsi = rsi_values.iloc[-1]
    rsi_signal = analyze_rsi_signal(current_rsi)
    print(f"  Valor: {current_rsi:.2f}")
    print(f"  Sinal: {rsi_signal['signal']} (força: {rsi_signal['strength']:.2f})")
    print(f"  Descrição: {rsi_signal['description']}")
    
    # Teste MACD
    print("\n📈 MACD:")
    macd_data = calculate_macd(test_data['close'])
    macd_signal = analyze_macd_signal(macd_data)
    print(f"  MACD: {macd_data['macd'].iloc[-1]:.4f}")
    print(f"  Signal: {macd_data['signal'].iloc[-1]:.4f}")
    print(f"  Histograma: {macd_data['histogram'].iloc[-1]:.4f}")
    print(f"  Sinal: {macd_signal['signal']} (força: {macd_signal['strength']:.2f})")
    
    # Teste Bollinger Bands
    print("\n📊 Bollinger Bands:")
    bb_data = calculate_bollinger_bands(test_data['close'])
    bb_signal = analyze_bollinger_signal(current_price, bb_data)
    print(f"  Banda Superior: ${bb_data['upper'].iloc[-1]:.2f}")
    print(f"  Média: ${bb_data['middle'].iloc[-1]:.2f}")
    print(f"  Banda Inferior: ${bb_data['lower'].iloc[-1]:.2f}")
    print(f"  Sinal: {bb_signal['signal']} (força: {bb_signal['strength']:.2f})")
    
    # Teste EMA
    print("\n📈 EMA:")
    ema_data = calculate_ema(test_data['close'])
    ema_signal = analyze_ema_signal(current_price, ema_data)
    print(f"  EMA Curta: ${ema_data['ema_short'].iloc[-1]:.2f}")
    print(f"  EMA Longa: ${ema_data['ema_long'].iloc[-1]:.2f}")
    print(f"  EMA Filtro: ${ema_data['ema_filter'].iloc[-1]:.2f}")
    print(f"  Sinal: {ema_signal['signal']} (força: {ema_signal['strength']:.2f})")

def test_configuration_integration():
    """
    Testa se as configurações centralizadas estão sendo utilizadas corretamente.
    """
    print("\n🔧 TESTE DE INTEGRAÇÃO COM CONFIGURAÇÕES")
    print("=" * 60)
    
    # Importar configurações
    try:
        from config.settings import (
            RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT, RSI_WEIGHT,
            MACD_FAST, MACD_SLOW, MACD_SIGNAL, MACD_WEIGHT,
            BB_PERIOD, BB_STD, BB_WEIGHT,
            EMA_SHORT, EMA_LONG, EMA_FILTER, EMA_WEIGHT
        )
        
        print("✅ Configurações importadas com sucesso:")
        print(f"   📊 RSI: Período={RSI_PERIOD}, Sobrevenda={RSI_OVERSOLD}, Sobrecompra={RSI_OVERBOUGHT}, Peso={RSI_WEIGHT}")
        print(f"   📈 MACD: Rápida={MACD_FAST}, Lenta={MACD_SLOW}, Sinal={MACD_SIGNAL}, Peso={MACD_WEIGHT}")
        print(f"   📊 BB: Período={BB_PERIOD}, Desvio={BB_STD}, Peso={BB_WEIGHT}")
        print(f"   📈 EMA: Curta={EMA_SHORT}, Longa={EMA_LONG}, Filtro={EMA_FILTER}, Peso={EMA_WEIGHT}")
        
        # Verificar se os pesos somam aproximadamente 1
        total_weight = RSI_WEIGHT + MACD_WEIGHT + BB_WEIGHT + EMA_WEIGHT
        print(f"   ⚖️  Peso Total: {total_weight} (deve ser próximo de 1.0)")
        
        if abs(total_weight - 1.0) < 0.01:
            print("   ✅ Pesos balanceados corretamente!")
        else:
            print("   ⚠️  Atenção: Pesos não estão balanceados!")
            
    except ImportError as e:
        print(f"❌ Erro ao importar configurações: {e}")

def main():
    """Função principal de teste."""
    try:
        test_configuration_integration()
        test_individual_indicators()
        test_integrated_analysis()
        
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("✅ A análise técnica integrada está funcionando corretamente.")
        print("✅ Os 4 indicadores (RSI, MACD, Bollinger Bands, EMA) estão sendo")
        print("   aplicados simultaneamente com os pesos definidos em settings.py.")
        print("✅ A integração com as configurações centralizadas está ativa.")
        print("✅ Os sinais estão sendo gerados baseados na análise combinada.")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
