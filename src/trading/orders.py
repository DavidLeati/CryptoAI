# orders.py
# Módulo acessório responsável pela execução de ordens e gerenciamento de posições.

from binance.client import Client
from binance.enums import *

# =============================================================================
# 1. PARÂMETROS DE EXECUÇÃO
#    Valores padrão para as funções de ordem.
# =============================================================================
DEFAULT_TRADE_VALUE_USD = 10.00  # Valor padrão em USD para cada operação (ex: $10)
DEFAULT_STOP_LOSS_PCT = 1.5      # Stop-loss padrão de 1.5% abaixo/acima do preço de entrada

# =============================================================================
# 2. FUNÇÕES DE EXECUÇÃO DE ORDENS
# =============================================================================

def open_long_position(client, symbol, trade_value_usd=DEFAULT_TRADE_VALUE_USD, stop_loss_pct=DEFAULT_STOP_LOSS_PCT):
    """
    Abre uma posição de COMPRA (LONG) e imediatamente cria uma ordem stop-loss.

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.
    """
    try:
        print(f"\n>>> Iniciando abertura de posição LONG para {symbol}...")
        
        # Converter símbolo para formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # 1. Obter o preço atual para calcular a quantidade
        ticker = client.futures_ticker(symbol=binance_symbol)
        current_price = float(ticker['lastPrice'])
        if not current_price:
            print(f"Erro: Não foi possível obter o preço atual de {symbol}.")
            return False
            
        # 2. Calcular a quantidade do ativo a ser comprada
        amount = trade_value_usd / current_price
        print(f"Preço atual: ${current_price:.2f}. Calculando quantidade para ${trade_value_usd:.2f} -> {amount:.8f} {symbol.split('/')[0]}")

        # 3. Criar a ordem de compra a mercado
        print("Enviando ordem de COMPRA a mercado...")
        order_buy = client.futures_create_order(
            symbol=binance_symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=amount
        )
        entry_price = float(order_buy['fills'][0]['price']) if order_buy['fills'] else current_price
        print(f"Ordem de COMPRA executada a um preço médio de ${entry_price:.2f}")

        # 4. Calcular e criar a ordem de STOP-LOSS
        stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
        print(f"Calculando preço do Stop-Loss ({stop_loss_pct}%) -> ${stop_loss_price:.2f}")
        
        # O stop-loss para um LONG é uma ordem de VENDA do tipo STOP_MARKET
        stop_loss_order = client.futures_create_order(
            symbol=binance_symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,
            quantity=amount,
            stopPrice=stop_loss_price,
            reduceOnly=True
        )
        print("Ordem de Stop-Loss de VENDA criada com sucesso.")
        
        return True

    except Exception as e:
        print(f"ERRO ao abrir posição LONG para {symbol}: {e}")
        return False

def open_short_position(client, symbol, trade_value_usd=DEFAULT_TRADE_VALUE_USD, stop_loss_pct=DEFAULT_STOP_LOSS_PCT):
    """
    Abre uma posição de VENDA (SHORT) e imediatamente cria uma ordem stop-loss.
    
    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.
    """
    try:
        print(f"\n>>> Iniciando abertura de posição SHORT para {symbol}...")
        
        # Converter símbolo para formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # 1. Obter o preço atual e 2. Calcular a quantidade (mesmo processo do LONG)
        ticker = client.futures_ticker(symbol=binance_symbol)
        current_price = float(ticker['lastPrice'])
        amount = trade_value_usd / current_price
        print(f"Preço atual: ${current_price:.2f}. Calculando quantidade para ${trade_value_usd:.2f} -> {amount:.8f} {symbol.split('/')[0]}")

        # 3. Criar a ordem de venda a mercado para ABRIR a posição
        print("Enviando ordem de VENDA a mercado...")
        order_sell = client.futures_create_order(
            symbol=binance_symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=amount
        )
        entry_price = float(order_sell['fills'][0]['price']) if order_sell['fills'] else current_price
        print(f"Ordem de VENDA executada a um preço médio de ${entry_price:.2f}")

        # 4. Calcular e criar a ordem de STOP-LOSS
        stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
        print(f"Calculando preço do Stop-Loss ({stop_loss_pct}%) -> ${stop_loss_price:.2f}")
        
        # O stop-loss para um SHORT é uma ordem de COMPRA do tipo STOP_MARKET
        stop_loss_order = client.futures_create_order(
            symbol=binance_symbol,
            side=SIDE_BUY,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,
            quantity=amount,
            stopPrice=stop_loss_price,
            reduceOnly=True
        )
        print("Ordem de Stop-Loss de COMPRA criada com sucesso.")
        
        return True
        
    except Exception as e:
        print(f"ERRO ao abrir posição SHORT para {symbol}: {e}")
        return False

def close_position(client, symbol):
    """
    Fecha qualquer posição aberta para um determinado símbolo e cancela ordens associadas.
    """
    try:
        print(f"\n>>> Tentando fechar qualquer posição aberta para {symbol}...")
        
        # Converter símbolo para formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # 1. Verifica se existe uma posição aberta
        account = client.futures_account()
        positions = account['positions']
        position = next((p for p in positions if p['symbol'] == binance_symbol and float(p['positionAmt']) != 0), None)

        if not position:
            print(f"Nenhuma posição aberta encontrada para {symbol}.")
            # Ainda assim, vamos cancelar ordens abertas por segurança
            client.futures_cancel_all_open_orders(symbol=binance_symbol)
            print(f"Ordens abertas para {symbol} canceladas (por segurança).")
            return True

        # 2. Determina o lado e a quantidade da posição
        position_amt = float(position['positionAmt'])
        side = 'long' if position_amt > 0 else 'short'
        amount = abs(position_amt)
        print(f"Posição encontrada: {side} de {amount} {symbol.split('/')[0]}")

        # 3. Cria a ordem de fechamento a mercado
        if side == 'long':
            client.futures_create_order(
                symbol=binance_symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=amount,
                reduceOnly=True
            )
            print("Ordem de VENDA a mercado para fechar a posição enviada.")
        else: # short
            client.futures_create_order(
                symbol=binance_symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=amount,
                reduceOnly=True
            )
            print("Ordem de COMPRA a mercado para fechar a posição enviada.")

        # 4. Cancela TODAS as outras ordens abertas para o símbolo (ex: o stop-loss que não foi ativado)
        client.futures_cancel_all_open_orders(symbol=binance_symbol)
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

    class MockClient:
        """Classe falsa para simular a client da Binance sem enviar ordens reais."""
        def futures_ticker(self, symbol): 
            return {'lastPrice': '50000.0'}
        
        def futures_create_order(self, symbol, side, type, quantity, **kwargs): 
            price = 50050.0 if side == SIDE_BUY else 49950.0
            print(f"ORDEM SIMULADA: {side} {type} {quantity:.8f} @ ${price:.2f}")
            return {'fills': [{'price': str(price)}]}
        
        def futures_account(self): 
            return {
                'positions': [
                    {'symbol': 'BTCUSDT', 'positionAmt': '0.001'}
                ]
            }
        
        def futures_cancel_all_open_orders(self, symbol): 
            print(f"ORDEM SIMULADA: Cancelar todas as ordens para {symbol}")

    mock_client = MockClient()

    # Teste 1: Abrir LONG
    open_long_position(mock_client, 'BTC/USDT:USDT')

    # Teste 2: Abrir SHORT
    open_short_position(mock_client, 'BTC/USDT:USDT')

    # Teste 3: Fechar Posição
    close_position(mock_client, 'BTC/USDT:USDT')
    
    print("\n--- Fim do teste ---")