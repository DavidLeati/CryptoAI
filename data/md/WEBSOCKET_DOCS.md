# 📡 WebSocket - Dados em Tempo Real

## 🎯 Visão Geral

A nova funcionalidade de WebSocket permite coletar dados de mercado em tempo real da Binance sem fazer chamadas repetitivas à API REST. Isso reduz significativamente a latência e evita limites de rate limiting.

## 🚀 Características Principais

### ✅ Vantagens do WebSocket
- **Tempo Real:** Dados instantâneos sem delay
- **Eficiência:** Sem limitações de rate limiting da API
- **Baixa Latência:** Conexão direta com stream da Binance
- **Organização Automática:** Dados organizados por timeframe
- **Buffer Inteligente:** Mantém histórico configurável
- **Thread Seguro:** Não bloqueia a aplicação principal

### 📊 Funcionalidades
- Coleta de dados OHLCV em tempo real
- Suporte a múltiplos timeframes (1m, 5m, 15m, 1h, etc.)
- Buffer configurável para manter histórico
- Callbacks personalizados para novos dados
- Monitoramento de vela atual (não fechada)
- Gerenciamento de múltiplos streams simultaneamente

## 🔧 Como Usar

### 1. Uso Básico - Função de Conveniência

```python
from src.utils.data import fetch_realtime_data

def meu_callback(df):
    """Chamado quando uma nova vela é fechada"""
    if df is not None and len(df) > 0:
        ultimo_preco = df.iloc[-1]['close']
        print(f"Novo preço BTC: {ultimo_preco:.2f}")

# Iniciar coleta em tempo real
manager = fetch_realtime_data(
    symbol='BTC/USDT:USDT',
    timeframe='1m',
    limit=500,  # manter últimas 500 velas
    callback=meu_callback
)

# Obter dados atuais
stream_key = 'BTC/USDT:USDT_1m'
dados_historicos = manager.get_dataframe(stream_key)
vela_atual = manager.get_current_candle(stream_key)

# Parar quando terminar
manager.stop_all_streams()
```

### 2. Uso Avançado - Múltiplos Streams

```python
from src.utils.data import RealTimeDataManager

manager = RealTimeDataManager()

# Callbacks específicos
def callback_btc(df):
    print(f"BTC: {df.iloc[-1]['close']:.2f}")

def callback_eth(df):
    print(f"ETH: {df.iloc[-1]['close']:.2f}")

# Iniciar múltiplos streams
manager.start_stream('BTC/USDT:USDT', '1m', 100, callback_btc)
manager.start_stream('ETH/USDT:USDT', '5m', 100, callback_eth)
manager.start_stream('BNB/USDT:USDT', '15m', 50)  # sem callback

# Monitorar dados
import time
time.sleep(30)

# Obter dados específicos
btc_data = manager.get_dataframe('BTC/USDT:USDT_1m')
eth_current = manager.get_current_candle('ETH/USDT:USDT_5m')

# Parar stream específico
manager.stop_stream('BNB/USDT:USDT_15m')

# Ou parar todos
manager.stop_all_streams()
```

### 3. Integração com Sistema de Trading

```python
from src.utils.data import fetch_realtime_data
from src.analysis.analysis import find_comprehensive_signal

class TradingBot:
    def __init__(self):
        self.manager = None
    
    def on_new_candle(self, df):
        """Analisar cada nova vela fechada"""
        if df is not None and len(df) >= 50:  # mínimo para análise
            signal = find_comprehensive_signal(df, self.client, self.symbol)
            
            if signal == 'COMPRAR':
                print("🚀 SINAL DE COMPRA!")
                # Executar ordem de compra
            elif signal == 'VENDER':
                print("📉 SINAL DE VENDA!")
                # Executar ordem de venda
    
    def start_monitoring(self, symbol):
        self.symbol = symbol
        self.manager = fetch_realtime_data(
            symbol=symbol,
            timeframe='1m',
            limit=200,
            callback=self.on_new_candle
        )
    
    def stop(self):
        if self.manager:
            self.manager.stop_all_streams()

# Usar o bot
bot = TradingBot()
bot.start_monitoring('BTC/USDT:USDT')
# Bot roda em background...
bot.stop()
```

## 📋 API Reference

### RealTimeDataManager

#### Métodos Principais

##### `start_stream(symbol, timeframe, limit, callback)`
- **symbol** (str): Símbolo do par (ex: 'BTC/USDT:USDT')
- **timeframe** (str): Timeframe ('1m', '5m', '15m', '1h', etc.)
- **limit** (int): Máximo de velas no buffer
- **callback** (function): Função chamada em novas velas
- **Returns**: stream_key (str)

##### `get_dataframe(stream_key)`
- **stream_key** (str): Chave do stream
- **Returns**: pd.DataFrame com dados OHLCV

##### `get_current_candle(stream_key)`
- **stream_key** (str): Chave do stream  
- **Returns**: dict com dados da vela atual

##### `stop_stream(stream_key)`
- Para um stream específico

##### `stop_all_streams()`
- Para todos os streams ativos

### fetch_realtime_data()
Função de conveniência que cria e configura automaticamente um RealTimeDataManager.

## ⚡ Timeframes Suportados

- **1m, 3m, 5m, 15m, 30m** - Timeframes de minutos
- **1h, 2h, 4h, 6h, 8h, 12h** - Timeframes de horas  
- **1d** - Timeframe diário

## 🔄 Estrutura dos Dados

### DataFrame retornado por `get_dataframe()`:
```
                     open     high      low    close     volume
timestamp                                                      
2025-01-15 10:00:00  42500.0  42600.0  42450.0  42580.0  125.45
2025-01-15 10:01:00  42580.0  42620.0  42560.0  42600.0  98.23
...
```

### Dict retornado por `get_current_candle()`:
```python
{
    'timestamp': pd.Timestamp('2025-01-15 10:02:30'),
    'open': 42600.0,
    'high': 42650.0,
    'low': 42590.0,
    'close': 42635.0,  # preço atual
    'volume': 67.89,
    'is_closed': False  # True quando vela fechar
}
```

## 🛠️ Configuração e Dependências

### Dependências Necessárias
```bash
pip install websocket-client pandas
```

### Configuração de Rede
- Porta: 443 (HTTPS/WSS)
- URL: wss://fstream.binance.com/ws/
- Sem necessidade de autenticação para dados públicos

## ⚠️ Considerações Importantes

### 🔒 Limitações
- Apenas dados públicos (OHLCV, volume)
- Requer conexão internet estável
- Consumo contínuo de largura de banda (mínimo)

### 🎯 Boas Práticas
- Use callbacks eficientes (processamento rápido)
- Limite o tamanho do buffer conforme necessário
- Sempre pare os streams quando não precisar
- Trate exceções de rede adequadamente

### 🚨 Troubleshooting
- **Conexão falha**: Verificar internet/firewall
- **Dados não chegam**: Verificar formato do símbolo
- **Memory leak**: Sempre chamar `stop_all_streams()`
- **Performance**: Reduzir número de streams simultâneos

## 📝 Exemplo Completo

Veja o arquivo `exemplo_websocket.py` no diretório raiz para exemplos práticos de uso.
