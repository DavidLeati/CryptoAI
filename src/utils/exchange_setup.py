# exchange_setup.py
# Arquivo principal do robô. Responsável por inicializar a conexão,
# configurar parâmetros e executar o loop de trading principal.

from binance.client import Client
from binance.enums import *
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
        # Conectando ao Binance Futures usando a biblioteca python-binance
        # MUDANÇA: Removido testnet=True para usar a API real
        client = Client(BINANCE_API, SECRET_API)
        print("Conexão principal estabelecida com sucesso (API REAL).")
        return client
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível criar a conexão com a exchange: {e}")
        return None

def setup_leverage_for_symbol(client, symbol, leverage, margin_type='ISOLATED'):
    """Define a alavancagem para um símbolo."""
    try:
        # Remove /USDT:USDT do símbolo para o formato da Binance
        binance_symbol = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
        
        # Tentar configurar alavancagem
        try:
            client.futures_change_leverage(symbol=binance_symbol, leverage=leverage)
            print(f"  ✅ Alavancagem {leverage}x configurada para {binance_symbol}")
        except Exception as leverage_error:
            error_str = str(leverage_error)
            if "leverage not modified" in error_str:
                print(f"  ℹ️  Alavancagem já está em {leverage}x para {binance_symbol}")
            else:
                print(f"  ⚠️  {binance_symbol}: {leverage_error}")
        
        return True
    except Exception as e:
        print(f"  ❌ ERRO {symbol}: {e}")
        return True  # Continua mesmo com erro

def test_api_connection(client):
    """Testa a conexão e permissões da API."""
    try:
        print("Testando conexão e permissões da API...")
        
        # Testar acesso à conta de futuros
        account_info = client.futures_account()
        print("✅ Conexão com Binance Futures estabelecida com sucesso!")
        print(f"Saldo total da carteira: {account_info['totalWalletBalance']} USDT")
        
        # Testar se pode acessar informações de posições
        positions = client.futures_position_information()
        print(f"✅ Acesso a {len(positions)} símbolos de futuros confirmado!")
        
        return True
    except Exception as e:
        print(f"❌ ERRO ao testar conexão: {e}")
        print("\nPossíveis soluções:")
        print("1. Verifique se suas API keys estão corretas")
        print("2. Certifique-se de que 'Enable Futures' está ativado na sua API key")
        print("3. Verifique se não há restrições de IP")
        print("4. Confirme que você tem saldo em USDT na conta de futuros")
        return False

def check_account_mode(client):
    """Verifica e informa sobre o modo da conta (Multi-Assets vs Single-Asset)."""
    try:
        # Tentar alterar o tipo de margem de um símbolo popular para detectar o modo
        test_symbol = 'BTCUSDT'
        try:
            client.futures_change_margin_type(symbol=test_symbol, marginType='ISOLATED')
            print("ℹ️  Conta em modo Single-Asset (configuração de margem disponível)")
            return "single-asset"
        except Exception as e:
            if "Multi-Assets mode" in str(e):
                print("ℹ️  Conta em modo Multi-Assets detectada")
                print("   📋 No modo Multi-Assets:")
                print("   • Todas as posições compartilham a margem")
                print("   • Não é possível alterar entre ISOLATED/CROSS para símbolos individuais")
                print("   • A alavancagem ainda pode ser configurada normalmente")
                print("   • O bot funcionará perfeitamente com essas configurações\n")
                return "multi-assets"
            else:
                print(f"⚠️  Erro ao detectar modo da conta: {e}")
                return "unknown"
    except Exception as e:
        print(f"⚠️  Não foi possível verificar o modo da conta: {e}")
        return "unknown"

