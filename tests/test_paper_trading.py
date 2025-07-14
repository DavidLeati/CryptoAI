#!/usr/bin/env python3
# test_paper_trading.py
# Teste rápido das funcionalidades integradas do paper trading

import sys
from pathlib import Path

# Adicionar src ao Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

try:
    from trading.paper_trading import (
        paper_trader,
        paper_open_long_position,
        paper_open_short_position,
        paper_close_position,
        paper_save_results,
        paper_get_position_status
    )
    
    print("🧪 TESTE DO PAPER TRADING INTEGRADO")
    print("=" * 50)
    
    # Teste 1: Abrir posição LONG
    print("\n1️⃣ Testando abertura de posição LONG...")
    success = paper_open_long_position("BTCUSDT", 50000.0, 50.0, 1)
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")
    
    # Teste 2: Verificar status
    print("\n2️⃣ Testando status da posição...")
    status = paper_get_position_status("BTCUSDT")
    print(f"Status: {status}")
    
    # Teste 3: Abrir posição SHORT
    print("\n3️⃣ Testando abertura de posição SHORT...")
    success = paper_open_short_position("ETHUSDT", 3000.0, 30.0, 1)
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")
    
    # Teste 4: Fechar posição LONG
    print("\n4️⃣ Testando fechamento de posição LONG...")
    success = paper_close_position("BTCUSDT", 51000.0)  # Preço maior = lucro
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")
    
    # Teste 5: Salvar resultados
    print("\n5️⃣ Testando salvamento de resultados...")
    paper_save_results()
    print("✅ Resultados salvos")
    
    # Teste 6: Mostrar saldo final
    print(f"\n💰 Saldo final: ${paper_trader.current_balance:.2f}")
    print(f"📊 Total de trades: {paper_trader.total_trades}")
    
    print("\n🎉 Todos os testes concluídos!")
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
except Exception as e:
    print(f"❌ Erro durante teste: {e}")
