# src/utils/cache.py
# Sistema de cache centralizado baseado nas configurações

import time
import threading
from typing import Any, Optional, Dict
import sys
from pathlib import Path

# Adicionar config ao path
config_path = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_path))

try:
    from settings import CACHE_ENABLED, CACHE_TTL
except ImportError:
    # Valores padrão se não conseguir importar
    CACHE_ENABLED = True
    CACHE_TTL = 300  # 5 minutos

class CryptoAICache:
    """Sistema de cache thread-safe para o CryptoAI."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.enabled = CACHE_ENABLED
        self.default_ttl = CACHE_TTL
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Verifica se uma entrada do cache expirou."""
        if 'expires_at' not in entry:
            return True
        return time.time() > entry['expires_at']
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera um valor do cache."""
        if not self.enabled:
            return None
        
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Armazena um valor no cache."""
        if not self.enabled:
            return
        
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl
            }
    
    def delete(self, key: str) -> bool:
        """Remove uma entrada do cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove entradas expiradas do cache."""
        if not self.enabled:
            return 0
        
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values()
                if self._is_expired(entry)
            )
            
            return {
                'enabled': self.enabled,
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'default_ttl': self.default_ttl
            }

# Instância global do cache
cache_instance = CryptoAICache()

# Funções de conveniência
def get_cached_data(key: str) -> Optional[Any]:
    """Recupera dados do cache."""
    return cache_instance.get(key)

def cache_data(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Armazena dados no cache."""
    cache_instance.set(key, value, ttl)

def invalidate_cache(key: str) -> bool:
    """Invalida uma entrada do cache."""
    return cache_instance.delete(key)

def clear_cache() -> None:
    """Limpa todo o cache."""
    cache_instance.clear()

def cache_market_data(symbol: str, timeframe: str, data: Any) -> None:
    """Cache específico para dados de mercado."""
    key = f"market_data:{symbol}:{timeframe}"
    cache_data(key, data, 60)  # Cache por 1 minuto

def get_cached_market_data(symbol: str, timeframe: str) -> Optional[Any]:
    """Recupera dados de mercado do cache."""
    key = f"market_data:{symbol}:{timeframe}"
    return get_cached_data(key)

def cache_analysis_result(symbol: str, analysis_type: str, result: Any) -> None:
    """Cache específico para resultados de análise."""
    key = f"analysis:{symbol}:{analysis_type}"
    cache_data(key, result, 30)  # Cache por 30 segundos

def get_cached_analysis(symbol: str, analysis_type: str) -> Optional[Any]:
    """Recupera análise do cache."""
    key = f"analysis:{symbol}:{analysis_type}"
    return get_cached_data(key)
