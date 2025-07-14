#!/usr/bin/env python3
# run.py
# Ponto de entrada principal para o CryptoAI Trading Bot

import sys
import os
import argparse
from pathlib import Path

# Adicionar src ao Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Imports
try:
    from config.settings import get_config, validate_config, VERSION, APP_NAME
    from core.main import main as run_core_bot
    from web.web_interface import app, socketio
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("💡 Certifique-se de que todas as dependências estão instaladas")
    sys.exit(1)

def print_banner():
    """Exibe o banner do sistema."""
    banner = f"""
══════════════════════════════════════════════════════════════
                                                              
   {APP_NAME:<50}                                             
   Versão: {VERSION:<47}                                      
   Desenvolvido por: David Leati                              
                                                              
   Sistema de Trading Automatizado com IA                     
   Suporte a 65+ Criptomoedas                                 
   Paper Trading + Trading Real                               
   Interface Web em Tempo Real                                
                                                              
══════════════════════════════════════════════════════════════
"""
    print(banner)

def validate_system():
    """Valida as configurações do sistema."""
    print("🔍 Validando configurações do sistema...")
    
    errors = validate_config()
    if errors:
        print("❌ Erros encontrados nas configurações:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    # Verificar se os diretórios necessários existem
    required_dirs = ['data', 'logs', 'src']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"📁 Criando diretório: {dir_name}")
            os.makedirs(dir_name, exist_ok=True)
    
    print("✅ Sistema validado com sucesso!")
    return True

def run_bot():
    """Executa o bot principal de trading."""
    print("🤖 Iniciando bot de trading...")
    try:
        run_core_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar bot: {e}")
        sys.exit(1)

def run_web():
    """Executa a interface web."""
    print("🌐 Iniciando interface web...")
    print("📊 Dashboard: http://localhost:5000")
    print("🔧 Configurações: http://localhost:5000/settings")
    print("📈 Trading: http://localhost:5000/trading")
    print("📊 Analytics: http://localhost:5000/analytics")
    print("\n💡 Pressione Ctrl+C para parar o servidor")
    
    try:
        config = get_config()
        web_config = config['web']
        socketio.run(
            app, 
            debug=web_config['debug'], 
            host=web_config['host'], 
            port=web_config['port'],
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Interface web interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar interface web: {e}")
        sys.exit(1)

def show_status():
    """Mostra o status atual do sistema."""
    print("📊 Status do Sistema:")
    print("=" * 50)
    
    config = get_config()
    
    print(f"🔧 Modo: {'Paper Trading (Simulação)' if config['general']['paper_trading_mode'] else 'Trading Real'}")
    print(f"💰 Valor por Trade: ${config['trading']['trade_value_usd']}")
    print(f"📈 Stop Loss: {config['trading']['stop_loss_pct']}%")
    print(f"📊 Take Profit: {config['trading']['take_profit_pct']}%")
    print(f"🎯 Ativos Monitorados: {config['assets']['total_assets']}")
    print(f"⚙️  Timeframe Principal: {config['timeframes']['primary']}")
    
    # Verificar se há resultados salvos
    results_file = config.get('data', {}).get('trading_results_file', 'data/paper_trading_results.json')
    if os.path.exists(results_file):
        print(f"💾 Arquivo de Resultados: Encontrado")
    else:
        print(f"💾 Arquivo de Resultados: Não encontrado")
    
    print("=" * 50)

def main():
    """Função principal do sistema."""
    parser = argparse.ArgumentParser(
        description=f'{APP_NAME} v{VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run.py bot          # Executa o bot de trading
  python run.py web          # Executa a interface web
  python run.py status       # Mostra status do sistema
  python run.py --help       # Mostra esta ajuda
        """
    )
    
    parser.add_argument(
        'command', 
        choices=['bot', 'web', 'status'], 
        help='Comando a executar'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'{APP_NAME} v{VERSION}'
    )
    
    # Se nenhum argumento foi fornecido, mostrar ajuda
    if len(sys.argv) == 1:
        print_banner()
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Sempre mostrar banner
    print_banner()
    
    # Validar sistema antes de executar qualquer comando
    if not validate_system():
        sys.exit(1)
    
    # Executar comando solicitado
    if args.command == 'bot':
        run_bot()
    elif args.command == 'web':
        run_web()
    elif args.command == 'status':
        show_status()

if __name__ == '__main__':
    main()
