# paper_trading.py
# Módulo de simulação de trading (paper trading) para testar estratégias sem usar dinheiro real

import time
from datetime import datetime
import json
import os
import sys

# Adicionar src ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar configurações centralizadas
from config.settings import TRADING_CONFIG, LOGGING_CONFIG

# Importar sistemas de utilidades
from src.utils.logger import get_logger
from src.utils.risk_manager import risk_manager
from src.utils.performance import performance_monitor

class PaperTradingSimulator:
    """Simulador de trading que rastreia posições e P&L virtuais."""
    
    def __init__(self, initial_balance=None):
        # Usar configuração centralizada se não especificado
        if initial_balance is None:
            initial_balance = TRADING_CONFIG['INITIAL_BALANCE']
            
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}  # {symbol: {'side': 'long/short', 'entry_price': float, 'quantity': float, 'entry_time': timestamp}}
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        
        # Configurar logger
        self.logger = get_logger('paper_trading')
        
    def open_position(self, symbol, side, price, trade_value_usd=None, leverage=None):
        """Simula abertura de posição."""
        try:
            # Usar configurações padrão se não especificado
            if trade_value_usd is None:
                trade_value_usd = TRADING_CONFIG['TRADE_VALUE_USD']
            if leverage is None:
                leverage = TRADING_CONFIG['LEVERAGE_LEVEL']
                
            if symbol in self.positions:
                self.logger.warning(f"Já existe posição aberta para {symbol}")
                return False
            
            # Verificar limites de risco
            if not risk_manager.can_open_position(symbol, trade_value_usd):
                self.logger.warning(f"Posição bloqueada pelo gerenciador de risco: {symbol}")
                return False
            
            # Normalizar side para compatibilidade
            side_normalized = side.lower()
            if side_normalized in ['buy', 'long']:
                side_normalized = 'long'
            elif side_normalized in ['sell', 'short']:
                side_normalized = 'short'
            else:
                self.logger.error(f"Side inválido: {side}. Use 'long'/'BUY' ou 'short'/'SELL'")
                return False
            
            # Calcular quantidade
            quantity = (trade_value_usd * leverage) / price
            
            # Verificar se tem saldo suficiente
            required_margin = trade_value_usd
            if required_margin > self.current_balance:
                self.logger.error(f"Saldo insuficiente para {symbol}. Necessário: ${required_margin:.2f}, Disponível: ${self.current_balance:.2f}")
                return False
            
            # Abrir posição
            self.positions[symbol] = {
                'side': side_normalized,
                'entry_price': price,
                'quantity': quantity,
                'trade_value': trade_value_usd,
                'leverage': leverage,
                'entry_time': datetime.now(),
                'margin_used': required_margin
            }
            
            # Reduzir saldo disponível (margem)
            self.current_balance -= required_margin
            
            self.logger.info(f"Posição {side_normalized.upper()} aberta para {symbol} - Preço: ${price:.4f}, Valor: ${trade_value_usd:.2f}, Alavancagem: {leverage}x")
            
            # Registrar posição no gerenciador de risco
            risk_manager.add_position(symbol, side_normalized, trade_value_usd)
            
            # Registrar no monitor de performance
            performance_monitor.record_trade_start(symbol, side_normalized, price, trade_value_usd)
            
            # Salvar resultados em tempo real
            self.auto_save_results()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao abrir posição {symbol}: {e}")
            return False
    
    def close_position(self, symbol, current_price):
        """Simula fechamento de posição e calcula P&L."""
        try:
            if symbol not in self.positions:
                self.logger.warning(f"Nenhuma posição encontrada para {symbol}")
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
                result_text = "LUCRO"
            else:
                self.losing_trades += 1
                self.total_loss += abs(pnl_usd)
                result_text = "PREJUÍZO"
            
            # Registrar trade no histórico
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
            
            # Log do fechamento
            self.logger.info(f"Posição {side.upper()} fechada para {symbol} - {result_text} - P&L: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
            
            # Registrar fechamento no gerenciador de risco
            risk_manager.remove_position(symbol)
            
            # Registrar no monitor de performance
            performance_monitor.record_trade_end(symbol, current_price, pnl_usd)
            
            # Remover posição
            del self.positions[symbol]
            
            # Mostrar estatísticas atualizadas
            self._print_summary()
            
            # Salvar resultados em tempo real
            self.auto_save_results()
            
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
    
    def save_results(self, filename=None):
        """Salva resultados em arquivo JSON."""
        try:
            # Usar caminho configurado se não especificado
            if filename is None:
                data_dir = LOGGING_CONFIG['DATA_DIR']
                filename = os.path.join(data_dir, 'paper_trading_results.json')
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Converter posições abertas para formato serializável
            open_positions_serializable = {}
            for symbol, pos in self.positions.items():
                pos_copy = pos.copy()
                # Converter datetime para string ISO
                if 'entry_time' in pos_copy and hasattr(pos_copy['entry_time'], 'isoformat'):
                    pos_copy['entry_time'] = pos_copy['entry_time'].isoformat()
                open_positions_serializable[symbol] = pos_copy
            
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
                'open_positions': open_positions_serializable,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Resultados salvos em: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar resultados: {e}")
            return False
    
    def auto_save_results(self):
        """Salva resultados automaticamente sem imprimir mensagem."""
        success = self.save_results()
        if success:
            # Silencioso - apenas salva sem log debug
            pass

# Instância global do simulador usando configuração centralizada
paper_trader = PaperTradingSimulator()

# =============================================================================
# FUNÇÕES DE COMPATIBILIDADE PARA O MAIN.PY
# =============================================================================

def paper_open_long_position(client_or_symbol, symbol_or_price=None, trade_value_usd=None, leverage_or_stop_loss=1):
    """Função de compatibilidade para abrir posição LONG."""
    # Detectar assinatura: se primeiro parâmetro é string, usar nova assinatura
    if isinstance(client_or_symbol, str):
        # Nova assinatura: (symbol, current_price, trade_value_usd, leverage=1)
        symbol = client_or_symbol
        current_price = symbol_or_price
        value = trade_value_usd if trade_value_usd is not None else TRADING_CONFIG['TRADE_VALUE_USD']
        leverage = leverage_or_stop_loss if leverage_or_stop_loss != 1 else TRADING_CONFIG['LEVERAGE_LEVEL']
        return paper_trader.open_position(symbol, "BUY", current_price, value, leverage)
    else:
        # Assinatura antiga: (client, symbol, trade_value_usd, stop_loss_pct)
        client = client_or_symbol
        symbol = symbol_or_price
        value = trade_value_usd if trade_value_usd is not None else TRADING_CONFIG['TRADE_VALUE_USD']
        stop_loss_pct = leverage_or_stop_loss if leverage_or_stop_loss != 1 else TRADING_CONFIG['STOP_LOSS_PCT']
        
        return paper_open_long_position_advanced(client, symbol, value, stop_loss_pct)

def paper_open_short_position(client_or_symbol, symbol_or_price=None, trade_value_usd=None, leverage_or_stop_loss=1):
    """Função de compatibilidade para abrir posição SHORT."""
    # Detectar assinatura: se primeiro parâmetro é string, usar nova assinatura
    if isinstance(client_or_symbol, str):
        # Nova assinatura: (symbol, current_price, trade_value_usd, leverage=1)
        symbol = client_or_symbol
        current_price = symbol_or_price
        value = trade_value_usd if trade_value_usd is not None else TRADING_CONFIG['TRADE_VALUE_USD']
        leverage = leverage_or_stop_loss if leverage_or_stop_loss != 1 else TRADING_CONFIG['LEVERAGE_LEVEL']
        return paper_trader.open_position(symbol, "SELL", current_price, value, leverage)
    else:
        # Assinatura antiga: (client, symbol, trade_value_usd, stop_loss_pct)
        client = client_or_symbol
        symbol = symbol_or_price
        value = trade_value_usd if trade_value_usd is not None else TRADING_CONFIG['TRADE_VALUE_USD']
        stop_loss_pct = leverage_or_stop_loss if leverage_or_stop_loss != 1 else TRADING_CONFIG['STOP_LOSS_PCT']
        
        return paper_open_short_position_advanced(client, symbol, value, stop_loss_pct)

def paper_close_position(client_or_symbol, symbol_or_price=None):
    """Função de compatibilidade para fechar posição."""
    # Detectar assinatura: se primeiro parâmetro é string, usar nova assinatura
    if isinstance(client_or_symbol, str) and symbol_or_price is not None:
        # Nova assinatura: (symbol, current_price)
        symbol = client_or_symbol
        current_price = symbol_or_price
        return paper_trader.close_position(symbol, current_price)
    else:
        # Assinatura antiga: (client, symbol)
        client = client_or_symbol
        symbol = symbol_or_price
        
        return paper_close_position_advanced(client, symbol)

def paper_save_results():
    """Função de compatibilidade para salvar resultados."""
    return paper_trader.auto_save_results()

# =============================================================================
# FUNÇÕES AVANÇADAS DO PAPER_ORDERS.PY INTEGRADAS
# =============================================================================

def paper_open_long_position_advanced(client, symbol, trade_value_usd=None, stop_loss_pct=None):
    """Simula abertura de posição LONG com integração à API da Binance."""
    try:
        # Usar configurações padrão se não especificado
        if trade_value_usd is None:
            trade_value_usd = TRADING_CONFIG['TRADE_VALUE_USD']
        if stop_loss_pct is None:
            stop_loss_pct = TRADING_CONFIG['STOP_LOSS_PCT']
            
        print(f"\n>>> [SIMULAÇÃO] Iniciando abertura de posição LONG para {symbol}...")
        
        # Converter símbolo para formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # Obter preço atual real
        ticker = client.futures_ticker(symbol=binance_symbol)
        current_price = float(ticker['lastPrice'])
        
        # Simular abertura da posição
        success = paper_trader.open_position(
            symbol=symbol,
            side='long',
            price=current_price,
            trade_value_usd=trade_value_usd,
            leverage=TRADING_CONFIG['LEVERAGE_LEVEL']
        )
        
        if success:
            print(f"✅ [SIMULAÇÃO] Posição LONG simulada criada para {symbol}")
            print(f"   📝 Stop-loss seria configurado em: ${current_price * (1 - stop_loss_pct / 100):.4f}")
        
        return success
        
    except Exception as e:
        print(f"❌ [SIMULAÇÃO] Erro ao simular posição LONG para {symbol}: {e}")
        return False

def paper_open_short_position_advanced(client, symbol, trade_value_usd=None, stop_loss_pct=None):
    """Simula abertura de posição SHORT com integração à API da Binance."""
    try:
        # Usar configurações padrão se não especificado
        if trade_value_usd is None:
            trade_value_usd = TRADING_CONFIG['TRADE_VALUE_USD']
        if stop_loss_pct is None:
            stop_loss_pct = TRADING_CONFIG['STOP_LOSS_PCT']
            
        print(f"\n>>> [SIMULAÇÃO] Iniciando abertura de posição SHORT para {symbol}...")
        
        # Converter símbolo para formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # Obter preço atual real
        ticker = client.futures_ticker(symbol=binance_symbol)
        current_price = float(ticker['lastPrice'])
        
        # Simular abertura da posição
        success = paper_trader.open_position(
            symbol=symbol,
            side='short',
            price=current_price,
            trade_value_usd=trade_value_usd,
            leverage=TRADING_CONFIG['LEVERAGE_LEVEL']
        )
        
        if success:
            print(f"✅ [SIMULAÇÃO] Posição SHORT simulada criada para {symbol}")
            print(f"   📝 Stop-loss seria configurado em: ${current_price * (1 + stop_loss_pct / 100):.4f}")
        
        return success
        
    except Exception as e:
        print(f"❌ [SIMULAÇÃO] Erro ao simular posição SHORT para {symbol}: {e}")
        return False

def paper_close_position_advanced(client, symbol):
    """Simula fechamento de posição com integração à API da Binance."""
    try:
        print(f"\n>>> [SIMULAÇÃO] Tentando fechar posição simulada para {symbol}...")
        
        # Verificar se tem posição
        if not paper_trader.has_position(symbol):
            print(f"ℹ️  [SIMULAÇÃO] Nenhuma posição simulada encontrada para {symbol}")
            return True
        
        # Converter símbolo para formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # Obter preço atual real para calcular P&L
        ticker = client.futures_ticker(symbol=binance_symbol)
        current_price = float(ticker['lastPrice'])
        
        # Fechar posição simulada
        success = paper_trader.close_position(symbol, current_price)
        
        if success:
            print(f"✅ [SIMULAÇÃO] Posição simulada fechada para {symbol}")
        
        return success
        
    except Exception as e:
        print(f"❌ [SIMULAÇÃO] Erro ao fechar posição simulada para {symbol}: {e}")
        return False

def paper_get_position_status(symbol):
    """Retorna status da posição simulada."""
    position = paper_trader.get_position(symbol)
    if position:
        return f"IN_{position['side'].upper()}"
    return 'MONITORING'
