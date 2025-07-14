# analysis.py
# Módulo acessório responsável pela análise técnica dos dados de mercado.
# Contém a lógica para identificar sinais de trading.

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Importar configurações centralizadas
config_path = Path(__file__).parent.parent.parent / 'config'
sys.path.insert(0, str(config_path))

try:
    from settings import (
        RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT, RSI_WEIGHT,
        MACD_FAST, MACD_SLOW, MACD_SIGNAL, MACD_WEIGHT,
        BB_PERIOD, BB_STD, BB_WEIGHT,
        EMA_SHORT, EMA_LONG, EMA_FILTER, EMA_WEIGHT
    )
except ImportError:
    # Valores padrão se não conseguir importar
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    RSI_WEIGHT = 0.25
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    MACD_WEIGHT = 0.25
    BB_PERIOD = 20
    BB_STD = 2.0
    BB_WEIGHT = 0.25
    EMA_SHORT = 12
    EMA_LONG = 26
    EMA_FILTER = 200
    EMA_WEIGHT = 0.25

# =============================================================================
# 1. PARÂMETROS DAS ESTRATÉGIAS (LEGADOS - MANTER COMPATIBILIDADE)
# =============================================================================

# --- Parâmetros de ENTRADA (Momentum) ---
PRICE_CHANGE_THRESHOLD = 0.5  # Reduzido para capturar movimentos menores
PRICE_CHANGE_PERIOD_MINUTES = 3  # Período menor para reação mais rápida
VOLUME_MULTIPLIER_THRESHOLD = 2.0  # Reduzido para ser mais sensível
VOLUME_AVERAGE_PERIOD_MINUTES = 20  # Período menor para detecção mais ágil

# --- Parâmetros de SAÍDA (Exaustão) - Usar configurações centralizadas
RSI_OVERBOUGHT_EXIT = 75.0  # Nível mais conservador para fechar LONGs
RSI_OVERSOLD_EXIT = 25.0    # Nível mais conservador para fechar SHORTs

# --- Parâmetros adicionais para detecção de exaustão ---
MOMENTUM_EXHAUSTION_PERIOD = 5  # Períodos para verificar perda de momentum
VOLUME_DECLINE_THRESHOLD = 0.5  # Multiplicador que indica queda de volume


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

def analyze_volume_price_divergence(market_data: pd.DataFrame, lookback_periods: int = 10) -> dict:
    """
    Analisa divergências entre preço e volume que podem indicar reversões.
    
    Returns:
        dict: {'bullish_divergence': bool, 'bearish_divergence': bool, 'strength': float}
    """
    if len(market_data) < lookback_periods + 5:
        return {'bullish_divergence': False, 'bearish_divergence': False, 'strength': 0}
    
    recent_data = market_data.iloc[-lookback_periods:]
    
    # Correlação entre preço e volume
    price_changes = recent_data['close'].pct_change().fillna(0)
    volume_changes = recent_data['volume'].pct_change().fillna(0)
    
    correlation = price_changes.corr(volume_changes)
    
    # Verificar se há divergência significativa
    price_trend = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
    volume_trend = (recent_data['volume'].iloc[-1] - recent_data['volume'].iloc[0]) / recent_data['volume'].iloc[0]
    
    # Divergência baixista: preço subindo, volume caindo
    bearish_divergence = price_trend > 0.01 and volume_trend < -0.2
    
    # Divergência altista: preço caindo, volume subindo  
    bullish_divergence = price_trend < -0.01 and volume_trend > 0.2
    
    return {
        'bullish_divergence': bullish_divergence,
        'bearish_divergence': bearish_divergence,
        'strength': abs(correlation) if not np.isnan(correlation) else 0,
        'price_trend': price_trend,
        'volume_trend': volume_trend
    }

def detect_reversal_patterns(market_data: pd.DataFrame) -> dict:
    """
    Detecta padrões de reversão como martelos, estrelas cadentes, etc.
    
    Returns:
        dict: {'bullish_reversal': bool, 'bearish_reversal': bool, 'pattern_name': str}
    """
    if len(market_data) < 3:
        return {'bullish_reversal': False, 'bearish_reversal': False, 'pattern_name': 'none'}
    
    current = market_data.iloc[-1]
    previous = market_data.iloc[-2] 
    
    # Calcular tamanhos do corpo e sombras
    body_size = abs(current['close'] - current['open'])
    upper_shadow = current['high'] - max(current['open'], current['close'])
    lower_shadow = min(current['open'], current['close']) - current['low']
    candle_range = current['high'] - current['low']
    
    if candle_range == 0:
        return {'bullish_reversal': False, 'bearish_reversal': False, 'pattern_name': 'none'}
    
    # Hammer Pattern (Martelo) - Bullish Reversal
    if (lower_shadow > body_size * 2 and  # Sombra inferior longa
        upper_shadow < body_size * 0.5 and  # Sombra superior pequena
        current['close'] > previous['close']):  # Fechamento em alta
        return {'bullish_reversal': True, 'bearish_reversal': False, 'pattern_name': 'hammer'}
    
    # Shooting Star (Estrela Cadente) - Bearish Reversal  
    if (upper_shadow > body_size * 2 and  # Sombra superior longa
        lower_shadow < body_size * 0.5 and  # Sombra inferior pequena
        current['close'] < previous['close']):  # Fechamento em baixa
        return {'bullish_reversal': False, 'bearish_reversal': True, 'pattern_name': 'shooting_star'}
    
    # Doji - Indecisão (pode indicar reversão)
    if body_size < candle_range * 0.1:  # Corpo muito pequeno
        trend_context = analyze_trend_context(market_data)
        if trend_context == 'uptrend':
            return {'bullish_reversal': False, 'bearish_reversal': True, 'pattern_name': 'doji_bearish'}
        elif trend_context == 'downtrend':
            return {'bullish_reversal': True, 'bearish_reversal': False, 'pattern_name': 'doji_bullish'}
    
    return {'bullish_reversal': False, 'bearish_reversal': False, 'pattern_name': 'none'}

def analyze_trend_context(market_data: pd.DataFrame, lookback: int = 10) -> str:
    """Analisa o contexto de tendência para os últimos períodos"""
    if len(market_data) < lookback:
        return 'sideways'
    
    recent_data = market_data.iloc[-lookback:]
    first_close = recent_data['close'].iloc[0]
    last_close = recent_data['close'].iloc[-1]
    
    trend_change = (last_close - first_close) / first_close
    
    if trend_change > 0.02:  # 2% de alta
        return 'uptrend'
    elif trend_change < -0.02:  # 2% de baixa
        return 'downtrend'
    else:
        return 'sideways'

def calculate_volatility_score(market_data: pd.DataFrame, period: int = 20) -> float:
    """
    Calcula uma pontuação de volatilidade baseada no desvio padrão dos retornos.
    """
    if len(market_data) < period:
        return 0.0
    
    recent_data = market_data.iloc[-period:]
    returns = recent_data['close'].pct_change().dropna()
    
    if len(returns) == 0:
        return 0.0
    
    volatility = returns.std() * np.sqrt(period)  # Volatilidade anualizada aproximada
    return volatility

# =============================================================================
# 3. FUNÇÕES PRINCIPAIS DE SINALIZAÇÃO
# =============================================================================

def find_momentum_signal(market_data: pd.DataFrame) -> str:
    """
    Analisa os dados de mercado para encontrar um sinal de ENTRADA baseado em momentum.
    Melhorado para detectar tanto oportunidades de COMPRA quanto VENDA.
    """
    required_rows = max(PRICE_CHANGE_PERIOD_MINUTES, VOLUME_AVERAGE_PERIOD_MINUTES) + 1
    if market_data is None or len(market_data) < required_rows:
        return 'AGUARDAR'

    latest_candle = market_data.iloc[-1]
    current_price = latest_candle['close']
    current_volume = latest_candle['volume']

    # Calcular mudança de preço no período especificado
    price_N_periods_ago = market_data['close'].iloc[-1 - PRICE_CHANGE_PERIOD_MINUTES]
    if price_N_periods_ago == 0: 
        return 'AGUARDAR'
    
    price_change_pct = ((current_price / price_N_periods_ago) - 1) * 100

    # Calcular volume médio e multiplicador atual
    previous_candles = market_data.iloc[-1 - VOLUME_AVERAGE_PERIOD_MINUTES:-1]
    average_volume = previous_candles['volume'].mean()
    
    if average_volume == 0:
        volume_multiplier = float('inf')
    else:
        volume_multiplier = current_volume / average_volume

    # Verificar também a tendência de preço recente (últimas 2 velas)
    recent_price_trend = 0
    if len(market_data) >= 3:
        price_2_ago = market_data['close'].iloc[-3]
        price_1_ago = market_data['close'].iloc[-2]
        
        if price_1_ago > price_2_ago and current_price > price_1_ago:
            recent_price_trend = 1  # Tendência de alta
        elif price_1_ago < price_2_ago and current_price < price_1_ago:
            recent_price_trend = -1  # Tendência de baixa
    
    print(f"Análise de ENTRADA: Variação Preço={price_change_pct:.2f}%, Vol. Multiplicador={volume_multiplier:.2f}x, Tendência Recente={recent_price_trend}")

    # Sinal de COMPRA (LONG): Momentum de alta + volume elevado
    if (price_change_pct >= PRICE_CHANGE_THRESHOLD and 
        volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD and
        recent_price_trend >= 0):  # Confirma tendência de alta
        print(f"🟢 MOMENTUM DE ALTA detectado: Preço +{price_change_pct:.2f}% com volume {volume_multiplier:.1f}x maior")
        return 'COMPRAR'
    
    # Sinal de VENDA (SHORT): Momentum de baixa + volume elevado  
    if (price_change_pct <= -PRICE_CHANGE_THRESHOLD and 
        volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD and
        recent_price_trend <= 0):  # Confirma tendência de baixa
        print(f"🔴 MOMENTUM DE BAIXA detectado: Preço {price_change_pct:.2f}% com volume {volume_multiplier:.1f}x maior")
        return 'VENDER'
        
    return 'AGUARDAR'

def find_exhaustion_signal(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Analisa uma posição aberta para encontrar um sinal de SAÍDA baseado em exaustão.
    Melhorado para detectar tanto exaustão por RSI quanto por perda de momentum.

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

    # 2. Verificar exaustão de momentum
    momentum_exhausted = detect_momentum_exhaustion(market_data, position_side)

    print(f"Análise de SAÍDA ({position_side}): RSI={current_rsi:.2f}, Momentum Exausto={momentum_exhausted}")

    # 3. Lógica de Decisão de Saída Melhorada
    if position_side == 'LONG':
        # Sair de posição longa se:
        # - RSI indica sobrecompra OU
        # - Momentum de alta está se esgotando
        rsi_exit = current_rsi >= RSI_OVERBOUGHT
        
        if rsi_exit:
            print(f"🚪 SINAL DE SAÍDA (LONG): RSI sobrecomprado ({current_rsi:.2f} >= {RSI_OVERBOUGHT})")
            return True
        elif momentum_exhausted:
            print(f"🚪 SINAL DE SAÍDA (LONG): Momentum de alta se esgotando")
            return True

    elif position_side == 'SHORT':
        # Sair de posição curta se:
        # - RSI indica sobrevenda OU  
        # - Momentum de baixa está se esgotando (preço para de cair com força)
        rsi_exit = current_rsi <= RSI_OVERSOLD
        
        if rsi_exit:
            print(f"🚪 SINAL DE SAÍDA (SHORT): RSI sobrevendido ({current_rsi:.2f} <= {RSI_OVERSOLD})")
            return True
        elif momentum_exhausted:
            print(f"🚪 SINAL DE SAÍDA (SHORT): Momentum de baixa se esgotando")
            return True

    # 4. Verificação adicional: Reversão de tendência baseada em preço
    if len(market_data) >= 5:
        recent_closes = market_data['close'].iloc[-5:].values
        
        if position_side == 'LONG':
            # Para LONG: sair se há 3 fechamentos consecutivos em queda
            consecutive_down = all(recent_closes[i] > recent_closes[i+1] for i in range(2))
            if consecutive_down:
                print(f"🚪 SINAL DE SAÍDA (LONG): Reversão de tendência detectada (3 fechamentos em queda)")
                return True
                
        elif position_side == 'SHORT':
            # Para SHORT: sair se há 3 fechamentos consecutivos em alta
            consecutive_up = all(recent_closes[i] < recent_closes[i+1] for i in range(2))
            if consecutive_up:
                print(f"🚪 SINAL DE SAÍDA (SHORT): Reversão de tendência detectada (3 fechamentos em alta)")
                return True

    # Nenhuma condição de saída foi atendida
    return False

def detect_momentum_exhaustion(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Detecta exaustão de momentum baseado na diminuição de volume e perda de força do movimento.
    """
    if len(market_data) < MOMENTUM_EXHAUSTION_PERIOD + VOLUME_AVERAGE_PERIOD_MINUTES:
        return False
    
    # Analisar últimas velas para detectar perda de momentum
    recent_candles = market_data.iloc[-MOMENTUM_EXHAUSTION_PERIOD:]
    
    # Calcular volume médio recente vs volume médio anterior
    current_avg_volume = recent_candles['volume'].mean()
    previous_avg_volume = market_data.iloc[-VOLUME_AVERAGE_PERIOD_MINUTES:-MOMENTUM_EXHAUSTION_PERIOD]['volume'].mean()
    
    volume_decline_ratio = current_avg_volume / previous_avg_volume if previous_avg_volume > 0 else 1
    
    # Verificar se o momentum está perdendo força
    if position_side == 'LONG':
        # Para posições longas, verificar se as altas estão diminuindo
        recent_highs = recent_candles['high'].values
        high_momentum_declining = len(recent_highs) >= 3 and recent_highs[-1] < recent_highs[-2] < recent_highs[-3]
        
        if volume_decline_ratio < VOLUME_DECLINE_THRESHOLD and high_momentum_declining:
            print(f"⚠️  EXAUSTÃO DE MOMENTUM (LONG): Volume caindo ({volume_decline_ratio:.2f}x) + altas em declínio")
            return True
            
    elif position_side == 'SHORT':
        # Para posições curtas, verificar se as baixas estão subindo (perda de força da queda)
        recent_lows = recent_candles['low'].values
        low_momentum_declining = len(recent_lows) >= 3 and recent_lows[-1] > recent_lows[-2] > recent_lows[-3]
        
        if volume_decline_ratio < VOLUME_DECLINE_THRESHOLD and low_momentum_declining:
            print(f"⚠️  EXAUSTÃO DE MOMENTUM (SHORT): Volume caindo ({volume_decline_ratio:.2f}x) + baixas subindo")
            return True
    
    return False

def find_enhanced_momentum_signal(market_data: pd.DataFrame) -> str:
    """
    Versão aprimorada da detecção de momentum que inclui análise de divergências.
    """
    # Primeiro aplicar a análise básica
    basic_signal = find_momentum_signal(market_data)
    
    if basic_signal == 'AGUARDAR':
        return basic_signal
    
    # Analisar divergências para confirmar ou rejeitar o sinal
    divergence_analysis = analyze_volume_price_divergence(market_data)
    
    if basic_signal == 'COMPRAR':
        # Confirmar sinal de compra se não há divergência baixista
        if divergence_analysis['bearish_divergence']:
            print(f"⚠️  Divergência baixista detectada - rejeitando sinal de COMPRA")
            return 'AGUARDAR'
        elif divergence_analysis['bullish_divergence']:
            print(f"✅ Divergência altista confirma sinal de COMPRA")
            
    elif basic_signal == 'VENDER':
        # Confirmar sinal de venda se não há divergência altista
        if divergence_analysis['bullish_divergence']:
            print(f"⚠️  Divergência altista detectada - rejeitando sinal de VENDA") 
            return 'AGUARDAR'
        elif divergence_analysis['bearish_divergence']:
            print(f"✅ Divergência baixista confirma sinal de VENDA")
    
    return basic_signal

# =============================================================================
# 4. ANÁLISE INTEGRADA AVANÇADA
# =============================================================================

def find_comprehensive_signal(market_data: pd.DataFrame) -> str:
    """
    Análise mais abrangente que combina momentum, divergências e padrões de reversão.
    """
    # 1. Análise básica de momentum com divergências
    enhanced_signal = find_enhanced_momentum_signal(market_data)
    
    if enhanced_signal == 'AGUARDAR':
        # 2. Se não há sinal claro, verificar padrões de reversão
        reversal_patterns = detect_reversal_patterns(market_data)
        volatility = calculate_volatility_score(market_data)
        
        # Só considerar padrões de reversão se a volatilidade for adequada
        if volatility > 0.02:  # Volatilidade mínima para confiar nos padrões
            if reversal_patterns['bullish_reversal']:
                print(f"🔄 Padrão de reversão ALTISTA detectado: {reversal_patterns['pattern_name']}")
                return 'COMPRAR'
            elif reversal_patterns['bearish_reversal']:
                print(f"🔄 Padrão de reversão BAIXISTA detectado: {reversal_patterns['pattern_name']}")
                return 'VENDER'
    
    # 3. Verificar se há confirmação adicional do sinal
    if enhanced_signal in ['COMPRAR', 'VENDER']:
        trend_context = analyze_trend_context(market_data)
        volatility = calculate_volatility_score(market_data)
        
        print(f"📊 Contexto: Tendência={trend_context}, Volatilidade={volatility:.4f}")
        
        # Filtrar sinais contra a tendência dominante se volatilidade for baixa
        if volatility < 0.015:  # Baixa volatilidade
            if enhanced_signal == 'COMPRAR' and trend_context == 'downtrend':
                print(f"⚠️  Sinal de COMPRA rejeitado: contra tendência de baixa em baixa volatilidade")
                return 'AGUARDAR'
            elif enhanced_signal == 'VENDER' and trend_context == 'uptrend':
                print(f"⚠️  Sinal de VENDA rejeitado: contra tendência de alta em baixa volatilidade")
                return 'AGUARDAR'
    
    return enhanced_signal

def find_comprehensive_exit_signal(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Análise avançada de saída que combina RSI, exaustão de momentum e padrões de reversão.
    """
    # 1. Análise básica de exaustão
    basic_exit = find_exhaustion_signal(market_data, position_side)
    
    if basic_exit:
        return True
    
    # 2. Verificar padrões de reversão
    reversal_patterns = detect_reversal_patterns(market_data)
    
    if position_side == 'LONG' and reversal_patterns['bearish_reversal']:
        print(f"🚪 SINAL DE SAÍDA (LONG): Padrão de reversão baixista '{reversal_patterns['pattern_name']}'")
        return True
    elif position_side == 'SHORT' and reversal_patterns['bullish_reversal']:
        print(f"🚪 SINAL DE SAÍDA (SHORT): Padrão de reversão altista '{reversal_patterns['pattern_name']}'")
        return True
    
    # 3. Análise de divergência como sinal de saída antecipado
    if len(market_data) >= 20:
        divergence_analysis = analyze_volume_price_divergence(market_data, lookback_periods=15)
        
        if position_side == 'LONG' and divergence_analysis['bearish_divergence']:
            print(f"🚪 SINAL DE SAÍDA (LONG): Divergência baixista detectada (saída antecipada)")
            return True
        elif position_side == 'SHORT' and divergence_analysis['bullish_divergence']:
            print(f"🚪 SINAL DE SAÍDA (SHORT): Divergência altista detectada (saída antecipada)")
            return True
    
    # 4. Verificação de volatilidade extrema (pode indicar reversão iminente)
    volatility = calculate_volatility_score(market_data, period=10)
    
    if volatility > 0.05:  # Volatilidade muito alta
        trend_context = analyze_trend_context(market_data, lookback=5)
        
        if position_side == 'LONG' and trend_context == 'downtrend':
            print(f"🚪 SINAL DE SAÍDA (LONG): Alta volatilidade + mudança de tendência")
            return True
        elif position_side == 'SHORT' and trend_context == 'uptrend':
            print(f"🚪 SINAL DE SAÍDA (SHORT): Alta volatilidade + mudança de tendência")
            return True
    
    return False