# orders.py
# Módulo responsável pela execução de ordens REAIS na Binance Futures
# Integrado com as configurações centralizadas e sistema de logging

import os
import sys
from datetime import datetime
from binance.client import Client
from binance.enums import *

# Adicionar src ao path para importações
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar configurações centralizadas
from config.settings import TRADING_CONFIG, LOGGING_CONFIG, ASSETS_CONFIG

# Importar sistemas de utilidades
from src.utils.logger import get_logger
from src.utils.risk_manager import risk_manager
from src.utils.performance import performance_monitor
from src.utils.exchange_setup import setup_leverage_for_symbol

# =============================================================================
# CONFIGURAÇÕES E INICIALIZAÇÃO
# =============================================================================

# Logger específico para ordens
logger = get_logger('orders')

# Verificar se está em modo paper trading
if TRADING_CONFIG['PAPER_TRADING_MODE']:
    logger.warning("⚠️  SISTEMA EM MODO PAPER TRADING - Ordens reais desabilitadas!")
    logger.warning("   Para ativar ordens reais, defina PAPER_TRADING_MODE = False em config/settings.py")

# =============================================================================
# CLASSE PRINCIPAL PARA GERENCIAMENTO DE ORDENS
# =============================================================================

class RealTradingManager:
    """Gerenciador de ordens reais na Binance Futures."""
    
    def __init__(self, client):
        self.client = client
        self.logger = get_logger('real_trading')
        
        # Verificar modo de trading
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            self.logger.error("❌ Tentativa de usar RealTradingManager em modo PAPER TRADING!")
            raise ValueError("Sistema está em modo Paper Trading. Desative para usar ordens reais.")
        
        self.logger.info("🚀 RealTradingManager inicializado - MODO REAL ATIVO")
    
    def _normalize_symbol(self, symbol):
        """Converte símmbolo para formato da Binance."""
        return symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
    
    def _get_current_price(self, symbol):
        """Obtém preço atual do mercado."""
        try:
            binance_symbol = self._normalize_symbol(symbol)
            ticker = self.client.futures_ticker(symbol=binance_symbol)
            return float(ticker['lastPrice'])
        except Exception as e:
            self.logger.error(f"Erro ao obter preço de {symbol}: {e}")
            return None
    
    def _calculate_quantity(self, symbol, price, trade_value_usd, leverage):
        """Calcula quantidade baseada no valor em USD e alavancagem."""
        try:
            # Quantidade = (Valor em USD * Alavancagem) / Preço
            raw_quantity = (trade_value_usd * leverage) / price
            
            # Obter precisão do símbolo para arredondar corretamente
            exchange_info = self.client.futures_exchange_info()
            symbol_info = next((s for s in exchange_info['symbols'] 
                              if s['symbol'] == self._normalize_symbol(symbol)), None)
            
            if symbol_info:
                # Encontrar filtro LOT_SIZE para determinar precisão
                lot_size_filter = next((f for f in symbol_info['filters'] 
                                      if f['filterType'] == 'LOT_SIZE'), None)
                if lot_size_filter:
                    step_size = float(lot_size_filter['stepSize'])
                    # Arredondar para baixo baseado no step_size
                    quantity = (raw_quantity // step_size) * step_size
                    self.logger.debug(f"Quantidade calculada: {raw_quantity:.8f} -> {quantity:.8f}")
                    return quantity
            
            # Fallback: usar 8 casas decimais
            return round(raw_quantity, 8)
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular quantidade para {symbol}: {e}")
            return None
    
    def _setup_position_configuration(self, symbol, leverage):
        """Configura alavancagem e tipo de margem."""
        try:
            binance_symbol = self._normalize_symbol(symbol)
            
            # Configurar alavancagem
            success = setup_leverage_for_symbol(self.client, symbol, leverage)
            if not success:
                self.logger.warning(f"Falha ao configurar alavancagem para {symbol}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na configuração de {symbol}: {e}")
            return False
    
    def open_long_position(self, symbol, trade_value_usd=None, leverage=None, stop_loss_pct=None):
        """Abre posição LONG real na Binance Futures."""
        try:
            # Usar configurações padrão se não especificado
            if trade_value_usd is None:
                trade_value_usd = TRADING_CONFIG['TRADE_VALUE_USD']
            if leverage is None:
                leverage = TRADING_CONFIG['LEVERAGE_LEVEL']
            if stop_loss_pct is None:
                stop_loss_pct = TRADING_CONFIG['STOP_LOSS_PCT']
            
            self.logger.info(f"🟢 Iniciando abertura de posição LONG para {symbol}")
            self.logger.info(f"   💰 Valor: ${trade_value_usd} | 📈 Alavancagem: {leverage}x | ⛔ Stop Loss: {stop_loss_pct}%")
            
            binance_symbol = self._normalize_symbol(symbol)
            
            # Verificar permissões de risco
            if not risk_manager.can_open_position(symbol, trade_value_usd):
                self.logger.warning(f"❌ Abertura de posição negada pelo gerenciador de risco para {symbol}")
                return False
            
            # Obter preço atual
            current_price = self._get_current_price(symbol)
            if not current_price:
                return False
            
            # Configurar alavancagem
            if not self._setup_position_configuration(symbol, leverage):
                return False
            
            # Calcular quantidade
            quantity = self._calculate_quantity(symbol, current_price, trade_value_usd, leverage)
            if not quantity or quantity <= 0:
                self.logger.error(f"❌ Quantidade inválida calculada para {symbol}")
                return False
            
            self.logger.info(f"   📊 Preço atual: ${current_price:.6f}")
            self.logger.info(f"   📦 Quantidade: {quantity:.8f}")
            
            # Executar ordem de compra a mercado
            self.logger.info("📤 Enviando ordem de COMPRA a mercado...")
            order_buy = self.client.futures_create_order(
                symbol=binance_symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            # Extrair preço de execução
            if order_buy.get('fills'):
                entry_price = float(order_buy['fills'][0]['price'])
            else:
                entry_price = current_price
            
            self.logger.info(f"✅ Ordem LONG executada!")
            self.logger.info(f"   💲 Preço de entrada: ${entry_price:.6f}")
            self.logger.info(f"   🆔 Order ID: {order_buy.get('orderId', 'N/A')}")
            
            # Criar ordem de Stop Loss
            stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
            self.logger.info(f"📝 Criando Stop Loss em ${stop_loss_price:.6f}")
            
            try:
                stop_loss_order = self.client.futures_create_order(
                    symbol=binance_symbol,
                    side=SIDE_SELL,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    quantity=quantity,
                    stopPrice=stop_loss_price,
                    reduceOnly=True
                )
                self.logger.info(f"✅ Stop Loss criado! ID: {stop_loss_order.get('orderId', 'N/A')}")
            except Exception as sl_error:
                self.logger.error(f"⚠️  Falha ao criar Stop Loss: {sl_error}")
                self.logger.warning("   Posição aberta SEM proteção de Stop Loss!")
            
            # Registrar no gerenciador de risco e performance
            risk_manager.open_position(symbol, 'long', entry_price, trade_value_usd, leverage)
            performance_monitor.record_trade_start(symbol, 'long', entry_price, trade_value_usd)
            
            self.logger.info(f"🎯 Posição LONG para {symbol} aberta com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ERRO ao abrir posição LONG para {symbol}: {e}")
            return False
    
    def open_short_position(self, symbol, trade_value_usd=None, leverage=None, stop_loss_pct=None):
        """Abre posição SHORT real na Binance Futures."""
        try:
            # Usar configurações padrão se não especificado
            if trade_value_usd is None:
                trade_value_usd = TRADING_CONFIG['TRADE_VALUE_USD']
            if leverage is None:
                leverage = TRADING_CONFIG['LEVERAGE_LEVEL']
            if stop_loss_pct is None:
                stop_loss_pct = TRADING_CONFIG['STOP_LOSS_PCT']
            
            self.logger.info(f"🔴 Iniciando abertura de posição SHORT para {symbol}")
            self.logger.info(f"   💰 Valor: ${trade_value_usd} | 📈 Alavancagem: {leverage}x | ⛔ Stop Loss: {stop_loss_pct}%")
            
            binance_symbol = self._normalize_symbol(symbol)
            
            # Verificar permissões de risco
            if not risk_manager.can_open_position(symbol, trade_value_usd):
                self.logger.warning(f"❌ Abertura de posição negada pelo gerenciador de risco para {symbol}")
                return False
            
            # Obter preço atual
            current_price = self._get_current_price(symbol)
            if not current_price:
                return False
            
            # Configurar alavancagem
            if not self._setup_position_configuration(symbol, leverage):
                return False
            
            # Calcular quantidade
            quantity = self._calculate_quantity(symbol, current_price, trade_value_usd, leverage)
            if not quantity or quantity <= 0:
                self.logger.error(f"❌ Quantidade inválida calculada para {symbol}")
                return False
            
            self.logger.info(f"   📊 Preço atual: ${current_price:.6f}")
            self.logger.info(f"   📦 Quantidade: {quantity:.8f}")
            
            # Executar ordem de venda a mercado
            self.logger.info("📤 Enviando ordem de VENDA a mercado...")
            order_sell = self.client.futures_create_order(
                symbol=binance_symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            # Extrair preço de execução
            if order_sell.get('fills'):
                entry_price = float(order_sell['fills'][0]['price'])
            else:
                entry_price = current_price
            
            self.logger.info(f"✅ Ordem SHORT executada!")
            self.logger.info(f"   💲 Preço de entrada: ${entry_price:.6f}")
            self.logger.info(f"   🆔 Order ID: {order_sell.get('orderId', 'N/A')}")
            
            # Criar ordem de Stop Loss
            stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
            self.logger.info(f"📝 Criando Stop Loss em ${stop_loss_price:.6f}")
            
            try:
                stop_loss_order = self.client.futures_create_order(
                    symbol=binance_symbol,
                    side=SIDE_BUY,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    quantity=quantity,
                    stopPrice=stop_loss_price,
                    reduceOnly=True
                )
                self.logger.info(f"✅ Stop Loss criado! ID: {stop_loss_order.get('orderId', 'N/A')}")
            except Exception as sl_error:
                self.logger.error(f"⚠️  Falha ao criar Stop Loss: {sl_error}")
                self.logger.warning("   Posição aberta SEM proteção de Stop Loss!")
            
            # Registrar no gerenciador de risco e performance
            risk_manager.open_position(symbol, 'short', entry_price, trade_value_usd, leverage)
            performance_monitor.record_trade_start(symbol, 'short', entry_price, trade_value_usd)
            
            self.logger.info(f"🎯 Posição SHORT para {symbol} aberta com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ERRO ao abrir posição SHORT para {symbol}: {e}")
            return False
    
    def close_position(self, symbol):
        """Fecha posição existente e cancela ordens relacionadas."""
        try:
            self.logger.info(f"🔄 Tentando fechar posição para {symbol}")
            
            binance_symbol = self._normalize_symbol(symbol)
            
            # Verificar posição existente
            account = self.client.futures_account()
            positions = account['positions']
            position = next((p for p in positions 
                           if p['symbol'] == binance_symbol and float(p['positionAmt']) != 0), None)
            
            if not position:
                self.logger.info(f"ℹ️  Nenhuma posição ativa encontrada para {symbol}")
                # Cancelar ordens abertas por segurança
                try:
                    self.client.futures_cancel_all_open_orders(symbol=binance_symbol)
                    self.logger.info(f"🧹 Ordens abertas canceladas para {symbol}")
                except:
                    pass
                return True
            
            # Analisar posição
            position_amt = float(position['positionAmt'])
            side = 'LONG' if position_amt > 0 else 'SHORT'
            quantity = abs(position_amt)
            unrealized_pnl = float(position['unrealizedPnl'])
            
            self.logger.info(f"   📊 Posição encontrada: {side} de {quantity:.8f}")
            self.logger.info(f"   💰 PnL não realizado: ${unrealized_pnl:+.4f}")
            
            # Obter preço atual para log
            current_price = self._get_current_price(symbol)
            if current_price:
                self.logger.info(f"   💲 Preço atual: ${current_price:.6f}")
            
            # Criar ordem de fechamento
            if position_amt > 0:  # LONG position
                self.logger.info("📤 Enviando ordem de VENDA para fechar LONG...")
                close_order = self.client.futures_create_order(
                    symbol=binance_symbol,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity,
                    reduceOnly=True
                )
            else:  # SHORT position
                self.logger.info("📤 Enviando ordem de COMPRA para fechar SHORT...")
                close_order = self.client.futures_create_order(
                    symbol=binance_symbol,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity,
                    reduceOnly=True
                )
            
            # Extrair preço de fechamento
            if close_order.get('fills'):
                close_price = float(close_order['fills'][0]['price'])
                self.logger.info(f"✅ Posição fechada em ${close_price:.6f}")
            else:
                self.logger.info("✅ Posição fechada com sucesso")
            
            self.logger.info(f"   🆔 Close Order ID: {close_order.get('orderId', 'N/A')}")
            
            # Cancelar ordens abertas (ex: stop loss)
            try:
                cancelled_orders = self.client.futures_cancel_all_open_orders(symbol=binance_symbol)
                if cancelled_orders:
                    self.logger.info(f"🧹 {len(cancelled_orders)} ordens canceladas")
            except Exception as cancel_error:
                self.logger.warning(f"⚠️  Erro ao cancelar ordens: {cancel_error}")
            
            # Registrar fechamento
            risk_manager.close_position(symbol, current_price or 0)
            if current_price:
                performance_monitor.record_trade_end(symbol, current_price, unrealized_pnl)
            
            self.logger.info(f"🎯 Posição para {symbol} fechada com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ERRO ao fechar posição para {symbol}: {e}")
            return False
    
    def get_position_info(self, symbol):
        """Retorna informações detalhadas da posição."""
        try:
            binance_symbol = self._normalize_symbol(symbol)
            account = self.client.futures_account()
            positions = account['positions']
            position = next((p for p in positions 
                           if p['symbol'] == binance_symbol), None)
            
            if not position:
                return None
            
            position_amt = float(position['positionAmt'])
            if position_amt == 0:
                return None
            
            return {
                'symbol': symbol,
                'side': 'LONG' if position_amt > 0 else 'SHORT',
                'size': abs(position_amt),
                'entry_price': float(position['entryPrice']),
                'mark_price': float(position['markPrice']),
                'unrealized_pnl': float(position['unrealizedPnl']),
                'percentage': float(position['percentage']),
                'isolated_margin': float(position['isolatedMargin']),
                'position_amt': position_amt
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações da posição {symbol}: {e}")
            return None

# =============================================================================
# INSTÂNCIA GLOBAL E FUNÇÕES DE COMPATIBILIDADE
# =============================================================================

# Instância global (será inicializada quando necessário)
_real_trading_manager = None

def get_real_trading_manager(client):
    """Obtém instância do gerenciador de trading real."""
    global _real_trading_manager
    if _real_trading_manager is None:
        _real_trading_manager = RealTradingManager(client)
    return _real_trading_manager

# =============================================================================
# FUNÇÕES DE COMPATIBILIDADE (API SIMPLIFICADA)
# =============================================================================

def open_long_position(client, symbol, trade_value_usd=None, stop_loss_pct=None):
    """Função de compatibilidade para abrir posição LONG."""
    try:
        # Verificar modo de trading
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            logger.warning("⚠️  Sistema em modo PAPER TRADING - redirecionando para paper_trading.py")
            # Importar aqui para evitar circular import
            from src.trading.paper_trading import paper_open_long_position_advanced
            return paper_open_long_position_advanced(client, symbol, trade_value_usd, stop_loss_pct)
        
        # Modo real
        manager = get_real_trading_manager(client)
        return manager.open_long_position(symbol, trade_value_usd, None, stop_loss_pct)
        
    except Exception as e:
        logger.error(f"Erro na função de compatibilidade open_long_position: {e}")
        return False

def open_short_position(client, symbol, trade_value_usd=None, stop_loss_pct=None):
    """Função de compatibilidade para abrir posição SHORT."""
    try:
        # Verificar modo de trading
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            logger.warning("⚠️  Sistema em modo PAPER TRADING - redirecionando para paper_trading.py")
            # Importar aqui para evitar circular import
            from src.trading.paper_trading import paper_open_short_position_advanced
            return paper_open_short_position_advanced(client, symbol, trade_value_usd, stop_loss_pct)
        
        # Modo real
        manager = get_real_trading_manager(client)
        return manager.open_short_position(symbol, trade_value_usd, None, stop_loss_pct)
        
    except Exception as e:
        logger.error(f"Erro na função de compatibilidade open_short_position: {e}")
        return False

def close_position(client, symbol):
    """Função de compatibilidade para fechar posição."""
    try:
        # Verificar modo de trading
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            logger.warning("⚠️  Sistema em modo PAPER TRADING - redirecionando para paper_trading.py")
            # Importar aqui para evitar circular import
            from src.trading.paper_trading import paper_close_position_advanced
            return paper_close_position_advanced(client, symbol)
        
        # Modo real
        manager = get_real_trading_manager(client)
        return manager.close_position(symbol)
        
    except Exception as e:
        logger.error(f"Erro na função de compatibilidade close_position: {e}")
        return False

def get_position_status(client, symbol):
    """Retorna status da posição (real ou simulada)."""
    try:
        # Verificar modo de trading
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            # Importar aqui para evitar circular import
            from src.trading.paper_trading import paper_get_position_status
            return paper_get_position_status(symbol)
        
        # Modo real
        manager = get_real_trading_manager(client)
        position_info = manager.get_position_info(symbol)
        
        if position_info:
            return f"IN_{position_info['side']}"
        return 'MONITORING'
        
    except Exception as e:
        logger.error(f"Erro ao obter status da posição {symbol}: {e}")
        return 'ERROR'

# =============================================================================
# FUNÇÕES AVANÇADAS PARA INTEGRAÇÃO
# =============================================================================

def check_account_balance(client):
    """Verifica saldo disponível na conta de futuros."""
    try:
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            logger.info("💰 Modo Paper Trading - saldo simulado ativo")
            return True
        
        account = client.futures_account()
        available_balance = float(account['availableBalance'])
        total_balance = float(account['totalWalletBalance'])
        
        logger.info(f"💰 Saldo total: ${total_balance:.2f} USDT")
        logger.info(f"💳 Saldo disponível: ${available_balance:.2f} USDT")
        
        min_balance = TRADING_CONFIG['TRADE_VALUE_USD'] * 2  # Mínimo = 2x valor do trade
        if available_balance < min_balance:
            logger.warning(f"⚠️  Saldo baixo! Disponível: ${available_balance:.2f}, Mínimo: ${min_balance:.2f}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao verificar saldo da conta: {e}")
        return False

def list_open_positions(client):
    """Lista todas as posições abertas."""
    try:
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            logger.info("📊 Modo Paper Trading - consultando posições simuladas")
            from src.trading.paper_trading import paper_trader
            positions = []
            for symbol, pos in paper_trader.positions.items():
                positions.append({
                    'symbol': symbol,
                    'side': pos['side'].upper(),
                    'size': pos['quantity'],
                    'entry_price': pos['entry_price'],
                    'unrealized_pnl': 0,  # Calcular se necessário
                    'margin': pos.get('margin_used', 0)
                })
            return positions
        
        # Modo real
        account = client.futures_account()
        positions = []
        
        for pos in account['positions']:
            position_amt = float(pos['positionAmt'])
            if position_amt != 0:
                positions.append({
                    'symbol': pos['symbol'],
                    'side': 'LONG' if position_amt > 0 else 'SHORT',
                    'size': abs(position_amt),
                    'entry_price': float(pos['entryPrice']),
                    'mark_price': float(pos['markPrice']),
                    'unrealized_pnl': float(pos['unrealizedPnl']),
                    'percentage': float(pos['percentage']),
                    'margin': float(pos['isolatedMargin'])
                })
        
        return positions
        
    except Exception as e:
        logger.error(f"Erro ao listar posições: {e}")
        return []

def cancel_all_orders(client, symbol=None):
    """Cancela todas as ordens abertas (de um símbolo específico ou todos)."""
    try:
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            logger.info("🧹 Modo Paper Trading - não há ordens reais para cancelar")
            return True
        
        if symbol:
            binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
            cancelled = client.futures_cancel_all_open_orders(symbol=binance_symbol)
            logger.info(f"🧹 Ordens canceladas para {symbol}: {len(cancelled) if cancelled else 0}")
        else:
            # Cancelar para todos os símbolos ativos
            positions = list_open_positions(client)
            total_cancelled = 0
            
            for pos in positions:
                try:
                    cancelled = client.futures_cancel_all_open_orders(symbol=pos['symbol'])
                    count = len(cancelled) if cancelled else 0
                    total_cancelled += count
                    if count > 0:
                        logger.info(f"🧹 {count} ordens canceladas para {pos['symbol']}")
                except:
                    pass
            
            logger.info(f"🧹 Total de ordens canceladas: {total_cancelled}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao cancelar ordens: {e}")
        return False

# =============================================================================
# BLOCO DE TESTE E DEMONSTRAÇÃO
# =============================================================================
if __name__ == '__main__':
    """
    Teste e demonstração do módulo orders.py
    
    ATENÇÃO: 
    - Se PAPER_TRADING_MODE = True: Executa simulação segura
    - Se PAPER_TRADING_MODE = False: Executa ordens REAIS na Binance!
    """
    
    print("="*60)
    print("🤖 TESTE DO MÓDULO ORDERS.PY")
    print("="*60)
    
    # Verificar configuração atual
    if TRADING_CONFIG['PAPER_TRADING_MODE']:
        print("✅ MODO SEGURO: Paper Trading ativado")
        print("   As ordens serão simuladas, não há risco financeiro")
    else:
        print("⚠️  MODO REAL: Trading real ativado!")
        print("   ⚠️  AS ORDENS SERÃO EXECUTADAS NA BINANCE!")
        print("   ⚠️  ISSO ENVOLVE DINHEIRO REAL!")
        
        # Confirmar se realmente quer continuar
        response = input("\n   Deseja continuar com ordens REAIS? (digite 'SIM' para confirmar): ")
        if response != 'SIM':
            print("   ❌ Teste cancelado por segurança")
            exit()
    
    print("\n📋 Configurações de teste:")
    print(f"   💰 Valor por trade: ${TRADING_CONFIG['TRADE_VALUE_USD']}")
    print(f"   📈 Alavancagem: {TRADING_CONFIG['LEVERAGE_LEVEL']}x")
    print(f"   ⛔ Stop Loss: {TRADING_CONFIG['STOP_LOSS_PCT']}%")
    
    # Criar cliente mockado ou real
    if TRADING_CONFIG['PAPER_TRADING_MODE']:
        print("\n🎭 Criando cliente simulado...")
        
        class MockClient:
            """Cliente simulado para testes seguros."""
            def futures_ticker(self, symbol): 
                return {'lastPrice': '50000.0'}
            
            def futures_create_order(self, symbol, side, type, quantity, **kwargs): 
                price = 50050.0 if side == SIDE_BUY else 49950.0
                print(f"   📋 ORDEM SIMULADA: {side} {type} {quantity:.8f} @ ${price:.2f}")
                return {'fills': [{'price': str(price)}], 'orderId': 12345}
            
            def futures_account(self): 
                return {
                    'positions': [
                        {'symbol': 'BTCUSDT', 'positionAmt': '0.001', 'entryPrice': '49500.0',
                         'markPrice': '50000.0', 'unrealizedPnl': '5.0', 'percentage': '1.0',
                         'isolatedMargin': '100.0'}
                    ],
                    'availableBalance': '1000.0',
                    'totalWalletBalance': '1000.0'
                }
            
            def futures_cancel_all_open_orders(self, symbol): 
                print(f"   🧹 SIMULADO: Cancelar ordens para {symbol}")
                return []
            
            def futures_exchange_info(self):
                return {
                    'symbols': [
                        {
                            'symbol': 'BTCUSDT',
                            'filters': [
                                {'filterType': 'LOT_SIZE', 'stepSize': '0.00001000'}
                            ]
                        }
                    ]
                }
        
        client = MockClient()
    else:
        print("\n🔗 Conectando à Binance (API REAL)...")
        try:
            from src.keys import BINANCE_API, SECRET_API
            from binance.client import Client
            client = Client(BINANCE_API, SECRET_API)
            
            # Teste básico de conexão
            balance_check = check_account_balance(client)
            if not balance_check:
                print("❌ Falha na verificação de saldo - teste cancelado")
                exit()
                
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            exit()
    
    print("\n🚀 Iniciando testes...")
    
    try:
        # Teste 1: Verificar saldo
        print("\n" + "="*40)
        print("📊 TESTE 1: Verificar saldo da conta")
        print("="*40)
        check_account_balance(client)
        
        # Teste 2: Listar posições existentes
        print("\n" + "="*40)
        print("📋 TESTE 2: Listar posições abertas")
        print("="*40)
        positions = list_open_positions(client)
        if positions:
            for pos in positions:
                print(f"   📊 {pos['symbol']}: {pos['side']} {pos['size']:.8f} @ ${pos['entry_price']:.2f}")
        else:
            print("   ℹ️  Nenhuma posição aberta encontrada")
        
        # Teste 3: Abrir posição LONG (simulada ou real)
        print("\n" + "="*40)
        print("🟢 TESTE 3: Abrir posição LONG")
        print("="*40)
        long_success = open_long_position(client, 'BTCUSDT')
        print(f"   Resultado: {'✅ Sucesso' if long_success else '❌ Falha'}")
        
        if long_success:
            # Teste 4: Verificar status da posição
            print("\n" + "="*40)
            print("🔍 TESTE 4: Verificar status da posição")
            print("="*40)
            status = get_position_status(client, 'BTCUSDT')
            print(f"   Status: {status}")
            
            # Aguardar um pouco (simulado)
            import time
            print("   ⏳ Aguardando 3 segundos...")
            time.sleep(3)
            
            # Teste 5: Fechar posição
            print("\n" + "="*40)
            print("🔄 TESTE 5: Fechar posição")
            print("="*40)
            close_success = close_position(client, 'BTCUSDT')
            print(f"   Resultado: {'✅ Sucesso' if close_success else '❌ Falha'}")
        
        # Teste 6: Cancelar ordens (por segurança)
        print("\n" + "="*40)
        print("🧹 TESTE 6: Cancelar ordens abertas")
        print("="*40)
        cancel_all_orders(client, 'BTCUSDT')
        
    except Exception as e:
        print(f"\n❌ ERRO durante os testes: {e}")
        logger.error(f"Erro nos testes: {e}")
    
    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS")
    
    if TRADING_CONFIG['PAPER_TRADING_MODE']:
        print("ℹ️  Todos os testes foram simulados com segurança")
    else:
        print("⚠️  ATENÇÃO: Ordens reais foram executadas!")
        print("   Verifique sua conta na Binance para confirmar as operações")
    
    print("="*60)