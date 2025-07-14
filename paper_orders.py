# paper_orders.py
# Versões simuladas das funções de ordem para paper trading

from paper_trading import paper_trader

# Parâmetros padrão (mesmos do orders.py)
DEFAULT_TRADE_VALUE_USD = 10.00
DEFAULT_STOP_LOSS_PCT = 1.5

def paper_open_long_position(client, symbol, trade_value_usd=DEFAULT_TRADE_VALUE_USD, stop_loss_pct=DEFAULT_STOP_LOSS_PCT):
    """Simula abertura de posição LONG."""
    try:
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
            leverage=25  # Usar alavancagem do sistema
        )
        
        if success:
            print(f"✅ [SIMULAÇÃO] Posição LONG simulada criada para {symbol}")
            print(f"   📝 Stop-loss seria configurado em: ${current_price * (1 - stop_loss_pct / 100):.4f}")
        
        return success
        
    except Exception as e:
        print(f"❌ [SIMULAÇÃO] Erro ao simular posição LONG para {symbol}: {e}")
        return False

def paper_open_short_position(client, symbol, trade_value_usd=DEFAULT_TRADE_VALUE_USD, stop_loss_pct=DEFAULT_STOP_LOSS_PCT):
    """Simula abertura de posição SHORT."""
    try:
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
            leverage=25  # Usar alavancagem do sistema
        )
        
        if success:
            print(f"✅ [SIMULAÇÃO] Posição SHORT simulada criada para {symbol}")
            print(f"   📝 Stop-loss seria configurado em: ${current_price * (1 + stop_loss_pct / 100):.4f}")
        
        return success
        
    except Exception as e:
        print(f"❌ [SIMULAÇÃO] Erro ao simular posição SHORT para {symbol}: {e}")
        return False

def paper_close_position(client, symbol):
    """Simula fechamento de posição."""
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

def paper_save_results():
    """Salva resultados da simulação."""
    paper_trader.save_results()
