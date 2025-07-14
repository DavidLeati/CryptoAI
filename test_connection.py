#!/usr/bin/env python3
# test_connection.py
# Script simples para testar a conexão com a Binance

from binance.client import Client
from keys import BINANCE_API, SECRET_API

def test_binance_connection():
    """Testa a conexão com a Binance e exibe informações da conta."""
    
    print("=== TESTE DE CONEXÃO COM A BINANCE ===\n")
    
    try:
        # Criar cliente (SEM testnet para usar API real)
        print("1. Criando conexão com a Binance...")
        client = Client(BINANCE_API, SECRET_API)
        print("✅ Cliente criado com sucesso!")
        
        # Testar informações da conta spot
        print("\n2. Testando acesso à conta spot...")
        account_info = client.get_account()
        print(f"✅ Acesso à conta spot: OK")
        print(f"   - Pode negociar: {account_info['canTrade']}")
        print(f"   - Pode sacar: {account_info['canWithdraw']}")
        print(f"   - Pode depositar: {account_info['canDeposit']}")
        
        # Testar informações da conta de futuros
        print("\n3. Testando acesso à conta de futuros...")
        futures_account = client.futures_account()
        print(f"✅ Acesso à conta de futuros: OK")
        print(f"   - Saldo total: {futures_account['totalWalletBalance']} USDT")
        print(f"   - Margem disponível: {futures_account['availableBalance']} USDT")
        
        # Testar acesso a dados de mercado
        print("\n4. Testando acesso a dados de mercado...")
        ticker = client.futures_ticker(symbol='BTCUSDT')
        print(f"✅ Dados de mercado: OK")
        print(f"   - Preço atual BTC: ${float(ticker['lastPrice']):.2f}")
        
        # Testar informações de posições
        print("\n5. Testando acesso a posições...")
        positions = client.futures_position_information()
        active_positions = [p for p in positions if float(p['positionAmt']) != 0]
        print(f"✅ Informações de posições: OK")
        print(f"   - Total de símbolos disponíveis: {len(positions)}")
        print(f"   - Posições ativas: {len(active_positions)}")
        
        if active_positions:
            print("   - Posições abertas:")
            for pos in active_positions:
                side = "LONG" if float(pos['positionAmt']) > 0 else "SHORT"
                print(f"     * {pos['symbol']}: {side} {abs(float(pos['positionAmt']))}")
        
        print(f"\n🎉 SUCESSO! Todas as conexões estão funcionando corretamente!")
        print(f"✅ Suas credenciais da API estão válidas e têm as permissões necessárias.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print(f"\n🔧 DIAGNÓSTICO:")
        
        error_str = str(e)
        if "Invalid API-key" in error_str:
            print("• Problema: Chave da API inválida")
            print("• Solução: Verifique se BINANCE_API está correta no arquivo keys.py")
        elif "Signature" in error_str:
            print("• Problema: Chave secreta inválida")  
            print("• Solução: Verifique se SECRET_API está correta no arquivo keys.py")
        elif "IP" in error_str:
            print("• Problema: Restrição de IP")
            print("• Solução: Remova as restrições de IP na sua API key ou adicione seu IP atual")
        elif "permissions" in error_str:
            print("• Problema: Permissões insuficientes")
            print("• Solução: Ative 'Enable Futures' na configuração da sua API key")
        else:
            print("• Problema: Erro desconhecido")
            print("• Solução: Verifique sua conexão com a internet e tente novamente")
            
        print(f"\n📋 CHECKLIST PARA RESOLVER:")
        print(f"1. Acesse: https://www.binance.com/en/my/settings/api-management")
        print(f"2. Verifique se sua API key está ativa")
        print(f"3. Certifique-se de que 'Enable Futures' está marcado")
        print(f"4. Remova todas as restrições de IP (ou adicione seu IP atual)")
        print(f"5. Confirme que as chaves no arquivo keys.py estão corretas")
        
        return False

if __name__ == "__main__":
    test_binance_connection()
