# src/utils/logger.py
# Sistema de logging centralizado baseado nas configurações

import logging
import logging.handlers
import os
from pathlib import Path
import sys

# Adicionar config ao path
config_path = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_path))

try:
    from settings import (
        LOG_LEVEL, LOG_FORMAT, LOG_FILE, MAX_LOG_SIZE, 
        LOG_BACKUP_COUNT, DATA_DIR
    )
except ImportError:
    # Valores padrão se não conseguir importar
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/cryptoai.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

class CryptoAILogger:
    """Sistema de logging centralizado para o CryptoAI."""
    
    def __init__(self):
        self.loggers = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura o sistema de logging."""
        # Criar diretório de logs se não existir
        log_dir = Path(LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar nível de log
        numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        
        # Configurar formatador
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Handler para arquivo com rotação
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, 
            maxBytes=MAX_LOG_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
        
        # Configurar logger raiz
        root_logger = logging.getLogger('cryptoai')
        root_logger.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Evitar duplicação de logs
        root_logger.propagate = False
        
        self.loggers['root'] = root_logger
    
    def get_logger(self, name: str = 'cryptoai') -> logging.Logger:
        """Retorna um logger configurado."""
        if name not in self.loggers:
            logger = logging.getLogger(f'cryptoai.{name}')
            logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
            # O logger herda os handlers do logger pai
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def log_trade(self, symbol: str, action: str, details: dict):
        """Log específico para trades."""
        trade_logger = self.get_logger('trades')
        trade_logger.info(f"TRADE - {symbol} - {action} - {details}")
    
    def log_analysis(self, symbol: str, signal: str, indicators: dict):
        """Log específico para análises."""
        analysis_logger = self.get_logger('analysis')
        analysis_logger.debug(f"ANALYSIS - {symbol} - {signal} - {indicators}")
    
    def log_error(self, component: str, error: Exception, context: str = ""):
        """Log específico para erros."""
        error_logger = self.get_logger('errors')
        error_logger.error(f"ERROR - {component} - {context} - {str(error)}", exc_info=True)
    
    def log_performance(self, metric: str, value: float, context: str = ""):
        """Log específico para métricas de performance."""
        perf_logger = self.get_logger('performance')
        perf_logger.info(f"PERFORMANCE - {metric} - {value} - {context}")

# Instância global do logger
logger_instance = CryptoAILogger()

# Funções de conveniência
def get_logger(name: str = 'cryptoai') -> logging.Logger:
    """Retorna um logger configurado."""
    return logger_instance.get_logger(name)

def log_trade(symbol: str, action: str, details: dict):
    """Log de trade."""
    logger_instance.log_trade(symbol, action, details)

def log_analysis(symbol: str, signal: str, indicators: dict):
    """Log de análise."""
    logger_instance.log_analysis(symbol, signal, indicators)

def log_error(component: str, error: Exception, context: str = ""):
    """Log de erro."""
    logger_instance.log_error(component, error, context)

def log_performance(metric: str, value: float, context: str = ""):
    """Log de performance."""
    logger_instance.log_performance(metric, value, context)
