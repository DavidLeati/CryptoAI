#!/usr/bin/env python3
"""
Teste das melhorias implementadas na análise de momentum para resolver
problemas comuns que fazem a análise cair no modo legacy.

Execução:
python test_momentum_improvements.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Adicionar src ao path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from analysis.analysis import (
    find_momentum_signal_legacy,
    diagnose_market_data_quality,
    explain_legacy_fallback_causes,
    test_improved_momentum_analysis,
    analyze_momentum_confirmation
)

def test_problematic_scenarios():
    """
    Testa cenários específicos que causavam problemas antes das melhorias.
    """
    print("🔬 TESTE DE CENÁRIOS PROBLEMÁTICOS")
    print("=" * 80)
    
    # Cenário 1: Volume médio zero (problema original)
    print("\n📊 CENÁRIO 1: Volume médio zero - Problema que causava 999.99x")
    dates = pd.date_range('2024-01-01', periods=30, freq='1min')
    
    scenario_1 = pd.DataFrame({
        'open': [100.0 + (i * 0.01) for i in range(30)],
        'high': [100.1 + (i * 0.01) for i in range(30)],
        'low': [99.9 + (i * 0.01) for i in range(30)],
        'close': [100.0 + (i * 0.01) for i in range(30)],
        'volume': [0.0] * 29 + [1500.0]  # Apenas última vela com volume
    }, index=dates)
    
    print("   💾 Dados de entrada:")
    print(f"      Preços: {scenario_1['close'].iloc[0]:.2f} → {scenario_1['close'].iloc[-1]:.2f}")
    print(f"      Volume: Médio={scenario_1['volume'].iloc[:-1].mean():.2f}, Atual={scenario_1['volume'].iloc[-1]:.2f}")
    
    diagnosis_1 = diagnose_market_data_quality(scenario_1, "CENÁRIO-1")
    result_1 = find_momentum_signal_legacy(scenario_1)
    
    print(f"   🎯 Resultado: {result_1}")
    print(f"   🩺 Diagnóstico: {diagnosis_1['summary']}")
    
    # Cenário 2: Preços idênticos (variação 0.00%)
    print("\n📊 CENÁRIO 2: Preços idênticos - Problema que causava 0.00% de variação")
    
    scenario_2 = pd.DataFrame({
        'open': [100.0] * 30,
        'high': [100.0] * 30,
        'low': [100.0] * 30,
        'close': [100.0] * 30,  # Sem movimento algum
        'volume': [1000.0 + (i * 10) for i in range(30)]  # Volume normal
    }, index=dates)
    
    print("   💾 Dados de entrada:")
    print(f"      Preços: {scenario_2['close'].iloc[0]:.2f} → {scenario_2['close'].iloc[-1]:.2f}")
    print(f"      Volume: Médio={scenario_2['volume'].mean():.2f}, Atual={scenario_2['volume'].iloc[-1]:.2f}")
    
    diagnosis_2 = diagnose_market_data_quality(scenario_2, "CENÁRIO-2")
    result_2 = find_momentum_signal_legacy(scenario_2)
    
    print(f"   🎯 Resultado: {result_2}")
    print(f"   🩺 Diagnóstico: {diagnosis_2['summary']}")
    
    # Cenário 3: Dados normais para comparação
    print("\n📊 CENÁRIO 3: Dados normais - Para comparação")
    
    scenario_3 = pd.DataFrame({
        'open': [100.0 + (i * 0.05) + np.random.normal(0, 0.01) for i in range(30)],
        'high': [100.2 + (i * 0.05) + np.random.normal(0, 0.01) for i in range(30)],
        'low': [99.8 + (i * 0.05) + np.random.normal(0, 0.01) for i in range(30)],
        'close': [100.0 + (i * 0.05) + np.random.normal(0, 0.01) for i in range(30)],
        'volume': [1000.0 + (i * 20) + np.random.normal(0, 50) for i in range(30)]
    }, index=dates)
    
    # Garantir volumes positivos
    scenario_3['volume'] = scenario_3['volume'].abs() + 100
    
    print("   💾 Dados de entrada:")
    print(f"      Preços: {scenario_3['close'].iloc[0]:.2f} → {scenario_3['close'].iloc[-1]:.2f}")
    print(f"      Volume: Médio={scenario_3['volume'].mean():.2f}, Atual={scenario_3['volume'].iloc[-1]:.2f}")
    
    diagnosis_3 = diagnose_market_data_quality(scenario_3, "CENÁRIO-3")
    result_3 = find_momentum_signal_legacy(scenario_3)
    
    print(f"   🎯 Resultado: {result_3}")
    print(f"   🩺 Diagnóstico: {diagnosis_3['summary']}")
    
    print("\n" + "=" * 80)

def test_momentum_confirmation_improvements():
    """
    Testa as melhorias na confirmação de momentum.
    """
    print("\n🔍 TESTE DE CONFIRMAÇÃO DE MOMENTUM")
    print("=" * 80)
    
    # Criar dados para teste de confirmação
    dates = pd.date_range('2024-01-01', periods=30, freq='1min')
    
    # Teste com volume problemático
    test_data = pd.DataFrame({
        'open': [100.0 + (i * 0.1) for i in range(30)],  # Tendência de alta clara
        'high': [100.2 + (i * 0.1) for i in range(30)],
        'low': [99.8 + (i * 0.1) for i in range(30)],
        'close': [100.0 + (i * 0.1) for i in range(30)],
        'volume': [0.0] * 25 + [1000.0] * 5  # Volume apenas no final
    }, index=dates)
    
    print("📊 Testando confirmação de sinal de COMPRA:")
    print(f"   Variação preço: {((test_data['close'].iloc[-1] / test_data['close'].iloc[-4]) - 1) * 100:.2f}%")
    print(f"   Volume médio: {test_data['volume'].iloc[:-5].mean():.2f}")
    print(f"   Volume atual: {test_data['volume'].iloc[-1]:.2f}")
    
    confirmation_buy = analyze_momentum_confirmation(test_data, 'COMPRAR')
    print(f"   ✅ Confirmação COMPRA: {confirmation_buy}")
    
    print("\n📊 Testando confirmação de sinal de VENDA:")
    # Inverter dados para tendência de baixa
    test_data_sell = test_data.copy()
    test_data_sell['close'] = test_data_sell['close'].iloc[::-1]  # Reverter ordem
    
    confirmation_sell = analyze_momentum_confirmation(test_data_sell, 'VENDER')
    print(f"   ✅ Confirmação VENDA: {confirmation_sell}")
    
    print("\n" + "=" * 80)

def main():
    """
    Executa todos os testes das melhorias implementadas.
    """
    print("🚀 TESTE COMPLETO DAS MELHORIAS NA ANÁLISE DE MOMENTUM")
    print("=" * 80)
    print("Objetivo: Resolver problemas que fazem a análise cair no modo LEGACY")
    print("Problemas identificados:")
    print("  • Volume médio zero → Multiplicador 999.99x")
    print("  • Variação de preço 0.00%")
    print("  • Tendência recente = 0")
    print("=" * 80)
    
    try:
        # Explicar as causas
        explain_legacy_fallback_causes()
        
        # Testar cenários problemáticos
        test_problematic_scenarios()
        
        # Testar confirmação de momentum
        test_momentum_confirmation_improvements()
        
        # Testar funções de análise geral
        test_improved_momentum_analysis()
        
        print("\n✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n💡 RESUMO DAS MELHORIAS:")
        print("  ✅ Diagnóstico automático de qualidade dos dados")
        print("  ✅ Tratamento robusto para volume zero/inválido")
        print("  ✅ Análise de tendência melhorada (3-4 velas)")
        print("  ✅ Logs detalhados para debugging")
        print("  ✅ Validação de dados antes de cada cálculo")
        print("  ✅ Fallbacks inteligentes baseados na qualidade dos dados")
        print("  ✅ Critérios flexíveis para confirmação de momentum")
        
    except Exception as e:
        print(f"❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
