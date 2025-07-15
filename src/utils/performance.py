# src/utils/performance.py
# Sistema de métricas e performance baseado nas configurações

import time
import json
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import sys
from pathlib import Path

# Adicionar config ao path
config_path = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_path))

try:
    from settings import PERFORMANCE_FILE, ENABLE_PROFILING, DATA_DIR
except ImportError:
    # Valores padrão se não conseguir importar
    PERFORMANCE_FILE = 'data/performance_history.json'
    ENABLE_PROFILING = False
    DATA_DIR = 'data'

@dataclass
class PerformanceMetric:
    """Classe para representar uma métrica de performance."""
    timestamp: str
    metric_name: str
    value: float
    category: str
    symbol: Optional[str] = None
    metadata: Optional[Dict] = None

class PerformanceMonitor:
    """Monitor de performance para o CryptoAI."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.trading_metrics: Dict[str, Any] = {}
        self.system_metrics: Dict[str, Any] = {}
        self.start_time = time.time()
        self._lock = threading.RLock()
        self.profiling_enabled = ENABLE_PROFILING
        
        # Carregar métricas existentes
        self._load_metrics()
    
    def _load_metrics(self) -> None:
        """Carrega métricas do arquivo."""
        try:
            if Path(PERFORMANCE_FILE).exists():
                with open(PERFORMANCE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Carregar apenas métricas das últimas 24 horas
                cutoff_time = datetime.now() - timedelta(days=1)
                
                for metric_data in data.get('metrics', []):
                    metric_time = datetime.fromisoformat(metric_data['timestamp'])
                    if metric_time > cutoff_time:
                        metric = PerformanceMetric(**metric_data)
                        self.metrics.append(metric)
                
                self.trading_metrics = data.get('trading_metrics', {})
                self.system_metrics = data.get('system_metrics', {})
                
        except Exception as e:
            print(f"⚠️  Erro ao carregar métricas: {e}")
    
    def _save_metrics(self) -> None:
        """Salva métricas no arquivo."""
        try:
            # Criar diretório se não existir
            Path(PERFORMANCE_FILE).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'metrics': [asdict(metric) for metric in self.metrics],
                'trading_metrics': self.trading_metrics,
                'system_metrics': self.system_metrics,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(PERFORMANCE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Erro ao salvar métricas: {e}")
    
    def record_metric(self, name: str, value: float, category: str = "general",
                     symbol: Optional[str] = None, metadata: Optional[Dict] = None) -> None:
        """Registra uma métrica de performance."""
        with self._lock:
            metric = PerformanceMetric(
                timestamp=datetime.now().isoformat(),
                metric_name=name,
                value=value,
                category=category,
                symbol=symbol,
                metadata=metadata or {}
            )
            
            self.metrics.append(metric)
            
            # Manter apenas últimas 1000 métricas na memória
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
    
    def record_trade_performance(self, symbol: str, pnl: float, pnl_pct: float,
                               duration_minutes: float, trade_type: str) -> None:
        """Registra performance de um trade."""
        self.record_metric("trade_pnl", pnl, "trading", symbol, {
            "pnl_pct": pnl_pct,
            "duration_minutes": duration_minutes,
            "trade_type": trade_type
        })
        
        self.record_metric("trade_duration", duration_minutes, "trading", symbol)
        self.record_metric("trade_return", pnl_pct, "trading", symbol)
        
        # Atualizar métricas de trading
        with self._lock:
            if symbol not in self.trading_metrics:
                self.trading_metrics[symbol] = {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_pnl": 0.0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0,
                    "avg_duration": 0.0
                }
            
            metrics = self.trading_metrics[symbol]
            metrics["total_trades"] += 1
            metrics["total_pnl"] += pnl
            
            if pnl > 0:
                metrics["winning_trades"] += 1
            
            metrics["best_trade"] = max(metrics["best_trade"], pnl)
            metrics["worst_trade"] = min(metrics["worst_trade"], pnl)
            
            # Calcular duração média
            total_duration = metrics["avg_duration"] * (metrics["total_trades"] - 1) + duration_minutes
            metrics["avg_duration"] = total_duration / metrics["total_trades"]
    
    def record_trade_start(self, symbol: str, side: str, price: float, value: float) -> None:
        """Registra o início de um trade."""
        self.record_metric("trade_start", value, "trading", symbol, {
            "side": side,
            "price": price
        })
        
        # Atualizar métricas de trading
        with self._lock:
            if symbol not in self.trading_metrics:
                self.trading_metrics[symbol] = {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "total_pnl": 0.0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0,
                    "avg_duration": 0.0
                }
            self.trading_metrics[symbol]["total_trades"] += 1

    def record_trade_end(self, symbol: str, exit_price: float, pnl: float) -> None:
        """Registra o fim de um trade."""
        self.record_metric("trade_end", pnl, "trading", symbol, {
            "exit_price": exit_price
        })
        
        # Atualizar métricas de trading
        with self._lock:
            if symbol in self.trading_metrics:
                metrics = self.trading_metrics[symbol]
                metrics["total_pnl"] += pnl
                
                if pnl > 0:
                    metrics["winning_trades"] += 1

    def record_analysis_time(self, symbol: str, analysis_time_ms: float) -> None:
        """Registra tempo de análise."""
        self.record_metric("analysis_time", analysis_time_ms, "performance", symbol)
    
    def record_api_latency(self, endpoint: str, latency_ms: float) -> None:
        """Registra latência da API."""
        self.record_metric("api_latency", latency_ms, "performance", None, {
            "endpoint": endpoint
        })
    
    def record_memory_usage(self, usage_mb: float) -> None:
        """Registra uso de memória."""
        self.record_metric("memory_usage", usage_mb, "system")
    
    def record_cpu_usage(self, usage_pct: float) -> None:
        """Registra uso de CPU."""
        self.record_metric("cpu_usage", usage_pct, "system")
    
    def get_trading_summary(self) -> Dict[str, Any]:
        """Retorna resumo de performance de trading."""
        with self._lock:
            total_trades = sum(m["total_trades"] for m in self.trading_metrics.values())
            total_winning = sum(m["winning_trades"] for m in self.trading_metrics.values())
            total_pnl = sum(m["total_pnl"] for m in self.trading_metrics.values())
            
            win_rate = (total_winning / total_trades * 100) if total_trades > 0 else 0
            
            # Métricas dos últimos 24h
            cutoff_time = datetime.now() - timedelta(days=1)
            recent_trades = [
                m for m in self.metrics 
                if m.category == "trading" and m.metric_name == "trade_pnl"
                and datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
            
            daily_pnl = sum(m.value for m in recent_trades)
            daily_trades = len(recent_trades)
            
            return {
                "total_trades": total_trades,
                "winning_trades": total_winning,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "daily_trades": daily_trades,
                "daily_pnl": daily_pnl,
                "avg_trade": total_pnl / total_trades if total_trades > 0 else 0,
                "best_symbol": max(
                    self.trading_metrics.items(),
                    key=lambda x: x[1]["total_pnl"],
                    default=("N/A", {"total_pnl": 0})
                )[0],
                "symbols_traded": len(self.trading_metrics)
            }
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Retorna métricas de performance do sistema."""
        uptime_hours = (time.time() - self.start_time) / 3600
        
        # Métricas da última hora
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent_metrics = [
            m for m in self.metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        # Calcular médias
        analysis_times = [m.value for m in recent_metrics if m.metric_name == "analysis_time"]
        api_latencies = [m.value for m in recent_metrics if m.metric_name == "api_latency"]
        memory_usage = [m.value for m in recent_metrics if m.metric_name == "memory_usage"]
        cpu_usage = [m.value for m in recent_metrics if m.metric_name == "cpu_usage"]
        
        return {
            "uptime_hours": uptime_hours,
            "avg_analysis_time": sum(analysis_times) / len(analysis_times) if analysis_times else 0,
            "avg_api_latency": sum(api_latencies) / len(api_latencies) if api_latencies else 0,
            "avg_memory_usage": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            "avg_cpu_usage": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
            "total_metrics": len(self.metrics),
            "profiling_enabled": self.profiling_enabled
        }
    
    def get_symbol_performance(self, symbol: str) -> Dict[str, Any]:
        """Retorna performance de um símbolo específico."""
        with self._lock:
            if symbol not in self.trading_metrics:
                return {"error": f"Nenhuma métrica encontrada para {symbol}"}
            
            metrics = self.trading_metrics[symbol].copy()
            
            # Adicionar win rate
            if metrics["total_trades"] > 0:
                metrics["win_rate"] = (metrics["winning_trades"] / metrics["total_trades"]) * 100
            else:
                metrics["win_rate"] = 0
            
            # Métricas recentes do símbolo
            cutoff_time = datetime.now() - timedelta(days=1)
            recent_trades = [
                m for m in self.metrics 
                if m.symbol == symbol and m.category == "trading"
                and datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
            
            metrics["daily_trades"] = len([m for m in recent_trades if m.metric_name == "trade_pnl"])
            metrics["daily_pnl"] = sum(m.value for m in recent_trades if m.metric_name == "trade_pnl")
            
            return metrics
    
    def cleanup_old_metrics(self, days_to_keep: int = 7) -> int:
        """Remove métricas antigas."""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        with self._lock:
            original_count = len(self.metrics)
            self.metrics = [
                m for m in self.metrics 
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
            removed_count = original_count - len(self.metrics)
            
            if removed_count > 0:
                self._save_metrics()
            
            return removed_count
    
    def save_performance_data(self) -> None:
        """Salva dados de performance."""
        self._save_metrics()

# Instância global do monitor de performance
performance_monitor = PerformanceMonitor()

# Funções de conveniência
def record_trade_performance(symbol: str, pnl: float, pnl_pct: float,
                           duration_minutes: float, trade_type: str) -> None:
    """Registra performance de trade."""
    performance_monitor.record_trade_performance(symbol, pnl, pnl_pct, duration_minutes, trade_type)

def record_analysis_time(symbol: str, analysis_time_ms: float) -> None:
    """Registra tempo de análise."""
    performance_monitor.record_analysis_time(symbol, analysis_time_ms)

def get_trading_summary() -> Dict[str, Any]:
    """Retorna resumo de trading."""
    return performance_monitor.get_trading_summary()

def get_system_performance() -> Dict[str, Any]:
    """Retorna performance do sistema."""
    return performance_monitor.get_system_performance()

def save_performance_data() -> None:
    """Salva dados de performance."""
    performance_monitor.save_performance_data()
