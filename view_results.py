#!/usr/bin/env python3
# view_results.py
# Script para visualizar e analisar os resultados do paper trading

import json
import os
from datetime import datetime
import pandas as pd

def load_results(filename="paper_trading_results.json"):
    """Carrega resultados do arquivo JSON."""
    try:
        if not os.path.exists(filename):
            print(f"❌ Arquivo {filename} não encontrado.")
            return None
            
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar resultados: {e}")
        return None

def print_summary(results):
    """Imprime resumo dos resultados."""
    if not results:
        return
        
    summary = results['summary']
    
    print("="*60)
    print("📊 RESUMO DOS RESULTADOS DO PAPER TRADING")
    print("="*60)
    
    print(f"💰 Saldo Inicial: ${summary['initial_balance']:.2f}")
    print(f"💳 Saldo Final: ${summary['final_balance']:.2f}")
    print(f"📈 P&L Total: ${summary['total_pnl']:+.2f}")
    print(f"🎯 ROI: {summary['roi_percent']:+.2f}%")
    print()
    
    print(f"📊 Total de Trades: {summary['total_trades']}")
    print(f"🟢 Trades Vencedores: {summary['winning_trades']}")
    print(f"🔴 Trades Perdedores: {summary['losing_trades']}")
    print(f"🏆 Taxa de Acerto: {summary['win_rate']:.1f}%")
    print()
    
    print(f"💚 Lucro Total: ${summary['total_profit']:.2f}")
    print(f"💔 Prejuízo Total: ${summary['total_loss']:.2f}")
    
    if summary['total_profit'] > 0 and summary['total_loss'] > 0:
        profit_factor = summary['total_profit'] / summary['total_loss']
        print(f"📊 Profit Factor: {profit_factor:.2f}")
    
    print("="*60)

def analyze_trades(results):
    """Analisa trades individuais."""
    if not results or not results['trade_history']:
        print("ℹ️  Nenhum trade executado ainda.")
        return
        
    trades = results['trade_history']
    df = pd.DataFrame(trades)
    
    print("\n📈 ANÁLISE DETALHADA DOS TRADES")
    print("-"*60)
    
    # Estatísticas por símbolo
    print("📊 Performance por Símbolo:")
    symbol_stats = df.groupby('symbol').agg({
        'pnl_usd': ['count', 'sum', 'mean'],
        'pnl_pct': ['mean'],
        'duration_minutes': ['mean']
    }).round(2)
    
    print(symbol_stats)
    
    # Melhores e piores trades
    print(f"\n🏆 Melhor Trade:")
    best_trade = df.loc[df['pnl_usd'].idxmax()]
    print(f"   {best_trade['symbol']} - {best_trade['side'].upper()}: ${best_trade['pnl_usd']:+.2f} ({best_trade['pnl_pct']:+.2f}%)")
    
    print(f"\n💔 Pior Trade:")
    worst_trade = df.loc[df['pnl_usd'].idxmin()]
    print(f"   {worst_trade['symbol']} - {worst_trade['side'].upper()}: ${worst_trade['pnl_usd']:+.2f} ({worst_trade['pnl_pct']:+.2f}%)")
    
    # Duração média dos trades
    avg_duration = df['duration_minutes'].mean()
    print(f"\n⏱️  Duração Média dos Trades: {avg_duration:.1f} minutos")
    
    # Distribuição de P&L
    print(f"\n📊 Distribuição de P&L:")
    print(f"   Trades > $1: {len(df[df['pnl_usd'] > 1])}")
    print(f"   Trades $0-$1: {len(df[(df['pnl_usd'] > 0) & (df['pnl_usd'] <= 1)])}")
    print(f"   Trades $0-(-$1): {len(df[(df['pnl_usd'] < 0) & (df['pnl_usd'] >= -1)])}")
    print(f"   Trades < -$1: {len(df[df['pnl_usd'] < -1])}")

def show_recent_trades(results, n=10):
    """Mostra os últimos N trades."""
    if not results or not results['trade_history']:
        return
        
    trades = results['trade_history']
    recent_trades = trades[-n:] if len(trades) >= n else trades
    
    print(f"\n📋 ÚLTIMOS {len(recent_trades)} TRADES")
    print("-"*80)
    
    for i, trade in enumerate(recent_trades, 1):
        pnl_emoji = "🟢" if trade['pnl_usd'] > 0 else "🔴"
        side_emoji = "📈" if trade['side'] == 'long' else "📉"
        
        entry_time = datetime.fromisoformat(trade['entry_time']).strftime("%H:%M")
        duration = trade['duration_minutes']
        
        print(f"{i:2d}. {pnl_emoji} {side_emoji} {trade['symbol']:<15} | "
              f"${trade['entry_price']:>8.4f} → ${trade['exit_price']:>8.4f} | "
              f"P&L: ${trade['pnl_usd']:>+6.2f} ({trade['pnl_pct']:>+5.1f}%) | "
              f"{duration:>4.1f}min | {entry_time}")

def main():
    """Função principal."""
    print("🔍 VISUALIZADOR DE RESULTADOS DO PAPER TRADING")
    print()
    
    # Carregar resultados
    results = load_results()
    if not results:
        return
    
    # Mostrar resumo
    print_summary(results)
    
    # Mostrar trades recentes
    show_recent_trades(results)
    
    # Análise detalhada se houver trades
    if results['trade_history']:
        analyze_trades(results)
    
    print(f"\n📅 Dados atualizados em: {results['timestamp']}")
    print(f"📁 Arquivo: paper_trading_results.json")

if __name__ == "__main__":
    main()
