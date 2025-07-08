# analysis.py
# Módulo acessório responsável pela análise técnica dos dados de mercado.
# Contém a lógica para identificar sinais de trading.

import pandas as pd

# =============================================================================
# 1. PARÂMETROS DA ESTRATÉGIA
#    Centralizar os parâmetros aqui facilita o ajuste fino (tuning) da estratégia.
# =============================================================================

# Para um sinal de COMPRA ou VENDA, o preço deve mudar em pelo menos 2.0%...
PRICE_CHANGE_THRESHOLD = 2.0 
# ...nos últimos 5 minutos.
PRICE_CHANGE_PERIOD_MINUTES = 5

# E o volume da última vela deve ser pelo menos 5 vezes maior que a média...
VOLUME_MULTIPLIER_THRESHOLD = 5.0
# ...dos últimos 30 minutos (excluindo a vela atual).
VOLUME_AVERAGE_PERIOD_MINUTES = 30


# =============================================================================
# 2. FUNÇÃO PRINCIPAL DE ANÁLISE
# =============================================================================

def find_momentum_signal(market_data: pd.DataFrame) -> str:
    """
    Analisa os dados de mercado para encontrar um sinal de momentum de alta ou baixa.

    Args:
        market_data (pd.DataFrame): DataFrame contendo os dados OHLCV.

    Returns:
        str: Um sinal de 'COMPRAR', 'VENDER' ou 'AGUARDAR'.
    """
    # --- Validação de Segurança ---
    # Garante que temos dados suficientes para realizar os cálculos.
    required_rows = max(PRICE_CHANGE_PERIOD_MINUTES, VOLUME_AVERAGE_PERIOD_MINUTES) + 1
    if market_data is None or len(market_data) < required_rows:
        print("Dados insuficientes para análise. Aguardando mais dados.")
        return 'AGUARDAR'

    # --- Extração de Dados ---
    # Pegamos a vela mais recente (a última linha do DataFrame)
    latest_candle = market_data.iloc[-1]
    current_price = latest_candle['close']
    current_volume = latest_candle['volume']

    # --- Análise de Preço ---
    # Pegamos o preço de N minutos atrás para comparação
    price_N_periods_ago = market_data['close'].iloc[-1 - PRICE_CHANGE_PERIOD_MINUTES]
    
    # Calculamos a variação percentual
    # Evita divisão por zero se o preço antigo for 0
    if price_N_periods_ago == 0:
        return 'AGUARDAR'
    price_change_pct = ((current_price / price_N_periods_ago) - 1) * 100

    # --- Análise de Volume ---
    # Calculamos a média de volume das velas ANTERIORES à vela atual
    previous_candles = market_data.iloc[-1 - VOLUME_AVERAGE_PERIOD_MINUTES:-1]
    average_volume = previous_candles['volume'].mean()

    # Calculamos o multiplicador de volume
    # Evita divisão por zero se o volume médio for 0
    if average_volume == 0:
        volume_multiplier = float('inf') # Volume atual é infinitamente maior
    else:
        volume_multiplier = current_volume / average_volume

    # --- Lógica de Decisão ---
    print(f"Análise: Variação de Preço={price_change_pct:.2f}%, Multiplicador de Volume={volume_multiplier:.2f}x")
    
    # Condição de Compra: Alta forte de preço com volume alto para confirmar
    if price_change_pct >= PRICE_CHANGE_THRESHOLD and volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD:
        return 'COMPRAR'

    # Condição de Venda: Queda forte de preço com volume alto para confirmar
    if price_change_pct <= -PRICE_CHANGE_THRESHOLD and volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD:
        return 'VENDER'
        
    # Se nenhuma das condições acima for atendida, não fazemos nada
    return 'AGUARDAR'

# =============================================================================
# 3. BLOCO DE TESTE
# =============================================================================

if __name__ == '__main__':
    print("--- Testando o módulo analysis.py ---")

    # Cenário 1: Criando dados FALSOS para simular um SINAL DE COMPRA
    print("\n[Teste 1] Simulação de um sinal de COMPRA claro:")
    buy_data = {
        'open': [100]*40, 'high': [100]*40, 'low': [99]*40,
        'close': [100]*35 + [100, 101, 102, 103, 105], # Preço sobe 5% nos últimos 5 min
        'volume': [10]*39 + [55] # Volume explode na última vela (média é 10)
    }
    df_buy = pd.DataFrame(buy_data)
    signal = find_momentum_signal(df_buy)
    print(f"Sinal Gerado: {signal}")
    assert signal == 'COMPRAR'
    print("Teste de COMPRA passou!")

    # Cenário 2: Criando dados FALSOS para simular um SINAL DE VENDA
    print("\n[Teste 2] Simulação de um sinal de VENDA claro:")
    sell_data = {
        'open': [100]*40, 'high': [101]*40, 'low': [95]*40,
        'close': [100]*35 + [100, 99, 98, 97, 95], # Preço cai 5% nos últimos 5 min
        'volume': [10]*39 + [60] # Volume explode na última vela (média é 10)
    }
    df_sell = pd.DataFrame(sell_data)
    signal = find_momentum_signal(df_sell)
    print(f"Sinal Gerado: {signal}")
    assert signal == 'VENDER'
    print("Teste de VENDA passou!")

    # Cenário 3: Criando dados FALSOS para um mercado normal (SEM SINAL)
    print("\n[Teste 3] Simulação de um cenário sem sinal (mercado normal):")
    hold_data = {
        'open': [100]*40, 'high': [101]*40, 'low': [99]*40,
        'close': [100]*35 + [100.1, 100.2, 100.3, 100.2, 100.1], # Variação pequena
        'volume': [10]*39 + [12] # Volume normal
    }
    df_hold = pd.DataFrame(hold_data)
    signal = find_momentum_signal(df_hold)
    print(f"Sinal Gerado: {signal}")
    assert signal == 'AGUARDAR'
    print("Teste de AGUARDAR passou!")
    print("\n--- Fim dos testes ---")