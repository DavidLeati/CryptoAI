# config/settings.py
# Configurações centralizadas do CryptoAI Trading Bot

import os
from typing import List, Dict, Any

# =============================================================================
# CONFIGURAÇÕES GERAIS
# =============================================================================

# Versão do sistema
VERSION = "0.0.1"
APP_NAME = "CryptoAI"
AUTHOR = "David Leati"

# Modo de operação
PAPER_TRADING_MODE = True  # True = Simulação, False = Trading Real
DEBUG_MODE = True

# =============================================================================
# CONFIGURAÇÕES DE TARIFAS E CUSTOS
# =============================================================================

# Tarifas da Binance (Paper Trading Realista)
BINANCE_MAKER_FEE = 0.0005  # 0.05% para maker orders
BINANCE_TAKER_FEE = 0.0005  # 0.05% para taker orders (mais comum em bots rápidos)
DEFAULT_TRADING_FEE = BINANCE_TAKER_FEE  # Usar taker fee como padrão

# Configurações de slippage
ESTIMATED_SLIPPAGE = 0.0002  # 0.02% slippage estimado
TOTAL_ENTRY_COST = DEFAULT_TRADING_FEE + ESTIMATED_SLIPPAGE  # 0.07% total na entrada
TOTAL_EXIT_COST = DEFAULT_TRADING_FEE + ESTIMATED_SLIPPAGE   # 0.07% total na saída

# Configurações de spread
ESTIMATED_SPREAD = 0.0001  # 0.01% spread médio estimado

# =============================================================================
# CONFIGURAÇÕES DE TRADING
# =============================================================================

# Parâmetros de trading
INITIAL_BALANCE = 100.0      # Saldo inicial para paper trading
TRADE_VALUE_USD = 5.0        # Valor em USD por trade
STOP_LOSS_PCT = 1.0          # Stop loss em percentual
TAKE_PROFIT_PCT = 5.0        # Take profit em percentual
LEVERAGE_LEVEL = 50          # Nível de alavancagem (1x = sem alavancagem)

# Gerenciamento de risco
MAX_CONCURRENT_TRADES = 10   # Máximo de trades simultâneos
MAX_DAILY_LOSS = 20.0        # Perda máxima diária em USD
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
    '1000XECUSDT', '1000LUNCUSDT',
    
    # Altcoins populares
    'CHRUSDT', 'GALAUSDT', 'APEUSDT', 'GMTUSDT', 'JASMYUSDT',
    'WOOUSDT', 'LRCUSDT', 'IMXUSDT', 'OPUSDT', 'INJUSDT',
    'STGUSDT', 'SPELLUSDT', 'LDOUSDT', 'CVXUSDT', 'GALUSDT'
]

# =============================================================================
# CONFIGURAÇÕES DE INDICADORES TÉCNICOS
# =============================================================================

# RSI (Relative Strength Index)
RSI_PERIOD = 7 # Período do RSI (padrão = 14)
RSI_OVERSOLD = 20 # Nível de sobrecompra do RSI (padrão = 20)
RSI_OVERBOUGHT = 80 # Nível de sobrevenda do RSI (padrão = 80)
RSI_WEIGHT = 0.25 # Peso do RSI na análise integrada (padrão = 0.25)

# MACD (Moving Average Convergence Divergence)
MACD_FAST = 5 # Período rápido (padrão = 12)
MACD_SLOW = 13 # Período lento (padrão = 26)
MACD_SIGNAL = 6 # Período do sinal (padrão = 9)
MACD_WEIGHT = 0.25 # Peso do MACD na análise integrada (padrão = 0.25)

# Bandas de Bollinger
BB_PERIOD = 14 # Período das Bandas de Bollinger (padrão = 20)
BB_STD = 2.0 # Desvio padrão para as bandas (padrão = 2.0)
BB_WEIGHT = 0.25 # Peso das Bandas de Bollinger na análise integrada (padrão = 0.25)

# Médias Móveis Exponenciais
EMA_SHORT = 7 # Período curto da EMA (padrão = 12)
EMA_LONG = 14 # Período longo da EMA (padrão = 26)
EMA_FILTER = 100 # Período da EMA para filtro de tendência (padrão = 200)
EMA_WEIGHT = 0.25 # Peso da EMA na análise integrada (padrão = 0.25)

# =============================================================================
# CONFIGURAÇÕES DE ANÁLISE DE MOMENTUM (LEGACY)
# =============================================================================

# Parâmetros de entrada (Momentum)
PRICE_CHANGE_THRESHOLD = 0.5        # % mínima de mudança de preço para detectar momentum
PRICE_CHANGE_PERIOD_MINUTES = 3     # Período em minutos para calcular mudança de preço
VOLUME_MULTIPLIER_THRESHOLD = 2.0   # Multiplicador mínimo de volume comparado à média
VOLUME_AVERAGE_PERIOD_MINUTES = 20  # Período em minutos para calcular volume médio

# Parâmetros de saída (Exaustão)
RSI_OVERBOUGHT_EXIT = 75.0          # Nível RSI para fechar posições LONGs
RSI_OVERSOLD_EXIT = 25.0            # Nível RSI para fechar posições SHORTs

# Parâmetros de detecção de exaustão de momentum
MOMENTUM_EXHAUSTION_PERIOD = 5      # Períodos para verificar perda de momentum
VOLUME_DECLINE_THRESHOLD = 0.5      # Multiplicador que indica queda de volume

# =============================================================================
# CONFIGURAÇÕES DE ANÁLISE INTEGRADA
# =============================================================================

# Thresholds para sinais integrados
INTEGRATED_SIGNAL_THRESHOLD_BUY = 0.15   # Score mínimo para sinal de COMPRA
INTEGRATED_SIGNAL_THRESHOLD_SELL = -0.15 # Score máximo para sinal de VENDA
CONFIDENCE_MULTIPLIER = 2.0              # Multiplicador para amplificar confiança

# Thresholds de confiança
HIGH_CONFIDENCE_THRESHOLD = 0.8          # Confiança alta - aceita sem confirmação
MEDIUM_CONFIDENCE_THRESHOLD = 0.5        # Confiança média - verifica consenso
CONSENSUS_INDICATORS_REQUIRED = 3        # Mínimo de indicadores concordando para consenso

# Confirmação de momentum - fatores de redução dos thresholds
MOMENTUM_CONFIRMATION_PRICE_FACTOR = 0.3  # 30% do threshold de preço
MOMENTUM_CONFIRMATION_VOLUME_FACTOR = 0.5 # 50% do threshold de volume

# Análise de saída integrada
EXIT_CONFIDENCE_THRESHOLD = 0.4          # Confiança mínima para sugerir saída
EXIT_CONFIRMATION_THRESHOLD = 0.6        # Confiança para saída sem confirmação momentum
RSI_CRITICAL_STRENGTH = 0.6              # Força mínima do RSI para saída crítica

# Requisitos de dados
MIN_DATA_BUFFER = 3                       # Buffer mínimo além do maior período
FALLBACK_EMA_FILTER = 30                  # EMA filter alternativo se muito grande

# =============================================================================
# CONFIGURAÇÕES DE PADRÕES DE REVERSÃO
# =============================================================================

# Volatilidade para padrões de reversão
MIN_VOLATILITY_FOR_PATTERNS = 0.02       # Volatilidade mínima para confiar em padrões

# Contexto de tendência
TREND_CHANGE_THRESHOLD = 0.02             # 2% de mudança para definir tendência

# Divergência preço-volume
DIVERGENCE_PRICE_THRESHOLD = 0.01         # 1% mudança de preço
DIVERGENCE_VOLUME_THRESHOLD = 0.2         # 20% mudança de volume
DIVERGENCE_LOOKBACK_PERIODS = 10          # Períodos para analisar divergência

# Volatilidade
VOLATILITY_CALCULATION_PERIOD = 20        # Períodos para calcular volatilidade

# Análise de tendência
TREND_ANALYSIS_LOOKBACK = 10              # Períodos para analisar contexto de tendência

# =============================================================================
# CONFIGURAÇÕES DE TIMEFRAMES
# =============================================================================

PRIMARY_TIMEFRAME = '1m'      # Timeframe principal para análise (padrão = 5m)
SECONDARY_TIMEFRAME = '5m'    # Timeframe secundário (padrão = 15m)
CONFIRMATION_TIMEFRAME = '15m' # Timeframe para confirmação (padrão = 1h)

# Intervalos de atualização
UPDATE_INTERVAL = 30         # Segundos entre atualizações (padrão = 30)
HEARTBEAT_INTERVAL = 60      # Segundos entre heartbeats (padrão = 60)

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
MAX_WORKER_THREADS = 1000
ANALYSIS_THREADS = 100

# Cache
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 minutos

# Performance
ENABLE_PROFILING = True
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

# =============================================================================
# CONFIGURAÇÕES ESTRUTURADAS PARA COMPATIBILIDADE
# =============================================================================

# Configurações de trading estruturadas para compatibilidade com paper_trading.py
TRADING_CONFIG = {
    'INITIAL_BALANCE': INITIAL_BALANCE,      
    'PAPER_TRADING_MODE': PAPER_TRADING_MODE,
    'TRADE_VALUE_USD': TRADE_VALUE_USD,
    'STOP_LOSS_PCT': STOP_LOSS_PCT,
    'TAKE_PROFIT_PCT': TAKE_PROFIT_PCT,
    'LEVERAGE_LEVEL': LEVERAGE_LEVEL,
    'MAX_CONCURRENT_TRADES': MAX_CONCURRENT_TRADES,
    'MAX_POSITIONS': MAX_CONCURRENT_TRADES,
    'MAX_DAILY_LOSS': MAX_DAILY_LOSS,
    'DAILY_LOSS_LIMIT': MAX_DAILY_LOSS,
    'MAX_POSITION_SIZE_PCT': MAX_POSITION_SIZE_PCT,
    
    # Configurações de tarifas e custos realistas
    'TRADING_FEE': DEFAULT_TRADING_FEE,      # 0.05% - Taxa de trading da Binance
    'ENTRY_FEE': TOTAL_ENTRY_COST,          # 0.07% - Taxa + slippage na entrada
    'EXIT_FEE': TOTAL_EXIT_COST,            # 0.07% - Taxa + slippage na saída
    'SLIPPAGE': ESTIMATED_SLIPPAGE,         # 0.02% - Slippage estimado
    'SPREAD': ESTIMATED_SPREAD,             # 0.01% - Spread médio estimado
    'REALISTIC_FEES': True                  # Flag para ativar/desativar tarifas realistas
}

# Configurações da interface web estruturadas
WEB_CONFIG = {
    'HOST': WEB_HOST,
    'PORT': WEB_PORT,
    'DEBUG': DEBUG_WEB,
    'SECRET_KEY': SECRET_KEY,
    'SOCKETIO_ASYNC_MODE': SOCKETIO_ASYNC_MODE,
    'CORS_ORIGINS': CORS_ORIGINS
}

# Configurações de ativos estruturadas
ASSETS_CONFIG = {
    'SYMBOLS': LISTA_DE_ATIVOS,
    'TOTAL_ASSETS': len(LISTA_DE_ATIVOS)
}

# Configurações de logging estruturadas para compatibilidade
LOGGING_CONFIG = {
    'LOG_LEVEL': LOG_LEVEL,
    'LOG_FORMAT': LOG_FORMAT,
    'LOG_FILE': LOG_FILE,
    'MAX_LOG_SIZE': MAX_LOG_SIZE,
    'LOG_BACKUP_COUNT': LOG_BACKUP_COUNT,
    'DATA_DIR': DATA_DIR,
    'RESULTS_DIR': RESULTS_DIR,
    'BACKUP_DIR': BACKUP_DIR,
    'TRADING_RESULTS_FILE': TRADING_RESULTS_FILE,
    'SETTINGS_FILE': SETTINGS_FILE,
    'PERFORMANCE_FILE': PERFORMANCE_FILE
}
