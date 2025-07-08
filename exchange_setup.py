# exchange_setup.py
# Arquivo principal do robô. Responsável por inicializar a conexão,
# configurar parâmetros e executar o loop de trading principal.

import ccxt
import time
import os

import data 
from keys import BINANCE_API, SECRET_API

# =============================================================================
# FUNÇÕES DE CONFIGURAÇÃO
# =============================================================================

def create_exchange_connection():
    """Cria e retorna o objeto de conexão da exchange centralizado."""
    print("Inicializando a conexão principal com a exchange...")
    try:
        exchange = ccxt.binance({
            'apiKey': BINANCE_API,
            'secret': SECRET_API,
            'options': {
                'defaultType': 'future',
            },
        })
        # Para usar a Testnet
        exchange.set_sandbox_mode(True)
        print("Conexão principal estabelecida com sucesso.")
        return exchange
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível criar a conexão com a exchange: {e}")
        return None

def setup_leverage_for_symbol(exchange, symbol, leverage, margin_type='ISOLATED'):
    """Define a alavancagem e o tipo de margem para um símbolo."""
    try:
        print(f"Configurando {symbol} para alavancagem de {leverage}x e margem {margin_type}...")
        exchange.set_margin_mode(margin_type, symbol)
        exchange.set_leverage(leverage, symbol)
        print(f"Configuração para {symbol} concluída.")
        return True
    except Exception as e:
        print(f"ERRO ao configurar alavancagem para {symbol}: {e}")
        return False

