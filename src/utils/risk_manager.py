# src/utils/risk_manager.py
# Sistema de gerenciamento de risco baseado nas configurações

import time
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Adicionar config ao path
config_path = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_path))

try:
    from settings import (
        MAX_CONCURRENT_TRADES, MAX_DAILY_LOSS, MAX_POSITION_SIZE_PCT,
        TRADE_VALUE_USD, STOP_LOSS_PCT, TAKE_PROFIT_PCT, INITIAL_BALANCE
    )
except ImportError:
    # Valores padrão se não conseguir importar
    MAX_CONCURRENT_TRADES = 5
    MAX_DAILY_LOSS = 200.0
    MAX_POSITION_SIZE_PCT = 10.0
    TRADE_VALUE_USD = 50.0
    STOP_LOSS_PCT = 2.0
    TAKE_PROFIT_PCT = 5.0

class RiskManager:
    """Gerenciador de risco para controlar exposição e perdas."""
    
    def __init__(self, initial_balance: float = INITIAL_BALANCE):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.daily_pnl = 0.0
        self.open_positions: Dict[str, Dict] = {}
        self.trade_history: List[Dict] = []
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self._lock = threading.RLock()
    
    def _reset_daily_stats(self):
        """Reseta estatísticas diárias se necessário."""
        now = datetime.now()
        next_reset = self.daily_reset_time + timedelta(days=1)
        
        if now >= next_reset:
            self.daily_pnl = 0.0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def can_open_position(self, symbol: str, trade_value: float) -> Tuple[bool, str]:
        """Verifica se é seguro abrir uma nova posição."""
        with self._lock:
            self._reset_daily_stats()
            
            # Verificar número máximo de trades simultâneos
            if len(self.open_positions) >= MAX_CONCURRENT_TRADES:
                return False, f"Máximo de {MAX_CONCURRENT_TRADES} trades simultâneos atingido"
            
            # Verificar se já tem posição no símbolo
            if symbol in self.open_positions:
                return False, f"Posição já aberta para {symbol}"
            
            # Verificar perda diária máxima
            if self.daily_pnl <= -MAX_DAILY_LOSS:
                return False, f"Perda diária máxima de ${MAX_DAILY_LOSS} atingida"
            
            # Verificar tamanho máximo da posição
            max_position_value = self.current_balance * (MAX_POSITION_SIZE_PCT / 100)
            if trade_value > max_position_value:
                return False, f"Valor da posição excede {MAX_POSITION_SIZE_PCT}% do capital"
            
            # Verificar saldo suficiente
            if trade_value > self.current_balance:
                return False, f"Saldo insuficiente: ${self.current_balance:.2f}"
            
            return True, "Posição aprovada pelo gerenciador de risco"
    
    def open_position(self, symbol: str, side: str, entry_price: float, 
                     trade_value: float, leverage: int = 1) -> bool:
        """Registra abertura de posição."""
        with self._lock:
            can_open, message = self.can_open_position(symbol, trade_value)
            if not can_open:
                print(f"🚫 [RISK] Posição rejeitada: {message}")
                return False
            
            # Calcular stop loss e take profit
            if side.lower() in ['long', 'buy']:
                stop_loss_price = entry_price * (1 - STOP_LOSS_PCT / 100)
                take_profit_price = entry_price * (1 + TAKE_PROFIT_PCT / 100)
            else:  # short/sell
                stop_loss_price = entry_price * (1 + STOP_LOSS_PCT / 100)
                take_profit_price = entry_price * (1 - TAKE_PROFIT_PCT / 100)
            
            position = {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'trade_value': trade_value,
                'leverage': leverage,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'open_time': datetime.now(),
                'quantity': (trade_value * leverage) / entry_price
            }
            
            self.open_positions[symbol] = position
            self.current_balance -= trade_value  # Reservar margem
            
            print(f"✅ [RISK] Posição aprovada: {symbol} {side.upper()}")
            print(f"   💰 SL: ${stop_loss_price:.4f} | TP: ${take_profit_price:.4f}")
            
            return True
    
    def close_position(self, symbol: str, exit_price: float) -> Optional[Dict]:
        """Registra fechamento de posição e calcula P&L."""
        with self._lock:
            if symbol not in self.open_positions:
                return None
            
            position = self.open_positions[symbol]
            
            # Calcular P&L
            entry_price = position['entry_price']
            side = position['side']
            trade_value = position['trade_value']
            leverage = position['leverage']
            
            if side.lower() in ['long', 'buy']:
                price_change_pct = ((exit_price - entry_price) / entry_price) * 100
            else:  # short/sell
                price_change_pct = ((entry_price - exit_price) / entry_price) * 100
            
            pnl_pct = price_change_pct * leverage
            pnl_usd = (pnl_pct / 100) * trade_value
            
            # Atualizar saldos
            self.current_balance += trade_value + pnl_usd  # Devolver margem + P&L
            self.daily_pnl += pnl_usd
            
            # Criar registro do trade
            trade_record = {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'trade_value': trade_value,
                'leverage': leverage,
                'pnl_usd': pnl_usd,
                'pnl_pct': pnl_pct,
                'open_time': position['open_time'],
                'close_time': datetime.now(),
                'duration': datetime.now() - position['open_time']
            }
            
            self.trade_history.append(trade_record)
            del self.open_positions[symbol]
            
            print(f"📊 [RISK] Trade fechado: {symbol} P&L: ${pnl_usd:+.2f}")
            print(f"   💳 Saldo: ${self.current_balance:.2f} | P&L Diário: ${self.daily_pnl:+.2f}")
            
            return trade_record
    
    def should_close_position(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        """Verifica se uma posição deve ser fechada por stop loss ou take profit."""
        with self._lock:
            if symbol not in self.open_positions:
                return False, "Posição não encontrada"
            
            position = self.open_positions[symbol]
            side = position['side']
            stop_loss = position['stop_loss_price']
            take_profit = position['take_profit_price']
            
            if side.lower() in ['long', 'buy']:
                if current_price <= stop_loss:
                    return True, f"Stop Loss atingido: ${current_price:.4f} <= ${stop_loss:.4f}"
                elif current_price >= take_profit:
                    return True, f"Take Profit atingido: ${current_price:.4f} >= ${take_profit:.4f}"
            else:  # short/sell
                if current_price >= stop_loss:
                    return True, f"Stop Loss atingido: ${current_price:.4f} >= ${stop_loss:.4f}"
                elif current_price <= take_profit:
                    return True, f"Take Profit atingido: ${current_price:.4f} <= ${take_profit:.4f}"
            
            return False, "Posição dentro dos limites"
    
    def get_risk_metrics(self) -> Dict:
        """Retorna métricas de risco atuais."""
        with self._lock:
            self._reset_daily_stats()
            
            # Calcular exposição total
            total_exposure = sum(pos['trade_value'] for pos in self.open_positions.values())
            exposure_pct = (total_exposure / self.current_balance) * 100 if self.current_balance > 0 else 0
            
            # Calcular P&L não realizado
            unrealized_pnl = 0.0  # Seria necessário preço atual para calcular
            
            return {
                'current_balance': self.current_balance,
                'daily_pnl': self.daily_pnl,
                'open_positions_count': len(self.open_positions),
                'max_positions': MAX_CONCURRENT_TRADES,
                'total_exposure': total_exposure,
                'exposure_percentage': exposure_pct,
                'daily_loss_limit': MAX_DAILY_LOSS,
                'remaining_daily_loss': max(0, MAX_DAILY_LOSS + self.daily_pnl),
                'total_trades': len(self.trade_history)
            }
    
    def get_position_info(self, symbol: str) -> Optional[Dict]:
        """Retorna informações de uma posição específica."""
        with self._lock:
            return self.open_positions.get(symbol, None)

# Instância global do gerenciador de risco
risk_manager = RiskManager()

# Funções de conveniência
def can_open_trade(symbol: str, trade_value: float) -> Tuple[bool, str]:
    """Verifica se é seguro abrir um trade."""
    return risk_manager.can_open_position(symbol, trade_value)

def register_trade_open(symbol: str, side: str, entry_price: float, 
                       trade_value: float, leverage: int = 1) -> bool:
    """Registra abertura de trade."""
    return risk_manager.open_position(symbol, side, entry_price, trade_value, leverage)

def register_trade_close(symbol: str, exit_price: float) -> Optional[Dict]:
    """Registra fechamento de trade."""
    return risk_manager.close_position(symbol, exit_price)

def check_stop_loss_take_profit(symbol: str, current_price: float) -> Tuple[bool, str]:
    """Verifica se deve fechar por SL/TP."""
    return risk_manager.should_close_position(symbol, current_price)

def get_risk_status() -> Dict:
    """Retorna status do gerenciador de risco."""
    return risk_manager.get_risk_metrics()
