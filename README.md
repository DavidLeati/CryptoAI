# 🤖 CryptoAI Trading Bot

**Sistema Avançado de Trading Automatizado para Criptomoedas com Interface Web em Tempo Real**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Binance API](https://img.shields.io/badge/Exchange-Binance-yellow.svg)](https://binance.com/)

## 📋 Índice

- [🎯 Características](#-características)
- [📁 Estrutura do Projeto](#-estrutura-do-projeto)
- [🚀 Instalação](#-instalação)
- [💻 Como Usar](#-como-usar)
- [⚙️ Configuração](#️-configuração)
- [🌐 Interface Web](#-interface-web)
- [📊 Indicadores Técnicos](#-indicadores-técnicos)
- [🔧 API Endpoints](#-api-endpoints)
- [📈 Performance](#-performance)
- [🛡️ Segurança](#️-segurança)

## 🎯 Características

### ✅ **Core Features**
- 🧪 **Paper Trading**: Simulação completa sem risco financeiro
- 💰 **Trading Real**: Execução automática na Binance
- 📊 **65+ Ativos**: Monitoramento de principais criptomoedas
- 🔄 **Multi-threading**: Processamento paralelo eficiente
- 💾 **Salvamento Automático**: Resultados persistidos em tempo real
- 🔧 **Sistema Integrado**: Todas as funções centralizadas no paper_trading.py

### 🌐 **Interface Web**
- 📱 **Dashboard Responsivo**: Visualização em tempo real
- 📈 **Gráficos Interativos**: Chart.js com dados dinâmicos
- ⚙️ **Configuração Visual**: Ajustes sem editar código
- 🔔 **Notificações Push**: Alertas instantâneos
- 📊 **Analytics Avançado**: Métricas profissionais de trading

### 🔬 **Análise Técnica**
- 📉 **RSI**: Força relativa com zonas de sobrecompra/sobrevenda
- 📊 **MACD**: Convergência de médias móveis
- 🎯 **Bollinger Bands**: Análise de volatilidade
- 📈 **EMAs**: Médias móveis exponenciais múltiplas
- 🔍 **Multi-timeframe**: Confirmação em diferentes períodos

## 📁 Estrutura do Projeto

```
CryptoAI/
├── 📄 run.py                    # Ponto de entrada principal
├── 📄 requirements.txt          # Dependências Python
├── 📄 README.md                 # Documentação
│
├── 📁 src/                      # Código fonte principal
│   ├── 📁 core/                 # Lógica central
│   │   ├── 📄 __init__.py
│   │   └── 📄 main.py           # Orquestração principal
│   │
│   ├── 📁 trading/              # Execução de trades
│   │   ├── 📄 __init__.py
│   │   ├── 📄 paper_trading.py  # Sistema de simulação
│   │   └── 📄 orders.py         # Gerenciamento de ordens
│   │
│   ├── 📁 analysis/             # Análise técnica
│   │   ├── 📄 __init__.py
│   │   └── 📄 analysis.py       # Indicadores e sinais
│   │
│   ├── 📁 utils/                # Utilitários
│   │   ├── 📄 __init__.py
│   │   ├── 📄 data.py           # Coleta de dados
│   │   └── 📄 exchange_setup.py # Configuração da exchange
│   │
│   └── 📁 web/                  # Interface web
│       ├── 📄 __init__.py
│       ├── 📄 web_interface.py  # Servidor Flask
│       ├── 📁 templates/        # Templates HTML
│       │   ├── 📄 base.html
│       │   ├── 📄 dashboard.html
│       │   ├── 📄 trading.html
│       │   ├── 📄 analytics.html
│       │   └── 📄 settings.html
│       └── 📁 static/           # Assets estáticos
│           ├── 📁 css/
│           │   └── 📄 style.css
│           └── 📁 js/
│               └── 📄 app.js
│
├── 📁 config/                   # Configurações
│   └── 📄 settings.py           # Configurações centralizadas
│
├── 📁 data/                     # Dados e resultados
│   ├── 📄 paper_trading_results.json
│   └── 📄 *.txt
│
├── 📁 logs/                     # Arquivos de log
│
└── 📁 tests/                    # Testes automatizados
```

## 🚀 Instalação

### 1. **Pré-requisitos**
```bash
# Python 3.12+ obrigatório
python --version  # Deve ser 3.12+
```

### 2. **Clone o Repositório**
```bash
git clone https://github.com/DavidLeati/CryptoAI.git
cd CryptoAI
```

### 3. **Instalar Dependências**
```bash
pip install -r requirements.txt
```

### 4. **Configuração (Opcional)**
```bash
# Editar configurações se necessário
notepad config/settings.py
```

## 💻 Como Usar

### 🎮 **Comandos Principais**

```bash
# Ver ajuda e opções disponíveis
python run.py --help

# Executar bot de trading (modo terminal)
python run.py bot

# Executar interface web (recomendado)
python run.py web

# Ver status do sistema
python run.py status
```

### 🌐 **Interface Web (Recomendado)**

1. **Iniciar Interface**:
   ```bash
   python run.py web
   ```

2. **Acessar Dashboard**:
   - 📊 **Dashboard**: http://localhost:5000
   - 📈 **Trading**: http://localhost:5000/trading
   - 📊 **Analytics**: http://localhost:5000/analytics
   - ⚙️ **Configurações**: http://localhost:5000/settings

3. **Controlar Bot**:
   - ▶️ **Iniciar**: Botão "Iniciar Bot" no dashboard
   - ⏹️ **Parar**: Botão "Parar Bot" no dashboard
   - 📊 **Monitorar**: Dados atualizados em tempo real

## ⚙️ Configuração

### 📋 **Configurações Principais** (`config/settings.py`)

```python
# Modo de operação
PAPER_TRADING_MODE = True        # True = Simulação, False = Real

# Parâmetros de trading
TRADE_VALUE_USD = 50.0          # Valor por trade
STOP_LOSS_PCT = 2.0             # Stop loss %
TAKE_PROFIT_PCT = 5.0           # Take profit %
LEVERAGE_LEVEL = 1              # Alavancagem

# Gerenciamento de risco
MAX_CONCURRENT_TRADES = 5       # Trades simultâneos
MAX_DAILY_LOSS = 200.0          # Perda máxima diária
```

### 🎯 **Ativos Monitorados**

O sistema monitora **65+ criptomoedas**, incluindo:
- 💎 **Principais**: BTC, ETH, BNB, ADA, SOL, XRP
- 🚀 **Altcoins**: DOT, LINK, MATIC, UNI, AAVE
- 🐕 **Meme Coins**: DOGE, SHIB, PEPE, FLOKI
- 📊 **DeFi**: SUSHI, CRV, COMP, YFI

## 🌐 Interface Web

### 📊 **Dashboard Principal**
- 💰 Saldo total e P&L em tempo real
- 📈 Gráfico de performance da conta
- 🎯 Métricas de trading (win rate, drawdown)
- 📋 Lista de trades recentes
- 🔄 Status do bot e conexão

### 📈 **Página de Trading**
- 📊 Histórico completo de trades
- 🔍 Filtros por período, status, ativo
- 📈 Posições abertas com P&L não realizado
- 🎯 Sinais de trading detectados
- 📊 Performance por ativo

### 📊 **Analytics Avançado**
- 📈 ROI, Sharpe Ratio, Maximum Drawdown
- 📊 Curva de capital com drawdown
- 📅 P&L diário e mensal
- 🎯 Distribuição de resultados
- ⏰ Análise por horário de trading

### ⚙️ **Configurações**
- 🎮 Parâmetros de trading
- 🛡️ Gerenciamento de risco
- 📊 Indicadores técnicos
- 🔔 Notificações
- 🖥️ Configurações do sistema

## 📊 Indicadores Técnicos

### 🔬 **RSI (Relative Strength Index)**
- **Período**: 14 candlesticks
- **Sobrevenda**: < 30
- **Sobrecompra**: > 70
- **Peso**: 25% do sinal final

### 📈 **MACD (Moving Average Convergence Divergence)**
- **EMA Rápida**: 12 períodos
- **EMA Lenta**: 26 períodos
- **Linha de Sinal**: 9 períodos
- **Peso**: 25% do sinal final

### 🎯 **Bollinger Bands**
- **Período**: 20 candlesticks
- **Desvio Padrão**: 2.0
- **Peso**: 25% do sinal final

### 📊 **EMAs (Exponential Moving Averages)**
- **EMA Curta**: 12 períodos
- **EMA Longa**: 26 períodos
- **EMA Filtro**: 200 períodos
- **Peso**: 25% do sinal final

## 🔧 API Endpoints

### 📊 **Status e Dados**
```
GET  /api/status                 # Status geral do sistema
GET  /api/trading-results        # Resultados do trading
GET  /api/settings               # Configurações atuais
```

### 🎮 **Controle do Bot**
```
POST /api/bot/start              # Iniciar bot
POST /api/bot/stop               # Parar bot
POST /api/settings               # Atualizar configurações
```

### 📈 **WebSocket Events**
```
connect                          # Conexão estabelecida
trading_update                   # Novo trade executado
bot_status_changed               # Status do bot alterado
new_alert                        # Nova notificação
```

## 📈 Performance

### 🎯 **Métricas de Exemplo** (Paper Trading)
```
💰 Capital Inicial: $1,000.00
📊 Saldo Final: $1,083.28
📈 ROI: +8.33%
🎯 Win Rate: 71.4%
📉 Max Drawdown: -2.1%
⏱️ Trades Executados: 7
🕐 Período: 24 horas
```

### ⚡ **Performance Técnica**
- 🔄 **Update Rate**: 30 segundos
- 💾 **Latência de Dados**: < 1 segundo
- 🔗 **Websocket**: Tempo real
- 💻 **Uso de CPU**: < 5%
- 💾 **Uso de RAM**: < 200MB

## 🛡️ Segurança

### 🔒 **Modo Paper Trading**
- ✅ **Zero Risco**: Nenhuma ordem real executada
- 📊 **Dados Reais**: Preços da Binance em tempo real
- 💾 **Simulação Completa**: Todas as funcionalidades disponíveis

### 🔐 **Chaves de API**
- 🔑 **Somente Leitura**: Paper trading não precisa de chaves
- 🛡️ **Armazenamento Seguro**: Variáveis de ambiente recomendadas
- 🔒 **Criptografia**: Implementar para trading real

### 🚨 **Controles de Risco**
- ⛔ **Stop Loss**: Limitação automática de perdas
- 💰 **Position Sizing**: Controle de tamanho das posições
- 📉 **Daily Loss Limit**: Limite de perda diária
- 🔄 **Max Concurrent**: Limite de trades simultâneos

---

## 🚀 **Getting Started**

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar interface web
python run.py web

# 3. Acessar dashboard
# http://localhost:5000

# 4. Iniciar bot via interface
# Clicar em "Iniciar Bot" no dashboard
```
