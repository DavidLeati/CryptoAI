# CryptoAI Trading Bot - Migração para python-binance

## Mudanças Realizadas

O projeto foi migrado da biblioteca `ccxt` para a biblioteca oficial `python-binance` da Binance. Esta mudança oferece:

### Vantagens da python-binance:
- **Biblioteca oficial**: Mantida pela própria Binance
- **Melhor performance**: Otimizada especificamente para a Binance
- **Documentação completa**: Suporte direto da Binance
- **Menos dependências**: Biblioteca mais leve
- **Atualizações frequentes**: Sempre compatível com a API mais recente

### Principais Alterações:

#### 1. **exchange_setup.py**
- Substituted `ccxt.binance()` por `Client()` da python-binance
- Configuração de testnet agora usa o parâmetro `testnet=True`
- Funções de alavancagem adaptadas para usar métodos específicos dos futuros

#### 2. **data.py**
- Substituída `fetch_ohlcv()` por `futures_klines()`
- Mapeamento de timeframes para constantes da Binance
- Conversão automática de símbolos (ex: 'BTC/USDT:USDT' → 'BTCUSDT')

#### 3. **orders.py**
- Todas as funções de trading adaptadas para usar `futures_create_order()`
- Implementação correta de stop-loss com `reduceOnly=True`
- Suporte para ordens de mercado e stop-market

#### 4. **main.py**
- Atualização de todas as chamadas de função para usar `client` em vez de `exchange`
- Mantida a estrutura multithread original

## Configuração

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar API Keys
Edite o arquivo `keys.py` e adicione suas credenciais da Binance:

```python
BINANCE_API = "sua_api_key_aqui"
SECRET_API = "sua_secret_key_aqui"
```

### 3. Obter API Keys da Binance
1. Acesse [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Crie uma nova API key
3. **IMPORTANTE**: Ative "Enable Futures" para trading de futuros
4. Configure restrições de IP se necessário
5. Adicione as chaves no arquivo `keys.py`

## Uso

Execute o bot:
```bash
python main.py
```

## Funcionalidades

- ✅ Trading automatizado em múltiplos ativos
- ✅ Análise técnica em tempo real
- ✅ Gestão automática de stop-loss
- ✅ Execução multithread
- ✅ Suporte a posições LONG e SHORT
- ✅ Integração com Binance Futures Testnet

## Importante

- O bot está configurado para usar a **Testnet da Binance** por padrão
- Para trading real, remova ou comente `testnet=True` no arquivo `exchange_setup.py`
- Sempre teste na testnet antes de usar fundos reais
- Configure adequadamente os limites de risco antes de usar

## Arquivos de Configuração

- `requirements.txt`: Dependências do projeto
- `keys.py`: Chaves da API (não versione este arquivo!)
- `main.py`: Ponto de entrada do bot
- `exchange_setup.py`: Configuração da conexão
- `data.py`: Busca de dados de mercado
- `orders.py`: Execução de ordens
- `analysis.py`: Análise técnica (não modificado)
