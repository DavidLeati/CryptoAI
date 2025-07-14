# analysis.py
# Módulo acessório responsável pela análise técnica dos dados de mercado.
# Contém a lógica para identificar sinais de trading.

import pandas as pd
import numpy as np # Importado para cálculos numéricos

# =============================================================================
# 1. PARÂMETROS DAS ESTRATÉGIAS
# =============================================================================

# --- Parâmetros de ENTRADA (Momentum) ---
PRICE_CHANGE_THRESHOLD = 1.0 
PRICE_CHANGE_PERIOD_MINUTES = 5
VOLUME_MULTIPLIER_THRESHOLD = 5.0
VOLUME_AVERAGE_PERIOD_MINUTES = 30

# --- Parâmetros de SAÍDA (Exaustão) ---
RSI_PERIOD = 14
RSI_OVERBOUGHT = 85.0 # Nível de sobrecompra para considerar fechar um LONG
RSI_OVERSOLD = 15.0   # Nível de sobrevenda para considerar fechar um SHORT


# =============================================================================
# 2. FUNÇÕES AUXILIARES DE ANÁLISE
# =============================================================================

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calcula o Índice de Força Relativa (RSI)."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# =============================================================================
# 3. FUNÇÕES PRINCIPAIS DE SINALIZAÇÃO
# =============================================================================

def find_momentum_signal(market_data: pd.DataFrame) -> str:
    """
    Analisa os dados de mercado para encontrar um sinal de ENTRADA baseado em momentum.
    (Lógica original mantida)
    """
    required_rows = max(PRICE_CHANGE_PERIOD_MINUTES, VOLUME_AVERAGE_PERIOD_MINUTES) + 1
    if market_data is None or len(market_data) < required_rows:
        return 'AGUARDAR'

    latest_candle = market_data.iloc[-1]
    current_price = latest_candle['close']
    current_volume = latest_candle['volume']

    price_N_periods_ago = market_data['close'].iloc[-1 - PRICE_CHANGE_PERIOD_MINUTES]
    if price_N_periods_ago == 0: return 'AGUARDAR'
    price_change_pct = ((current_price / price_N_periods_ago) - 1) * 100

    previous_candles = market_data.iloc[-1 - VOLUME_AVERAGE_PERIOD_MINUTES:-1]
    average_volume = previous_candles['volume'].mean()
    if average_volume == 0:
        volume_multiplier = float('inf')
    else:
        volume_multiplier = current_volume / average_volume
    
    print(f"Análise de ENTRADA: Variação Preço={price_change_pct:.2f}%, Vol. Multiplicador={volume_multiplier:.2f}x")

    if price_change_pct >= PRICE_CHANGE_THRESHOLD and volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD:
        return 'COMPRAR'
    if price_change_pct <= -PRICE_CHANGE_THRESHOLD and volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD:
        return 'VENDER'
        
    return 'AGUARDAR'

def find_exhaustion_signal(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Analisa uma posição aberta para encontrar um sinal de SAÍDA baseado em exaustão.

    Args:
        market_data (pd.DataFrame): DataFrame com os dados de mercado.
        position_side (str): O lado da posição atual ('LONG' ou 'SHORT').

    Returns:
        bool: True se um sinal de saída for encontrado, False caso contrário.
    """
    if market_data is None or len(market_data) < RSI_PERIOD + 1:
        print("Dados insuficientes para análise de saída. Mantendo posição.")
        return False

    # 1. Calcular o RSI
    market_data['rsi'] = calculate_rsi(market_data['close'], RSI_PERIOD)
    current_rsi = market_data['rsi'].iloc[-1]
    
    if np.isnan(current_rsi):
        return False

    print(f"Análise de SAÍDA ({position_side}): RSI atual = {current_rsi:.2f}")

    # 2. Lógica de Decisão de Saída
    if position_side == 'LONG' and current_rsi >= RSI_OVERBOUGHT:
        print(f"SINAL DE EXAUSTÃO (LONG): RSI ({current_rsi:.2f}) atingiu o nível de sobrecompra ({RSI_OVERBOUGHT}).")
        return True # Sinal para fechar o LONG

    if position_side == 'SHORT' and current_rsi <= RSI_OVERSOLD:
        print(f"SINAL DE EXAUSTÃO (SHORT): RSI ({current_rsi:.2f}) atingiu o nível de sobrevenda ({RSI_OVERSOLD}).")
        return True # Sinal para fechar o SHORT

    # Nenhuma condição de saída foi atendida
    return False