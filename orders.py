# orders.py
# Módulo acessório responsável pela execução de ordens e gerenciamento de posições.

import ccxt

# =============================================================================
# 1. PARÂMETROS DE EXECUÇÃO
#    Valores padrão para as funções de ordem.
# =============================================================================
DEFAULT_TRADE_VALUE_USD = 10.00  # Valor padrão em USD para cada operação (ex: $10)
DEFAULT_STOP_LOSS_PCT = 1.5      # Stop-loss padrão de 1.5% abaixo/acima do preço de entrada

# =============================================================================
# 2. FUNÇÕES DE EXECUÇÃO DE ORDENS
# =============================================================================

def open_long_position(exchange, symbol, trade_value_usd=DEFAULT_TRADE_VALUE_USD, stop_loss_pct=DEFAULT_STOP_LOSS_PCT):
    """
    Abre uma posição de COMPRA (LONG) e imediatamente cria uma ordem stop-loss.

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.
    """
    try:
        print(f"\n>>> Iniciando abertura de posição LONG para {symbol}...")
        
        # 1. Obter o preço atual para calcular a quantidade
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        if not current_price:
            print(f"Erro: Não foi possível obter o preço atual de {symbol}.")
            return False
            
        # 2. Calcular a quantidade do ativo a ser comprada
        amount = trade_value_usd / current_price
        print(f"Preço atual: ${current_price:.2f}. Calculando quantidade para ${trade_value_usd:.2f} -> {amount:.8f} {symbol.split('/')[0]}")

        # 3. Criar a ordem de compra a mercado
        print("Enviando ordem de COMPRA a mercado...")
        # NOTA: O 'reduceOnly' é FALSO para abrir uma nova posição
        # NOTA: O 'type' é 'market' para execução imediata
        order_buy = exchange.create_market_buy_order(symbol, amount)
        entry_price = float(order_buy['price']) # Preço real de execução
        print(f"Ordem de COMPRA executada a um preço médio de ${entry_price:.2f}")

        # 4. Calcular e criar a ordem de STOP-LOSS
        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
        print(f"Calculando preço do Stop-Loss ({stop_loss_pct}%) -> ${stop_loss_price:.2f}")
        
        # O stop-loss para um LONG é uma ordem de VENDA do tipo STOP_MARKET
        # NOTA: O 'reduceOnly' é VERDADEIRO para garantir que esta ordem apenas feche a posição
        params = {'stopPrice': stop_loss_price, 'reduceOnly': True}
        stop_loss_order = exchange.create_order(symbol, 'STOP_MARKET', 'sell', amount, params=params)
        print("Ordem de Stop-Loss de VENDA criada com sucesso.")
        
        return True

    except Exception as e:
        print(f"ERRO ao abrir posição LONG para {symbol}: {e}")
        return False

def open_short_position(exchange, symbol, trade_value_usd=DEFAULT_TRADE_VALUE_USD, stop_loss_pct=DEFAULT_STOP_LOSS_PCT):
    """
    Abre uma posição de VENDA (SHORT) e imediatamente cria uma ordem stop-loss.
    
    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.
    """
    try:
        print(f"\n>>> Iniciando abertura de posição SHORT para {symbol}...")
        
        # 1. Obter o preço atual e 2. Calcular a quantidade (mesmo processo do LONG)
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        amount = trade_value_usd / current_price
        print(f"Preço atual: ${current_price:.2f}. Calculando quantidade para ${trade_value_usd:.2f} -> {amount:.8f} {symbol.split('/')[0]}")

        # 3. Criar a ordem de venda a mercado para ABRIR a posição
        print("Enviando ordem de VENDA a mercado...")
        order_sell = exchange.create_market_sell_order(symbol, amount)
        entry_price = float(order_sell['price'])
        print(f"Ordem de VENDA executada a um preço médio de ${entry_price:.2f}")

        # 4. Calcular e criar a ordem de STOP-LOSS
        stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
        print(f"Calculando preço do Stop-Loss ({stop_loss_pct}%) -> ${stop_loss_price:.2f}")
        
        # O stop-loss para um SHORT é uma ordem de COMPRA do tipo STOP_MARKET
        params = {'stopPrice': stop_loss_price, 'reduceOnly': True}
        stop_loss_order = exchange.create_order(symbol, 'STOP_MARKET', 'buy', amount, params=params)
        print("Ordem de Stop-Loss de COMPRA criada com sucesso.")
        
        return True
        
    except Exception as e:
        print(f"ERRO ao abrir posição SHORT para {symbol}: {e}")
        return False

def close_position(exchange, symbol):
    """
    Fecha qualquer posição aberta para um determinado símbolo e cancela ordens associadas.
    """
    try:
        print(f"\n>>> Tentando fechar qualquer posição aberta para {symbol}...")
        
        # 1. Verifica se existe uma posição aberta
        positions = exchange.fetch_positions([symbol])
        position = next((p for p in positions if p['symbol'] == symbol and float(p['contracts']) != 0), None)

        if not position:
            print(f"Nenhuma posição aberta encontrada para {symbol}.")
            # Ainda assim, vamos cancelar ordens abertas por segurança
            exchange.cancel_all_orders(symbol)
            print(f"Ordens abertas para {symbol} canceladas (por segurança).")
            return True

        # 2. Determina o lado e a quantidade da posição
        side = 'long' if float(position['info']['positionAmt']) > 0 else 'short'
        amount = float(position['contracts'])
        print(f"Posição encontrada: {side} de {amount} {symbol.split('/')[0]}")

        # 3. Cria a ordem de fechamento a mercado
        if side == 'long':
            exchange.create_market_sell_order(symbol, amount, {'reduceOnly': True})
            print("Ordem de VENDA a mercado para fechar a posição enviada.")
        else: # short
            exchange.create_market_buy_order(symbol, amount, {'reduceOnly': True})
            print("Ordem de COMPRA a mercado para fechar a posição enviada.")

        # 4. Cancela TODAS as outras ordens abertas para o símbolo (ex: o stop-loss que não foi ativado)
        exchange.cancel_all_orders(symbol)
        print(f"Todas as ordens abertas remanescentes para {symbol} foram canceladas.")
        
        return True

    except Exception as e:
        print(f"ERRO ao fechar posição para {symbol}: {e}")
        return False

# =============================================================================
# 3. BLOCO DE TESTE
#    ATENÇÃO: Este teste é um "dry run". Ele não executa ordens reais,
#    apenas demonstra a lógica que SERIA executada.
# =============================================================================
if __name__ == '__main__':
    print("--- Testando o módulo orders.py (em modo 'dry run') ---")
    print("ATENÇÃO: Nenhuma ordem real será enviada.")

    class MockExchange:
        """Classe falsa para simular a exchange sem enviar ordens reais."""
        def fetch_ticker(self, symbol): return {'last': 50000.0}
        def create_market_buy_order(self, symbol, amount, params=None): return {'price': 50050.0}
        def create_market_sell_order(self, symbol, amount, params=None): return {'price': 49950.0}
        def create_order(self, symbol, type, side, amount, params): print(f"ORDEM SIMULADA: {side} {type} {amount:.8f} @ {params['stopPrice']:.2f}"); return {}
        def fetch_positions(self, symbols): return [{'symbol': 'BTC/USDT', 'info': {'positionAmt': '0.001'}, 'contracts': '0.001'}]
        def cancel_all_orders(self, symbol): print(f"ORDEM SIMULADA: Cancelar todas as ordens para {symbol}")

    mock_exchange = MockExchange()

    # Teste 1: Abrir LONG
    open_long_position(mock_exchange, 'BTC/USDT')

    # Teste 2: Abrir SHORT
    open_short_position(mock_exchange, 'BTC/USDT')

    # Teste 3: Fechar Posição
    close_position(mock_exchange, 'BTC/USDT')
    
    print("\n--- Fim do teste ---")