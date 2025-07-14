# web_interface.py
# Interface web Flask para monitoramento e controle do bot de trading em tempo real

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
import signal

# Adicionar src ao path se necessário
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar módulos do bot
from src.trading.paper_trading import paper_trader
from src.core import main
from config.settings import TRADING_CONFIG, WEB_CONFIG, ASSETS_CONFIG, get_config

# Importar sistemas de utilidades
from src.utils.logger import get_logger
from src.utils.cache import cache_manager
from src.utils.risk_manager import risk_manager
from src.utils.notifications import notification_manager
from src.utils.performance import performance_monitor

app = Flask(__name__)
app.config['SECRET_KEY'] = WEB_CONFIG['SECRET_KEY']
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurar logger
logger = get_logger('web_interface')

# Estado global da aplicação
app_state = {
    'bot_running': False,
    'bot_thread': None,
    'last_update': None,
    'connection_status': 'disconnected',
    'total_symbols': len(ASSETS_CONFIG['SYMBOLS']),
    'active_positions': 0,
    'alerts': []
}

# =============================================================================
# ROTAS PRINCIPAIS
# =============================================================================

@app.route('/')
def dashboard():
    """Dashboard principal com visão geral do sistema."""
    return render_template('dashboard.html')

@app.route('/trading')
def trading_view():
    """Página de monitoramento de trading detalhado."""
    return render_template('trading.html')

@app.route('/settings')
def settings():
    """Página de configurações do bot."""
    return render_template('settings.html')

@app.route('/analytics')
def analytics():
    """Página de análises e estatísticas."""
    return render_template('analytics.html')

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/status')
def api_status():
    """Retorna o status atual do sistema."""
    try:
        # Tentar carregar resultados do paper trading
        results = load_trading_results()
        
        # Calcular estatísticas básicas
        if results:
            summary = results.get('summary', {})
            open_positions = results.get('open_positions', {})
            trade_history = results.get('trade_history', [])
            
            # Últimas 5 trades
            recent_trades = sorted(trade_history, key=lambda x: x.get('exit_time', x.get('entry_time', '')), reverse=True)[:5]
            
            # Calcular P&L das últimas 24h (simulado)
            pnl_24h = sum([trade.get('pnl_usd', 0) for trade in trade_history[-10:]])
            
            status_data = {
                'bot_running': app_state['bot_running'],
                'connection_status': app_state['connection_status'],
                'current_balance': summary.get('final_balance', 1000.0),
                'initial_balance': summary.get('initial_balance', 1000.0),
                'total_pnl': summary.get('total_pnl', 0.0),
                'roi_percent': summary.get('roi_percent', 0.0),
                'total_trades': summary.get('total_trades', 0),
                'win_rate': summary.get('win_rate', 0.0),
                'active_positions': len(open_positions),
                'open_positions': open_positions,
                'recent_trades': recent_trades,
                'pnl_24h': pnl_24h,
                'total_symbols': app_state['total_symbols'],
                'last_update': app_state['last_update'] or datetime.now().isoformat(),
                'alerts': app_state['alerts'][-10:]  # Últimos 10 alertas
            }
        else:
            # Dados padrão quando não há resultados
            status_data = {
                'bot_running': app_state['bot_running'],
                'connection_status': app_state['connection_status'],
                'current_balance': 1000.0,
                'initial_balance': 1000.0,
                'total_pnl': 0.0,
                'roi_percent': 0.0,
                'total_trades': 0,
                'win_rate': 0.0,
                'active_positions': 0,
                'open_positions': {},
                'recent_trades': [],
                'pnl_24h': 0.0,
                'total_symbols': app_state['total_symbols'],
                'last_update': datetime.now().isoformat(),
                'alerts': app_state['alerts'][-10:]
            }
        
        return jsonify(status_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading-results')
def api_trading_results():
    """Retorna resultados completos do trading."""
    try:
        results = load_trading_results()
        if results:
            return jsonify(results)
        else:
            return jsonify({
                'summary': {},
                'trade_history': [],
                'open_positions': {},
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings')
def api_get_settings():
    """Retorna as configurações atuais do bot."""
    settings = {
        'paper_trading_mode': TRADING_CONFIG['PAPER_TRADING_MODE'],
        'trade_value_usd': TRADING_CONFIG['TRADE_VALUE_USD'],
        'stop_loss_pct': TRADING_CONFIG['STOP_LOSS_PCT'],
        'take_profit_pct': TRADING_CONFIG['TAKE_PROFIT_PCT'],
        'leverage_level': TRADING_CONFIG['LEVERAGE_LEVEL'],
        'max_positions': TRADING_CONFIG['MAX_POSITIONS'],
        'daily_loss_limit': TRADING_CONFIG['DAILY_LOSS_LIMIT'],
        'total_symbols': len(ASSETS_CONFIG['SYMBOLS']),
        'active_symbols': ASSETS_CONFIG['SYMBOLS'][:10]  # Primeiros 10 para preview
    }
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """Atualiza as configurações do bot."""
    try:
        data = request.get_json()
        
        # Atualizar configurações (cuidado: bot deve estar parado)
        if not app_state['bot_running']:
            updated_fields = []
            
            if 'trade_value_usd' in data:
                TRADING_CONFIG['TRADE_VALUE_USD'] = float(data['trade_value_usd'])
                updated_fields.append(f"Trade Value ${TRADING_CONFIG['TRADE_VALUE_USD']}")
            
            if 'stop_loss_pct' in data:
                TRADING_CONFIG['STOP_LOSS_PCT'] = float(data['stop_loss_pct'])
                updated_fields.append(f"Stop Loss {TRADING_CONFIG['STOP_LOSS_PCT']}%")
            
            if 'take_profit_pct' in data:
                TRADING_CONFIG['TAKE_PROFIT_PCT'] = float(data['take_profit_pct'])
                updated_fields.append(f"Take Profit {TRADING_CONFIG['TAKE_PROFIT_PCT']}%")
            
            if 'leverage_level' in data:
                TRADING_CONFIG['LEVERAGE_LEVEL'] = int(data['leverage_level'])
                updated_fields.append(f"Alavancagem {TRADING_CONFIG['LEVERAGE_LEVEL']}x")
            
            if 'max_positions' in data:
                TRADING_CONFIG['MAX_POSITIONS'] = int(data['max_positions'])
                updated_fields.append(f"Max Positions {TRADING_CONFIG['MAX_POSITIONS']}")
            
            logger.info(f"Configurações atualizadas via web: {', '.join(updated_fields)}")
            add_alert('info', f'Configurações atualizadas: {", ".join(updated_fields)}')
            return jsonify({'success': True, 'message': 'Configurações atualizadas com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Pare o bot antes de alterar as configurações'}), 400
    
    except Exception as e:
        logger.error(f"Erro ao atualizar configurações: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def api_start_bot():
    """Inicia o bot de trading."""
    try:
        if not app_state['bot_running']:
            # Iniciar bot em thread separada
            app_state['bot_thread'] = threading.Thread(target=run_bot_background)
            app_state['bot_thread'].daemon = True
            app_state['bot_thread'].start()
            
            app_state['bot_running'] = True
            app_state['connection_status'] = 'connecting'
            
            add_alert('success', 'Bot iniciado com sucesso!')
            
            # Emitir atualização via WebSocket
            socketio.emit('bot_status_changed', {'running': True})
            
            return jsonify({'success': True, 'message': 'Bot iniciado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Bot já está rodando'}), 400
    
    except Exception as e:
        add_alert('error', f'Erro ao iniciar bot: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def api_stop_bot():
    """Para o bot de trading."""
    try:
        if app_state['bot_running']:
            app_state['bot_running'] = False
            app_state['connection_status'] = 'disconnected'
            
            # Salvar resultados finais
            if main.PAPER_TRADING_MODE:
                paper_trader.save_results()
            
            add_alert('info', 'Bot parado. Resultados salvos.')
            
            # Emitir atualização via WebSocket
            socketio.emit('bot_status_changed', {'running': False})
            
            return jsonify({'success': True, 'message': 'Bot parado com sucesso'})
        else:
            return jsonify({'success': False, 'message': 'Bot não está rodando'}), 400
    
    except Exception as e:
        add_alert('error', f'Erro ao parar bot: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================================================
# WEBSOCKET EVENTS
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Evento de conexão WebSocket."""
    print('Cliente conectado ao WebSocket')
    emit('connected', {'data': 'Conectado ao sistema de trading'})

@socketio.on('disconnect')
def handle_disconnect():
    """Evento de desconexão WebSocket."""
    print('Cliente desconectado do WebSocket')

@socketio.on('request_update')
def handle_request_update():
    """Cliente solicita atualização de dados."""
    try:
        results = load_trading_results()
        if results:
            emit('trading_update', results)
    except Exception as e:
        emit('error', {'message': str(e)})

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def load_trading_results():
    """Carrega os resultados do paper trading do arquivo JSON."""
    try:
        # Usar caminho do diretório de dados configurado
        from config.settings import LOGGING_CONFIG
        data_dir = LOGGING_CONFIG['DATA_DIR']
        results_file = os.path.join(data_dir, 'paper_trading_results.json')
        
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar resultados: {e}")
        return None

def add_alert(type_alert, message):
    """Adiciona um alerta ao sistema."""
    alert = {
        'type': type_alert,  # success, info, warning, error
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    app_state['alerts'].append(alert)
    
    # Log do alerta
    if type_alert == 'error':
        logger.error(f"Alert: {message}")
    elif type_alert == 'warning':
        logger.warning(f"Alert: {message}")
    else:
        logger.info(f"Alert: {message}")
    
    # Manter apenas os últimos 50 alertas
    if len(app_state['alerts']) > 50:
        app_state['alerts'] = app_state['alerts'][-50:]
    
    # Emitir alerta via WebSocket
    socketio.emit('new_alert', alert)

def run_bot_background():
    """Executa o bot principal em background."""
    try:
        app_state['connection_status'] = 'connected'
        add_alert('success', 'Bot conectado e operacional!')
        logger.info("Bot iniciado em background via interface web")
        
        # Simular execução do bot (substituir pela lógica real)
        # main.main()  # Descomentado quando integrar completamente
        
        # Por enquanto, simular com updates periódicos
        while app_state['bot_running']:
            time.sleep(10)  # Update a cada 10 segundos
            app_state['last_update'] = datetime.now().isoformat()
            
            # Emitir atualização via WebSocket
            try:
                results = load_trading_results()
                if results:
                    socketio.emit('trading_update', results)
            except Exception as e:
                logger.error(f"Erro ao carregar resultados para WebSocket: {e}")
    
    except Exception as e:
        app_state['bot_running'] = False
        app_state['connection_status'] = 'error'
        logger.error(f"Erro no bot background: {e}")
        add_alert('error', f'Erro no bot: {str(e)}')

def monitor_trading_results():
    """Monitor que verifica mudanças nos resultados e atualiza via WebSocket."""
    last_modified = None
    
    # Usar caminho do diretório de dados configurado
    from config.settings import LOGGING_CONFIG
    data_dir = LOGGING_CONFIG['DATA_DIR']
    results_file = os.path.join(data_dir, 'paper_trading_results.json')
    
    logger.info(f"Iniciando monitor de resultados: {results_file}")
    
    while True:
        try:
            if os.path.exists(results_file):
                current_modified = os.path.getmtime(results_file)
                if last_modified is None or current_modified > last_modified:
                    last_modified = current_modified
                    
                    # Arquivo foi atualizado, enviar dados via WebSocket
                    results = load_trading_results()
                    if results:
                        socketio.emit('trading_update', results)
                        app_state['last_update'] = datetime.now().isoformat()
            
            time.sleep(2)  # Verificar a cada 2 segundos
        
        except Exception as e:
            logger.error(f"Erro no monitor de resultados: {e}")
            time.sleep(5)

# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

def shutdown_handler(signum, frame):
    """Handler para shutdown gracioso."""
    logger.info("🛑 Encerrando interface web...")
    if app_state['bot_running']:
        app_state['bot_running'] = False
        if TRADING_CONFIG['PAPER_TRADING_MODE']:
            paper_trader.save_results()
    sys.exit(0)

if __name__ == '__main__':
    # Configurar handlers de shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Iniciar monitor de resultados em thread separada
    monitor_thread = threading.Thread(target=monitor_trading_results)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Adicionar alerta inicial
    add_alert('info', 'Interface web iniciada. Sistema pronto para uso.')
    
    logger.info("🌐 Iniciando interface web...")
    print("🌐 Iniciando interface web...")
    print("📊 Dashboard disponível em: http://localhost:5000")
    print("🔧 Configurações em: http://localhost:5000/settings")
    print("📈 Trading view em: http://localhost:5000/trading")
    print("📊 Analytics em: http://localhost:5000/analytics")
    
    # Iniciar servidor Flask com SocketIO
    socketio.run(app, 
                debug=WEB_CONFIG.get('DEBUG', True), 
                host=WEB_CONFIG.get('HOST', '0.0.0.0'), 
                port=WEB_CONFIG.get('PORT', 5000), 
                allow_unsafe_werkzeug=True)
