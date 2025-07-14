# paper_trading.py
# Módulo de simulação de trading (paper trading) para testar estratégias sem usar dinheiro real

import time
from datetime import datetime
import json
import os

class PaperTradingSimulator:
    """Simulador de trading que rastreia posições e P&L virtuais."""
    
    def __init__(self, initial_balance=1000.0):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}  # {symbol: {'side': 'long/short', 'entry_price': float, 'quantity': float, 'entry_time': timestamp}}
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        
    def open_position(self, symbol, side, price, trade_value_usd, leverage=1):
        """Simula abertura de posição."""
        try:
            if symbol in self.positions:
                print(f"⚠️  [SIMULAÇÃO] Já existe posição aberta para {symbol}")
                return False
            
            # Calcular quantidade
            quantity = (trade_value_usd * leverage) / price
            
            # Verificar se tem saldo suficiente
            required_margin = trade_value_usd
            if required_margin > self.current_balance:
                print(f"❌ [SIMULAÇÃO] Saldo insuficiente para {symbol}. Necessário: ${required_margin:.2f}, Disponível: ${self.current_balance:.2f}")
                return False
            
            # Abrir posição
            self.positions[symbol] = {
                'side': side,
                'entry_price': price,
                'quantity': quantity,
                'trade_value': trade_value_usd,
                'leverage': leverage,
                'entry_time': datetime.now(),
                'margin_used': required_margin
            }
            
            # Reduzir saldo disponível (margem)
            self.current_balance -= required_margin
            
            print(f"✅ [SIMULAÇÃO] Posição {side.upper()} aberta para {symbol}")
            print(f"   💰 Preço de entrada: ${price:.4f}")
            print(f"   📊 Quantidade: {quantity:.8f}")
            print(f"   💵 Valor: ${trade_value_usd:.2f} (Alavancagem: {leverage}x)")
            print(f"   💳 Saldo restante: ${self.current_balance:.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ [SIMULAÇÃO] Erro ao abrir posição {symbol}: {e}")
            return False
    
    def close_position(self, symbol, current_price):
        """Simula fechamento de posição e calcula P&L."""
        try:
            if symbol not in self.positions:
                print(f"⚠️  [SIMULAÇÃO] Nenhuma posição encontrada para {symbol}")
                return False
            
            position = self.positions[symbol]
            entry_price = position['entry_price']
            quantity = position['quantity']
            side = position['side']
            trade_value = position['trade_value']
            leverage = position['leverage']
            margin_used = position['margin_used']
            entry_time = position['entry_time']
            
            # Calcular P&L
            if side == 'long':
                price_change_pct = ((current_price - entry_price) / entry_price) * 100
                pnl_pct = price_change_pct * leverage
            else:  # short
                price_change_pct = ((entry_price - current_price) / entry_price) * 100
                pnl_pct = price_change_pct * leverage
            
            pnl_usd = (pnl_pct / 100) * trade_value
            
            # Devolver margem + P&L
            self.current_balance += margin_used + pnl_usd
            
            # Estatísticas
            duration = datetime.now() - entry_time
            self.total_trades += 1
            
            if pnl_usd > 0:
                self.winning_trades += 1
                self.total_profit += pnl_usd
                result_emoji = "🟢"
                result_text = "LUCRO"
            else:
                self.losing_trades += 1
                self.total_loss += abs(pnl_usd)
                result_emoji = "🔴"
                result_text = "PREJUÍZO"
            
            # Registrar trade
            trade_record = {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'exit_price': current_price,
                'quantity': quantity,
                'trade_value': trade_value,
                'leverage': leverage,
                'pnl_usd': pnl_usd,
                'pnl_pct': pnl_pct,
                'duration_minutes': duration.total_seconds() / 60,
                'entry_time': entry_time.isoformat(),
                'exit_time': datetime.now().isoformat()
            }
            self.trade_history.append(trade_record)
            
            print(f"{result_emoji} [SIMULAÇÃO] Posição {side.upper()} fechada para {symbol} - {result_text}")
            print(f"   📈 Entrada: ${entry_price:.4f} → Saída: ${current_price:.4f}")
            print(f"   📊 P&L: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
            print(f"   ⏱️  Duração: {duration.total_seconds()/60:.1f} minutos")
            print(f"   💳 Novo saldo: ${self.current_balance:.2f}")
            
            # Remover posição
            del self.positions[symbol]
            
            # Mostrar estatísticas atualizadas
            self._print_summary()
            
            return True
            
        except Exception as e:
            print(f"❌ [SIMULAÇÃO] Erro ao fechar posição {symbol}: {e}")
            return False
    
    def get_position(self, symbol):
        """Retorna informações da posição se existir."""
        return self.positions.get(symbol, None)
    
    def has_position(self, symbol):
        """Verifica se tem posição aberta para o símbolo."""
        return symbol in self.positions
    
    def _print_summary(self):
        """Imprime resumo das estatísticas."""
        if self.total_trades == 0:
            return
            
        win_rate = (self.winning_trades / self.total_trades) * 100
        total_pnl = self.current_balance - self.initial_balance
        roi = (total_pnl / self.initial_balance) * 100
        
        print(f"\n📊 [RESUMO DA SIMULAÇÃO]")
        print(f"   💰 Saldo inicial: ${self.initial_balance:.2f}")
        print(f"   💳 Saldo atual: ${self.current_balance:.2f}")
        print(f"   📈 P&L total: ${total_pnl:+.2f} ({roi:+.2f}%)")
        print(f"   🎯 Trades: {self.total_trades} | Vitórias: {self.winning_trades} | Derrotas: {self.losing_trades}")
        print(f"   🏆 Taxa de acerto: {win_rate:.1f}%")
        print(f"   🟢 Lucro total: ${self.total_profit:.2f}")
        print(f"   🔴 Prejuízo total: ${self.total_loss:.2f}\n")
    
    def save_results(self, filename="paper_trading_results.json"):
        """Salva resultados em arquivo JSON."""
        try:
            results = {
                'summary': {
                    'initial_balance': self.initial_balance,
                    'final_balance': self.current_balance,
                    'total_pnl': self.current_balance - self.initial_balance,
                    'roi_percent': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100,
                    'total_trades': self.total_trades,
                    'winning_trades': self.winning_trades,
                    'losing_trades': self.losing_trades,
                    'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
                    'total_profit': self.total_profit,
                    'total_loss': self.total_loss
                },
                'trade_history': self.trade_history,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Resultados salvos em: {filename}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar resultados: {e}")

# Instância global do simulador
paper_trader = PaperTradingSimulator(initial_balance=1000.0)
