#!/usr/bin/env python3
# test_signatures.py
# Teste das assinaturas de compatibilidade do paper trading

import sys
from pathlib import Path

# Adicionar src ao Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

class MockClient:
    """Cliente mock para testar."""
    def futures_ticker(self, symbol):
        return {'lastPrice': '50000.0'}

try:
    from trading.paper_trading import (
        paper_open_long_position,
        paper_open_short_position,
        paper_close_position,
    )
    
    print("🧪 TESTE DAS ASSINATURAS DE COMPATIBILIDADE")
    print("=" * 60)
    
    # Teste 1: Assinatura nova (symbol, current_price, trade_value_usd, leverage)
    print("\n1️⃣ Testando assinatura NOVA...")
    success = paper_open_long_position("BTCUSDT", 50000.0, 50.0, 1)
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")
    
    # Teste 2: Assinatura antiga (client, symbol, trade_value_usd, stop_loss_pct) 
    print("\n2️⃣ Testando assinatura ANTIGA...")
    client = MockClient()
    success = paper_open_long_position(client, "ETHUSDT", 30.0, 2.0)
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")
    
    # Teste 3: Fechar com assinatura nova
    print("\n3️⃣ Testando fechamento com assinatura NOVA...")
    success = paper_close_position("BTCUSDT", 51000.0)
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")
    
    # Teste 4: Fechar com assinatura antiga
    print("\n4️⃣ Testando fechamento com assinatura ANTIGA...")
    success = paper_close_position(client, "ETHUSDT")
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")
    
    print("\n🎉 Todos os testes de compatibilidade concluídos!")
    
except Exception as e:
    print(f"❌ Erro durante teste: {e}")
    import traceback
    traceback.print_exc()
