# 📋 GUIA: Sistema de Ordens Reais - CryptoAI Bot

## 🚀 Visão Geral

O módulo `orders.py` foi completamente redesenhado para suportar **ordens reais** na Binance Futures, mantendo total compatibilidade com o sistema de **paper trading** existente.

## ⚙️ Características Principais

### 🔄 Modo Híbrido Inteligente
- **Paper Trading Mode**: Sistema redireciona automaticamente para simulação
- **Real Trading Mode**: Executa ordens reais na Binance Futures
- **Detecção Automática**: Baseada na configuração `PAPER_TRADING_MODE`

### 🛡️ Segurança Integrada
- ✅ Verificação de saldo antes de cada operação
- ✅ Integração com `risk_manager` para controle de risco
- ✅ Logs detalhados de todas as operações
- ✅ Configuração de Stop Loss automático
- ✅ Precisão de quantidade baseada nas regras da Binance

### 📊 Configurações Centralizadas
- Todos os parâmetros vêm do `config/settings.py`
- Valores padrão configuráveis para valor do trade, alavancagem, stop loss
- Configuração de tarifas realistas integrada

## 🔧 Como Usar

### 1. Configuração Básica

```python
from src.trading.orders import open_long_position, open_short_position, close_position
from src.utils.exchange_setup import create_exchange_connection

# Criar conexão com a Binance
client = create_exchange_connection()

# Verificar se a conexão foi bem-sucedida
if client is None:
    print("Erro: Não foi possível conectar à Binance")
    exit()
```

### 2. Abrir Posições

```python
# Abrir posição LONG (usa configurações padrão do settings.py)
success = open_long_position(client, 'BTCUSDT')

# Abrir posição LONG com parâmetros customizados
success = open_long_position(
    client, 
    'ETHUSDT', 
    trade_value_usd=20.0,  # $20 por trade
    stop_loss_pct=1.5      # Stop loss de 1.5%
)

# Abrir posição SHORT
success = open_short_position(client, 'ADAUSDT')
```

### 3. Fechar Posições

```python
# Fechar posição existente
success = close_position(client, 'BTCUSDT')

# Verificar status da posição
status = get_position_status(client, 'BTCUSDT')
# Retorna: 'IN_LONG', 'IN_SHORT', 'MONITORING', ou 'ERROR'
```

### 4. Funções Avançadas

```python
from src.trading.orders import check_account_balance, list_open_positions, cancel_all_orders

# Verificar saldo da conta
balance_ok = check_account_balance(client)

# Listar todas as posições abertas
positions = list_open_positions(client)
for pos in positions:
    print(f"{pos['symbol']}: {pos['side']} {pos['size']:.8f} @ ${pos['entry_price']:.2f}")

# Cancelar todas as ordens de um símbolo
cancel_all_orders(client, 'BTCUSDT')

# Cancelar todas as ordens de todos os símbolos
cancel_all_orders(client)
```

## ⚡ Mudança Entre Modos

### Para Ativar Ordens Reais:

1. **Edite `config/settings.py`:**
```python
PAPER_TRADING_MODE = False  # Muda de True para False
```

2. **Reinicie o sistema** para aplicar as mudanças

3. **ATENÇÃO**: A partir deste momento, todas as ordens serão **REAIS** e envolverão **dinheiro real**!

### Para Voltar ao Paper Trading:

1. **Edite `config/settings.py`:**
```python
PAPER_TRADING_MODE = True  # Volta para True
```

2. **Reinicie o sistema**

## 🔍 Configurações Importantes

### No arquivo `config/settings.py`:

```python
# Configurações de Trading
TRADE_VALUE_USD = 5.0        # Valor em USD por trade
STOP_LOSS_PCT = 2.0          # Stop loss em percentual
LEVERAGE_LEVEL = 50          # Nível de alavancagem
MAX_CONCURRENT_TRADES = 10   # Máximo de trades simultâneos

# Segurança
PAPER_TRADING_MODE = True    # True = Simulação, False = Real
MAX_DAILY_LOSS = 20.0        # Perda máxima diária
```

## 📋 Logs e Monitoramento

### Níveis de Log:

- **INFO**: Operações normais e status
- **WARNING**: Alertas e redirecionamentos
- **ERROR**: Erros e falhas nas operações

### Exemplo de Log Real:

```
2025-07-15 22:15:30 - real_trading - INFO - 🟢 Iniciando abertura de posição LONG para BTCUSDT
2025-07-15 22:15:30 - real_trading - INFO -    💰 Valor: $5.0 | 📈 Alavancagem: 50x | ⛔ Stop Loss: 2.0%
2025-07-15 22:15:31 - real_trading - INFO -    📊 Preço atual: $43250.340000
2025-07-15 22:15:31 - real_trading - INFO -    📦 Quantidade: 0.00578125
2025-07-15 22:15:31 - real_trading - INFO - 📤 Enviando ordem de COMPRA a mercado...
2025-07-15 22:15:32 - real_trading - INFO - ✅ Ordem LONG executada!
2025-07-15 22:15:32 - real_trading - INFO -    💲 Preço de entrada: $43251.20
2025-07-15 22:15:32 - real_trading - INFO -    🆔 Order ID: 1234567890
2025-07-15 22:15:33 - real_trading - INFO - 📝 Criando Stop Loss em $42366.18
2025-07-15 22:15:33 - real_trading - INFO - ✅ Stop Loss criado! ID: 1234567891
2025-07-15 22:15:33 - real_trading - INFO - 🎯 Posição LONG para BTCUSDT aberta com sucesso!
```

## ⚠️ Avisos de Segurança

### 🚨 IMPORTANTE - ORDENS REAIS:

1. **Teste Sempre no Paper Trading Primeiro**
   - Valide sua estratégia com `PAPER_TRADING_MODE = True`
   - Só mude para ordens reais após estar confiante

2. **Verifique Suas API Keys**
   - Certifique-se de que as chaves em `src/keys.py` estão corretas
   - Confirme que 'Enable Futures' está ativado na sua API key

3. **Controle de Risco**
   - Configure `MAX_DAILY_LOSS` adequadamente
   - Mantenha `TRADE_VALUE_USD` em valores que você pode perder
   - Monitore sempre o `MAX_CONCURRENT_TRADES`

4. **Saldo Mínimo**
   - Mantenha pelo menos 2x `TRADE_VALUE_USD` como saldo disponível
   - O sistema verifica automaticamente antes de cada trade

## 🧪 Teste de Segurança

Execute o teste integrado para validar:

```bash
cd CryptoAI
python src/trading/orders.py
```

Este teste:
- ✅ Detecta automaticamente o modo (Paper/Real)
- ✅ Executa operações seguras de teste
- ✅ Mostra logs detalhados
- ✅ Confirma funcionamento antes de usar em produção

## 📞 Integração com Main.py

O sistema mantém **total compatibilidade** com o código existente:

```python
# Estas funções funcionam automaticamente no modo Paper ou Real:
from src.trading.orders import open_long_position, open_short_position, close_position

# O sistema detecta automaticamente o modo baseado em PAPER_TRADING_MODE
success = open_long_position(client, symbol)  # Funciona nos dois modos
```

## 🎯 Próximos Passos

1. **Teste no Paper Trading** - Valide todas as funcionalidades
2. **Configure Parâmetros** - Ajuste valores em `config/settings.py`
3. **Monitore Logs** - Acompanhe o comportamento do sistema
4. **Ative Ordens Reais** - Quando estiver confiante, mude `PAPER_TRADING_MODE = False`

---

**Lembre-se**: Trading envolve riscos financeiros. Use sempre gestão de risco adequada e teste extensivamente antes de usar dinheiro real.
