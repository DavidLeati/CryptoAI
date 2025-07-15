#!/usr/bin/env python3
"""
Teste do Paper Trading com Tarifas Realistas
Demonstra o impacto das tarifas de 0,05% da Binance na simulação.
"""

import sys
from pathlib import Path
import time

# Adicionar o caminho do projeto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.trading.paper_trading import PaperTradingSimulator
from config.settings import TRADING_CONFIG

def test_fees_impact():
    """
    Testa o impacto das tarifas na simulação de paper trading.
    """
    print("🧪 TESTE DE PAPER TRADING COM TARIFAS REALISTAS")
    print("=" * 65)
    
    # Mostrar configurações de tarifas
    print("\n📋 CONFIGURAÇÕES DE TARIFAS:")
    print(f"   💸 Taxa de Trading: {TRADING_CONFIG.get('TRADING_FEE', 0) * 100:.3f}%")
    print(f"   📥 Taxa de Entrada: {TRADING_CONFIG.get('ENTRY_FEE', 0) * 100:.3f}%")
    print(f"   📤 Taxa de Saída: {TRADING_CONFIG.get('EXIT_FEE', 0) * 100:.3f}%")
    print(f"   🌊 Slippage: {TRADING_CONFIG.get('SLIPPAGE', 0) * 100:.3f}%")
    print(f"   🎯 Tarifas Realistas: {'✅ ATIVAS' if TRADING_CONFIG.get('REALISTIC_FEES') else '❌ DESATIVADAS'}")
    
    # Criar simulador
    simulator = PaperTradingSimulator(initial_balance=10000.0)
    
    print(f"\n💰 Saldo Inicial: ${simulator.initial_balance:.2f}")
    print(f"📊 Valor por Trade: ${TRADING_CONFIG['TRADE_VALUE_USD']:.2f}")
    print(f"🔢 Alavancagem: {TRADING_CONFIG['LEVERAGE_LEVEL']}x")
    
    # Simular cenário: 10 trades rápidos (como um bot ativo)
    print(f"\n🤖 SIMULANDO BOT ATIVO - 10 TRADES RÁPIDOS")
    print("-" * 50)
    
    test_prices = [
        50000.0,  # Entrada 1
        50100.0,  # Saída 1 (+0.2%)
        50050.0,  # Entrada 2
        49950.0,  # Saída 2 (-0.2%)
        49980.0,  # Entrada 3
        50080.0,  # Saída 3 (+0.2%)
        50060.0,  # Entrada 4
        49960.0,  # Saída 4 (-0.2%)
        49990.0,  # Entrada 5
        50090.0,  # Saída 5 (+0.2%)
    ]
    
    trade_count = 0
    
    for i in range(0, len(test_prices), 2):
        if i + 1 >= len(test_prices):
            break
            
        trade_count += 1
        entry_price = test_prices[i]
        exit_price = test_prices[i + 1]
        
        symbol = f"BTCUSDT"
        side = 'long' if exit_price > entry_price else 'long'  # Sempre long para simplicidade
        
        print(f"\n📊 TRADE #{trade_count}:")
        print(f"   🚀 Abrindo posição {side.upper()} em ${entry_price:.2f}")
        
        # Abrir posição
        success = simulator.open_position(symbol, side, entry_price)
        
        if success:
            print(f"   ✅ Posição aberta com sucesso")
            
            # Simular tempo de trade
            time.sleep(0.1)
            
            print(f"   🏁 Fechando posição em ${exit_price:.2f}")
            
            # Fechar posição
            simulator.close_position(symbol, exit_price)
        else:
            print(f"   ❌ Falha ao abrir posição")
    
    print(f"\n" + "=" * 65)
    print("📈 ANÁLISE DO IMPACTO DAS TARIFAS")
    print("=" * 65)
    
    # Calcular estatísticas
    total_fees = sum(trade.get('total_fees', 0.0) for trade in simulator.trade_history)
    total_gross_pnl = sum(trade.get('pnl_gross_usd', 0.0) for trade in simulator.trade_history)
    total_net_pnl = simulator.current_balance - simulator.initial_balance
    
    print(f"\n💰 RESUMO FINANCEIRO:")
    print(f"   🏦 Saldo Final: ${simulator.current_balance:.2f}")
    print(f"   📈 P&L Bruto: ${total_gross_pnl:+.2f}")
    print(f"   💸 Total em Tarifas: ${total_fees:.2f}")
    print(f"   📉 P&L Líquido: ${total_net_pnl:+.2f}")
    print(f"   🔢 Trades Executados: {simulator.total_trades}")
    
    if simulator.total_trades > 0:
        print(f"\n📊 ANÁLISE POR TRADE:")
        print(f"   💸 Taxa Média por Trade: ${total_fees / simulator.total_trades:.2f}")
        print(f"   📉 Impacto das Tarifas: {total_fees / simulator.initial_balance * 100:.3f}% do capital")
        
        # Calcular impacto por operação
        operations_count = simulator.total_trades * 2  # Entrada + Saída
        operations_per_minute = 10  # Conforme mencionado pelo usuário
        
        print(f"\n⚡ IMPACTO EM OPERAÇÕES FREQUENTES:")
        print(f"   🔄 Total de Operações: {operations_count} (entrada + saída)")
        print(f"   ⏱️  Operações por Minuto: {operations_per_minute}")
        print(f"   💸 Custo por Operação: ${total_fees / operations_count:.4f}")
        print(f"   📊 Custo por Hora: ${(total_fees / operations_count) * operations_per_minute * 60:.2f}")
        print(f"   📅 Custo por Dia (24h): ${(total_fees / operations_count) * operations_per_minute * 60 * 24:.2f}")
    
    # Exemplo de cenário otimista vs realista
    print(f"\n🔍 COMPARATIVO SEM VS COM TARIFAS:")
    print(f"   📈 Resultado Bruto (sem tarifas): ${total_gross_pnl:+.2f}")
    print(f"   💸 Desconto de Tarifas: ${-total_fees:.2f}")
    print(f"   📉 Resultado Líquido (com tarifas): ${total_net_pnl:+.2f}")
    print(f"   🎯 Diferença: {((total_net_pnl - total_gross_pnl) / abs(total_gross_pnl) * 100) if total_gross_pnl != 0 else 0:.1f}%")
    
    # Dicas para otimização
    print(f"\n💡 DICAS PARA OTIMIZAÇÃO:")
    print(f"   🎯 Para compensar as tarifas, cada trade precisa de:")
    if TRADING_CONFIG.get('REALISTIC_FEES'):
        min_profit_pct = (TRADING_CONFIG.get('ENTRY_FEE', 0) + TRADING_CONFIG.get('EXIT_FEE', 0)) * 100
        min_profit_leveraged = min_profit_pct / TRADING_CONFIG['LEVERAGE_LEVEL']
        print(f"      📊 Mínimo {min_profit_pct:.3f}% de movimento de preço")
        print(f"      🔢 Com {TRADING_CONFIG['LEVERAGE_LEVEL']}x alavancagem: {min_profit_leveraged:.3f}% de movimento")
    
    print(f"   ⚡ Reduzir frequência de trades quando possível")
    print(f"   🎯 Focar em sinais com maior probabilidade de sucesso")
    print(f"   📈 Considerar stop-loss e take-profit mais amplos")
    
    return simulator

def compare_with_without_fees():
    """
    Compara simulação com e sem tarifas para mostrar o impacto.
    """
    print(f"\n🔬 COMPARAÇÃO: COM vs SEM TARIFAS")
    print("=" * 50)
    
    # Teste sem tarifas
    print("\n📊 Simulação SEM tarifas:")
    TRADING_CONFIG['REALISTIC_FEES'] = False
    sim_without_fees = test_simple_scenario()
    
    # Teste com tarifas
    print("\n📊 Simulação COM tarifas:")
    TRADING_CONFIG['REALISTIC_FEES'] = True
    sim_with_fees = test_simple_scenario()
    
    # Comparação
    pnl_without = sim_without_fees.current_balance - sim_without_fees.initial_balance
    pnl_with = sim_with_fees.current_balance - sim_with_fees.initial_balance
    difference = pnl_with - pnl_without
    
    print(f"\n📈 RESULTADO DA COMPARAÇÃO:")
    print(f"   💰 Sem tarifas: ${pnl_without:+.2f}")
    print(f"   💸 Com tarifas: ${pnl_with:+.2f}")
    print(f"   📉 Diferença: ${difference:+.2f}")
    print(f"   📊 Impacto: {difference / abs(pnl_without) * 100 if pnl_without != 0 else 0:.1f}%")

def test_simple_scenario():
    """Cenário simples para comparação."""
    simulator = PaperTradingSimulator(initial_balance=1000.0)
    
    # 5 trades simples
    trades = [
        (50000, 50100),  # +0.2%
        (50100, 50200),  # +0.2%
        (50200, 50100),  # -0.2%
        (50100, 50200),  # +0.2%
        (50200, 50300),  # +0.2%
    ]
    
    for i, (entry, exit) in enumerate(trades):
        simulator.open_position(f"TEST{i}", 'long', entry)
        simulator.close_position(f"TEST{i}", exit)
    
    return simulator

def main():
    """Função principal."""
    try:
        simulator = test_fees_impact()
        compare_with_without_fees()
        
        print(f"\n🎉 TESTE CONCLUÍDO!")
        print("=" * 50)
        print("✅ Sistema de tarifas realistas implementado com sucesso!")
        print("💡 A simulação agora considera:")
        print("   📥 Taxa de entrada (0.07%)")
        print("   📤 Taxa de saída (0.07%)")
        print("   🌊 Slippage nos preços")
        print("   💸 Impacto real das tarifas no P&L")
        
        # Salvar resultados
        simulator.save_results()
        print("💾 Resultados salvos em data/paper_trading_results.json")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
