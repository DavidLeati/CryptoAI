# src/utils/notifications.py
# Sistema de notificações baseado nas configurações

import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import sys
from pathlib import Path
from datetime import datetime

# Adicionar config ao path
config_path = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_path))

try:
    from settings import (
        EMAIL_ENABLED, SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD,
        WEBHOOK_ENABLED, WEBHOOK_URL
    )
except ImportError:
    # Valores padrão se não conseguir importar
    EMAIL_ENABLED = False
    SMTP_SERVER = ''
    SMTP_PORT = 587
    EMAIL_USER = ''
    EMAIL_PASSWORD = ''
    WEBHOOK_ENABLED = False
    WEBHOOK_URL = ''

class NotificationManager:
    """Gerenciador de notificações para o CryptoAI."""
    
    def __init__(self):
        self.email_enabled = EMAIL_ENABLED
        self.webhook_enabled = WEBHOOK_ENABLED
        self.notification_history: List[Dict] = []
    
    def send_email(self, subject: str, message: str, to_email: str = None) -> bool:
        """Envia notificação por email."""
        if not self.email_enabled or not EMAIL_USER or not EMAIL_PASSWORD:
            return False
        
        try:
            # Configurar email
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = to_email or EMAIL_USER
            msg['Subject'] = f"[CryptoAI] {subject}"
            
            # Corpo do email
            body = f"""
CryptoAI Trading Bot - Notificação
====================================

{message}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Este é um email automático do sistema de trading.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_USER, to_email or EMAIL_USER, text)
            server.quit()
            
            print(f"📧 Email enviado: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
            return False
    
    def send_webhook(self, data: Dict) -> bool:
        """Envia notificação via webhook."""
        if not self.webhook_enabled or not WEBHOOK_URL:
            return False
        
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'source': 'CryptoAI Trading Bot',
                'data': data
            }
            
            response = requests.post(
                WEBHOOK_URL, 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"🔗 Webhook enviado: {data.get('type', 'notification')}")
                return True
            else:
                print(f"❌ Webhook falhou: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar webhook: {e}")
            return False
    
    def notify(self, notification_type: str, title: str, message: str, 
              data: Optional[Dict] = None, priority: str = "normal") -> None:
        """Envia notificação através de todos os canais configurados."""
        
        # Criar registro da notificação
        notification = {
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }
        
        self.notification_history.append(notification)
        
        # Manter apenas últimas 100 notificações
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]
        
        # Enviar por email se habilitado e for prioridade alta
        if priority in ['high', 'critical']:
            self.send_email(title, message)
        
        # Enviar por webhook se habilitado
        webhook_data = {
            'type': notification_type,
            'title': title,
            'message': message,
            'priority': priority
        }
        if data:
            webhook_data.update(data)
        
        self.send_webhook(webhook_data)
        
        # Log da notificação
        print(f"🔔 [{notification_type.upper()}] {title}: {message}")
    
    def notify_trade_opened(self, symbol: str, side: str, price: float, 
                           value: float, leverage: int) -> None:
        """Notificação específica para abertura de trade."""
        self.notify(
            'trade_opened',
            f'Trade Aberto - {symbol}',
            f'Posição {side.upper()} aberta em {symbol} por ${price:.4f}\n'
            f'Valor: ${value:.2f} | Alavancagem: {leverage}x',
            {
                'symbol': symbol,
                'side': side,
                'price': price,
                'value': value,
                'leverage': leverage
            },
            'normal'
        )
    
    def notify_trade_closed(self, symbol: str, side: str, entry_price: float,
                           exit_price: float, pnl: float, pnl_pct: float) -> None:
        """Notificação específica para fechamento de trade."""
        result = "LUCRO" if pnl > 0 else "PREJUÍZO"
        priority = "normal" if pnl > 0 else "high"
        
        self.notify(
            'trade_closed',
            f'Trade Fechado - {symbol} - {result}',
            f'Posição {side.upper()} fechada em {symbol}\n'
            f'Entrada: ${entry_price:.4f} | Saída: ${exit_price:.4f}\n'
            f'P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)',
            {
                'symbol': symbol,
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            },
            priority
        )
    
    def notify_signal_detected(self, symbol: str, signal: str, 
                              indicators: Dict) -> None:
        """Notificação específica para sinais detectados."""
        self.notify(
            'signal_detected',
            f'Sinal {signal} - {symbol}',
            f'Sinal de {signal} detectado para {symbol}\n'
            f'Indicadores: {indicators}',
            {
                'symbol': symbol,
                'signal': signal,
                'indicators': indicators
            },
            'normal'
        )
    
    def notify_risk_alert(self, alert_type: str, message: str, 
                         metrics: Dict) -> None:
        """Notificação específica para alertas de risco."""
        self.notify(
            'risk_alert',
            f'Alerta de Risco - {alert_type}',
            message,
            metrics,
            'high'
        )
    
    def notify_system_status(self, status: str, message: str) -> None:
        """Notificação específica para status do sistema."""
        priority = 'critical' if status in ['error', 'stopped'] else 'normal'
        
        self.notify(
            'system_status',
            f'Sistema {status.upper()}',
            message,
            {'status': status},
            priority
        )
    
    def get_notification_history(self, limit: int = 50) -> List[Dict]:
        """Retorna histórico de notificações."""
        return self.notification_history[-limit:]
    
    def clear_notification_history(self) -> None:
        """Limpa histórico de notificações."""
        self.notification_history.clear()

# Instância global do gerenciador de notificações
notification_manager = NotificationManager()

# Funções de conveniência
def notify(notification_type: str, title: str, message: str, 
          data: Optional[Dict] = None, priority: str = "normal") -> None:
    """Envia notificação."""
    notification_manager.notify(notification_type, title, message, data, priority)

def notify_trade_opened(symbol: str, side: str, price: float, 
                       value: float, leverage: int) -> None:
    """Notifica abertura de trade."""
    notification_manager.notify_trade_opened(symbol, side, price, value, leverage)

def notify_trade_closed(symbol: str, side: str, entry_price: float,
                       exit_price: float, pnl: float, pnl_pct: float) -> None:
    """Notifica fechamento de trade."""
    notification_manager.notify_trade_closed(symbol, side, entry_price, exit_price, pnl, pnl_pct)

def notify_signal_detected(symbol: str, signal: str, indicators: Dict) -> None:
    """Notifica sinal detectado."""
    notification_manager.notify_signal_detected(symbol, signal, indicators)

def notify_risk_alert(alert_type: str, message: str, metrics: Dict) -> None:
    """Notifica alerta de risco."""
    notification_manager.notify_risk_alert(alert_type, message, metrics)

def notify_system_status(status: str, message: str) -> None:
    """Notifica status do sistema."""
    notification_manager.notify_system_status(status, message)
