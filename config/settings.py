# config/settings.py
# Configurações centralizadas do CryptoAI Trading Bot

import os
from typing import List, Dict, Any

# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================

# Versão do sistema
VERSION = "1.0.0"
APP_NAME = "CryptoAI Trading Bot"
AUTHOR = "David Leati"

# Modo de operação
PAPER_TRADING_MODE = True  # True = Simulação, False = Trading Real
DEBUG_MODE = True

# =============================================================================
# CONFIGURAÇÕES DE TRADING
# =============================================================================

# Parâmetros de trading
TRADE_VALUE_USD = 50.0      # Valor em USD por trade
STOP_LOSS_PCT = 2.0         # Stop loss em percentual
TAKE_PROFIT_PCT = 5.0       # Take profit em percentual
LEVERAGE_LEVEL = 1          # Nível de alavancagem (1x = sem alavancagem)

# Gerenciamento de risco
MAX_CONCURRENT_TRADES = 5   # Máximo de trades simultâneos
MAX_DAILY_LOSS = 200.0      # Perda máxima diária em USD
MAX_POSITION_SIZE_PCT = 10.0 # Máximo percentual do capital por posição

# =============================================================================
# LISTA DE ATIVOS PARA MONITORAMENTO
# =============================================================================

LISTA_DE_ATIVOS = [
    # Principais criptomoedas
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
    'XRPUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT',
    'MATICUSDT', 'LTCUSDT', 'ATOMUSDT', 'UNIUSDT', 'ETCUSDT',
    'BCHUSDT', 'FILUSDT', 'TRXUSDT', 'XLMUSDT', 'VETUSDT',
    'ICPUSDT', 'NEARUSDT', 'ALGOUSDT', 'HBARUSDT', 'EGLDUSDT',
    'FLOWUSDT', 'MANAUSDT', 'SANDUSDT', 'AXSUSDT', 'THETAUSDT',
    'FTMUSDT', 'KLAYUSDT', 'HNTUSDT', 'KSMUSDT', 'XTZUSDT',
    'WAVESUSDT', 'ZILUSDT', 'CHZUSDT', 'ENJUSDT', 'SUSHIUSDT',
    'SNXUSDT', 'COMPUSDT', 'MKRUSDT', 'YFIUSDT', 'AAVEUSDT',
    'CRVUSDT', 'BALUSDT', 'RENUSDT', 'UMAUSDT', 'ALPHAUSDT',
    
    # Tokens com denominação especial (grupos de 1000)
    '1000PEPEUSDT', '1000SHIBUSDT', '1000FLOKIUSDT', '1000BONKUSDT',
    '1000XECUSDT', '1000LUNCUSDT', '1000RATUSDT', '1000BTTUSDT',
    
    # Altcoins populares
    'CHRUSDT', 'GALAUSDT', 'APEUSDT', 'GMTUSDT', 'JASMYUSDT',
    'WOOUSDT', 'LRCUSDT', 'IMXUSDT', 'OPUSDT', 'INJUSDT',
    'STGUSDT', 'SPELLUSDT', 'LDOUSDT', 'CVXUSDT', 'GALUSDT'
]

# =============================================================================
# CONFIGURAÇÕES DE INDICADORES TÉCNICOS
# =============================================================================

# RSI (Relative Strength Index)
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
RSI_WEIGHT = 0.25

# MACD (Moving Average Convergence Divergence)
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MACD_WEIGHT = 0.25

# Bandas de Bollinger
BB_PERIOD = 20
BB_STD = 2.0
BB_WEIGHT = 0.25

# Médias Móveis Exponenciais
EMA_SHORT = 12
EMA_LONG = 26
EMA_FILTER = 200
EMA_WEIGHT = 0.25

# =============================================================================
# CONFIGURAÇÕES DE TIMEFRAMES
# =============================================================================

PRIMARY_TIMEFRAME = '5m'      # Timeframe principal para análise
SECONDARY_TIMEFRAME = '15m'   # Timeframe secundário
CONFIRMATION_TIMEFRAME = '1h' # Timeframe para confirmação

# Intervalos de atualização
UPDATE_INTERVAL = 30         # Segundos entre atualizações
HEARTBEAT_INTERVAL = 60      # Segundos entre heartbeats

# =============================================================================
# CONFIGURAÇÕES DA EXCHANGE (BINANCE)
# =============================================================================

# Configurações da API (usar variáveis de ambiente em produção)
BINANCE_API_URL = 'https://api.binance.com'
BINANCE_WS_URL = 'wss://stream.binance.com:9443/ws/'
API_TIMEOUT = 30

# Configurações de conexão
MAX_RETRIES = 3
RETRY_DELAY = 5

# =============================================================================
# CONFIGURAÇÕES DA INTERFACE WEB
# =============================================================================

# Flask settings
WEB_HOST = '0.0.0.0'
WEB_PORT = 5000
SECRET_KEY = 'crypto_trading_bot_secret_2025'
DEBUG_WEB = True

# WebSocket settings
SOCKETIO_ASYNC_MODE = 'threading'
CORS_ORIGINS = "*"

# =============================================================================
# CONFIGURAÇÕES DE LOGGING
# =============================================================================

LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'logs/cryptoai.log'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# =============================================================================
# CONFIGURAÇÕES DE DADOS
# =============================================================================

# Diretórios de dados
DATA_DIR = 'data'
RESULTS_DIR = 'data/results'
BACKUP_DIR = 'data/backups'

# Arquivos de dados
TRADING_RESULTS_FILE = 'data/paper_trading_results.json'
SETTINGS_FILE = 'data/user_settings.json'
PERFORMANCE_FILE = 'data/performance_history.json'

# =============================================================================
# CONFIGURAÇÕES DE NOTIFICAÇÕES
# =============================================================================

# Email settings (configurar quando necessário)
EMAIL_ENABLED = False
SMTP_SERVER = ''
SMTP_PORT = 587
EMAIL_USER = ''
EMAIL_PASSWORD = ''

# Webhook settings
WEBHOOK_ENABLED = False
WEBHOOK_URL = ''

# =============================================================================
# CONFIGURAÇÕES AVANÇADAS
# =============================================================================

# Threading
MAX_WORKER_THREADS = 100
ANALYSIS_THREADS = 20

# Cache
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 minutos

# Performance
ENABLE_PROFILING = False
MEMORY_LIMIT_MB = 1024

# =============================================================================
# FUNÇÕES DE CONFIGURAÇÃO
# =============================================================================

def get_config() -> Dict[str, Any]:
    """Retorna todas as configurações como dicionário."""
    return {
        'general': {
            'version': VERSION,
            'app_name': APP_NAME,
            'paper_trading_mode': PAPER_TRADING_MODE,
            'debug_mode': DEBUG_MODE
        },
        'trading': {
            'trade_value_usd': TRADE_VALUE_USD,
            'stop_loss_pct': STOP_LOSS_PCT,
            'take_profit_pct': TAKE_PROFIT_PCT,
            'leverage_level': LEVERAGE_LEVEL,
            'max_concurrent_trades': MAX_CONCURRENT_TRADES,
            'max_daily_loss': MAX_DAILY_LOSS,
            'max_position_size_pct': MAX_POSITION_SIZE_PCT
        },
        'assets': {
            'lista_de_ativos': LISTA_DE_ATIVOS,
            'total_assets': len(LISTA_DE_ATIVOS)
        },
        'indicators': {
            'rsi': {
                'period': RSI_PERIOD,
                'oversold': RSI_OVERSOLD,
                'overbought': RSI_OVERBOUGHT,
                'weight': RSI_WEIGHT
            },
            'macd': {
                'fast': MACD_FAST,
                'slow': MACD_SLOW,
                'signal': MACD_SIGNAL,
                'weight': MACD_WEIGHT
            },
            'bollinger': {
                'period': BB_PERIOD,
                'std': BB_STD,
                'weight': BB_WEIGHT
            },
            'ema': {
                'short': EMA_SHORT,
                'long': EMA_LONG,
                'filter': EMA_FILTER,
                'weight': EMA_WEIGHT
            }
        },
        'timeframes': {
            'primary': PRIMARY_TIMEFRAME,
            'secondary': SECONDARY_TIMEFRAME,
            'confirmation': CONFIRMATION_TIMEFRAME,
            'update_interval': UPDATE_INTERVAL
        },
        'web': {
            'host': WEB_HOST,
            'port': WEB_PORT,
            'debug': DEBUG_WEB
        }
    }

def update_config(new_config: Dict[str, Any]) -> bool:
    """Atualiza configurações (implementar persistência quando necessário)."""
    # TODO: Implementar atualização e salvamento de configurações
    return True

def validate_config() -> List[str]:
    """Valida as configurações atuais."""
    errors = []
    
    if TRADE_VALUE_USD <= 0:
        errors.append("TRADE_VALUE_USD deve ser maior que 0")
    
    if STOP_LOSS_PCT <= 0 or STOP_LOSS_PCT >= 100:
        errors.append("STOP_LOSS_PCT deve estar entre 0 e 100")
    
    if not LISTA_DE_ATIVOS:
        errors.append("LISTA_DE_ATIVOS não pode estar vazia")
    
    if UPDATE_INTERVAL < 5:
        errors.append("UPDATE_INTERVAL deve ser pelo menos 5 segundos")
    
    return errors
