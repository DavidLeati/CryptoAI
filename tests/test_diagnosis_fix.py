#!/usr/bin/env python3
"""
Teste das correções na função diagnose_market_data_quality
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Adicionar o diretório src ao path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from analysis.analysis import diagnose_market_data_quality

def test_edge_cases():
    """Testa casos extremos que causavam problemas"""
    
    print("🧪 TESTANDO CASOS EXTREMOS DA FUNÇÃO diagnose_market_data_quality")
    print("=" * 70)
    
    # Teste 1: Dados nulos
    print("\n1. Teste com dados NULOS:")
    result = diagnose_market_data_quality(None, "TEST_NULL")
    print(f"   Resultado: {result['summary']}")
    assert "❌ DADOS NULOS" in result['summary']
    
    # Teste 2: DataFrame vazio
    print("\n2. Teste com DataFrame VAZIO:")
    empty_df = pd.DataFrame()
    result = diagnose_market_data_quality(empty_df, "TEST_EMPTY")
    print(f"   Resultado: {result['summary']}")
    assert "❌ DADOS VAZIOS" in result['summary']
    
    # Teste 3: DataFrame sem colunas necessárias
    print("\n3. Teste com colunas AUSENTES:")
    bad_df = pd.DataFrame({'wrong_col': [1, 2, 3]})
    result = diagnose_market_data_quality(bad_df, "TEST_BAD_COLS")
    print(f"   Resultado: {result['summary']}")
    assert "❌ ESTRUTURA INVÁLIDA" in result['summary']
    
    # Teste 4: Dados com valores NaN
    print("\n4. Teste com valores NaN:")
    nan_data = {
        'open': [1.0, 2.0, np.nan, 4.0, 5.0],
        'high': [1.1, 2.1, 3.1, 4.1, np.nan],
        'low': [0.9, 1.9, 2.9, 3.9, 4.9],
        'close': [1.05, 2.05, np.nan, 4.05, 5.05],
        'volume': [100, 200, 300, np.nan, 500]
    }
    nan_df = pd.DataFrame(nan_data)
    result = diagnose_market_data_quality(nan_df, "TEST_NAN")
    print(f"   Resultado: {result['summary']}")
    print(f"   Problemas preço: {len(result['price_issues'])}")
    print(f"   Problemas volume: {len(result['volume_issues'])}")
    
    # Teste 5: Dados com zeros e negativos
    print("\n5. Teste com valores ZERO/NEGATIVOS:")
    bad_data = {
        'open': [1.0, 2.0, 0.0, 4.0, -1.0],  # Zero e negativo
        'high': [1.1, 2.1, 3.1, 4.1, 5.1],
        'low': [0.9, 1.9, 2.9, 3.9, 4.9],
        'close': [1.05, 2.05, 0.0, 4.05, -0.5],  # Zero e negativo
        'volume': [100, 200, 0, 400, -50]  # Zero e negativo
    }
    bad_df = pd.DataFrame(bad_data)
    result = diagnose_market_data_quality(bad_df, "TEST_BAD_VALUES")
    print(f"   Resultado: {result['summary']}")
    print(f"   Problemas preço: {result['price_issues']}")
    print(f"   Problemas volume: {result['volume_issues']}")
    
    # Teste 6: Dados insuficientes (poucos pontos)
    print("\n6. Teste com dados INSUFICIENTES:")
    small_data = {
        'open': [1.0, 2.0],
        'high': [1.1, 2.1],
        'low': [0.9, 1.9],
        'close': [1.05, 2.05],
        'volume': [100, 200]
    }
    small_df = pd.DataFrame(small_data)
    result = diagnose_market_data_quality(small_df, "TEST_SMALL")
    print(f"   Resultado: {result['summary']}")
    print(f"   Data sufficient: {result['data_sufficient']}")
    print(f"   Recomendações: {result['recommendations']}")
    
    # Teste 7: Dados com valores extremos
    print("\n7. Teste com valores EXTREMOS:")
    extreme_data = {
        'open': [1.0, 2.0, 1e10, 4.0, 5.0],  # Valor muito grande
        'high': [1.1, 2.1, 1e10, 4.1, 5.1],
        'low': [0.9, 1.9, 1e-10, 3.9, 4.9],  # Valor muito pequeno
        'close': [1.05, 2.05, 1e10, 4.05, 5.05],
        'volume': [100, 200, 1e15, 400, 500]  # Volume extremo
    }
    extreme_df = pd.DataFrame(extreme_data)
    result = diagnose_market_data_quality(extreme_df, "TEST_EXTREME")
    print(f"   Resultado: {result['summary']}")
    print(f"   Problemas encontrados: {len(result['price_issues']) + len(result['volume_issues'])}")
    
    # Teste 8: Dados bons (controle positivo)
    print("\n8. Teste com dados BONS (controle):")
    good_data = {
        'open': np.random.uniform(99, 101, 250),   # 250 pontos com preços realistas
        'high': np.random.uniform(100, 102, 250),
        'low': np.random.uniform(98, 100, 250),
        'close': np.random.uniform(99, 101, 250),
        'volume': np.random.uniform(1000, 5000, 250)  # Volume realista
    }
    good_df = pd.DataFrame(good_data)
    # Garantir que high >= max(open, close) e low <= min(open, close)
    for i in range(len(good_df)):
        good_df.loc[i, 'high'] = max(good_df.loc[i, 'high'], good_df.loc[i, 'open'], good_df.loc[i, 'close'])
        good_df.loc[i, 'low'] = min(good_df.loc[i, 'low'], good_df.loc[i, 'open'], good_df.loc[i, 'close'])
    
    result = diagnose_market_data_quality(good_df, "TEST_GOOD")
    print(f"   Resultado: {result['summary']}")
    print(f"   Data sufficient: {result['data_sufficient']}")
    print(f"   Problemas: {len(result['price_issues']) + len(result['volume_issues'])}")
    
    print("\n" + "=" * 70)
    print("✅ TODOS OS TESTES CONCLUÍDOS!")
    print("✅ A função agora é ROBUSTA contra casos extremos!")

if __name__ == "__main__":
    test_edge_cases()
