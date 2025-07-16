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
        # Indicadores técnicos centralizados
        RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT, RSI_WEIGHT,
        MACD_FAST, MACD_SLOW, MACD_SIGNAL, MACD_WEIGHT,
        BB_PERIOD, BB_STD, BB_WEIGHT,
        EMA_SHORT, EMA_LONG, EMA_FILTER, EMA_WEIGHT,
        
        # Parâmetros de momentum legacy
        PRICE_CHANGE_THRESHOLD, PRICE_CHANGE_PERIOD_MINUTES,
        VOLUME_MULTIPLIER_THRESHOLD, VOLUME_AVERAGE_PERIOD_MINUTES,
        RSI_OVERBOUGHT_EXIT, RSI_OVERSOLD_EXIT,
        MOMENTUM_EXHAUSTION_PERIOD, VOLUME_DECLINE_THRESHOLD,
        
        # Configurações de análise integrada
        INTEGRATED_SIGNAL_THRESHOLD_BUY, INTEGRATED_SIGNAL_THRESHOLD_SELL,
        CONFIDENCE_MULTIPLIER, HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD,
        CONSENSUS_INDICATORS_REQUIRED, MOMENTUM_CONFIRMATION_PRICE_FACTOR,
        MOMENTUM_CONFIRMATION_VOLUME_FACTOR, EXIT_CONFIDENCE_THRESHOLD,
        EXIT_CONFIRMATION_THRESHOLD, RSI_CRITICAL_STRENGTH,
        MIN_DATA_BUFFER, FALLBACK_EMA_FILTER,
        
        # Configurações de padrões e análises
        MIN_VOLATILITY_FOR_PATTERNS, TREND_CHANGE_THRESHOLD,
        DIVERGENCE_PRICE_THRESHOLD, DIVERGENCE_VOLUME_THRESHOLD,
        DIVERGENCE_LOOKBACK_PERIODS, VOLATILITY_CALCULATION_PERIOD,
        TREND_ANALYSIS_LOOKBACK,
        
        # Configurações multi-timeframe
        PRIMARY_TIMEFRAME, SECONDARY_TIMEFRAME, CONFIRMATION_TIMEFRAME
    )
except ImportError:
    # Valores padrão se não conseguir importar
    # Indicadores técnicos
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
    
    # Momentum legacy
    PRICE_CHANGE_THRESHOLD = 0.5
    PRICE_CHANGE_PERIOD_MINUTES = 3
    VOLUME_MULTIPLIER_THRESHOLD = 2.0
    VOLUME_AVERAGE_PERIOD_MINUTES = 20
    RSI_OVERBOUGHT_EXIT = 75.0
    RSI_OVERSOLD_EXIT = 25.0
    MOMENTUM_EXHAUSTION_PERIOD = 5
    VOLUME_DECLINE_THRESHOLD = 0.5
    
    # Análise integrada
    INTEGRATED_SIGNAL_THRESHOLD_BUY = 0.15
    INTEGRATED_SIGNAL_THRESHOLD_SELL = -0.15
    CONFIDENCE_MULTIPLIER = 2.0
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.5
    CONSENSUS_INDICATORS_REQUIRED = 3
    MOMENTUM_CONFIRMATION_PRICE_FACTOR = 0.3
    MOMENTUM_CONFIRMATION_VOLUME_FACTOR = 0.5
    EXIT_CONFIDENCE_THRESHOLD = 0.4
    EXIT_CONFIRMATION_THRESHOLD = 0.6
    RSI_CRITICAL_STRENGTH = 0.6
    MIN_DATA_BUFFER = 3
    FALLBACK_EMA_FILTER = 30
    
    # Padrões e análises
    MIN_VOLATILITY_FOR_PATTERNS = 0.02
    TREND_CHANGE_THRESHOLD = 0.02
    DIVERGENCE_PRICE_THRESHOLD = 0.01
    DIVERGENCE_VOLUME_THRESHOLD = 0.2
    DIVERGENCE_LOOKBACK_PERIODS = 10
    VOLATILITY_CALCULATION_PERIOD = 20
    TREND_ANALYSIS_LOOKBACK = 10
    
    # Configurações multi-timeframe
    PRIMARY_TIMEFRAME = '1m'
    SECONDARY_TIMEFRAME = '5m'
    CONFIRMATION_TIMEFRAME = '15m'

# =============================================================================
# 1. FUNÇÕES DE DEBUG E CONFIGURAÇÃO
# =============================================================================

def print_current_settings():
    """
    Imprime as configurações atuais sendo utilizadas pelo sistema de análise.
    """
    print(f"\n{'='*60}")
    print(f"⚙️  CONFIGURAÇÕES ATUAIS DO SISTEMA DE ANÁLISE")
    print(f"{'='*60}")
    
    print(f"\n📊 INDICADORES TÉCNICOS:")
    print(f"   RSI: período={RSI_PERIOD}, oversold={RSI_OVERSOLD}, overbought={RSI_OVERBOUGHT}, peso={RSI_WEIGHT}")
    print(f"   MACD: fast={MACD_FAST}, slow={MACD_SLOW}, signal={MACD_SIGNAL}, peso={MACD_WEIGHT}")
    print(f"   BB: período={BB_PERIOD}, std={BB_STD}, peso={BB_WEIGHT}")
    print(f"   EMA: short={EMA_SHORT}, long={EMA_LONG}, filter={EMA_FILTER}, peso={EMA_WEIGHT}")
    
    print(f"\n🚀 MOMENTUM LEGACY:")
    print(f"   Mudança preço: threshold={PRICE_CHANGE_THRESHOLD}%, período={PRICE_CHANGE_PERIOD_MINUTES}min")
    print(f"   Volume: multiplicador={VOLUME_MULTIPLIER_THRESHOLD}x, período médio={VOLUME_AVERAGE_PERIOD_MINUTES}min")
    print(f"   RSI saída: overbought={RSI_OVERBOUGHT_EXIT}, oversold={RSI_OVERSOLD_EXIT}")
    print(f"   Exaustão: período={MOMENTUM_EXHAUSTION_PERIOD}, queda volume={VOLUME_DECLINE_THRESHOLD}")
    
    print(f"\n🎯 ANÁLISE INTEGRADA:")
    print(f"   Thresholds: compra={INTEGRATED_SIGNAL_THRESHOLD_BUY}, venda={INTEGRATED_SIGNAL_THRESHOLD_SELL}")
    print(f"   Confiança: multiplicador={CONFIDENCE_MULTIPLIER}, alta={HIGH_CONFIDENCE_THRESHOLD}, média={MEDIUM_CONFIDENCE_THRESHOLD}")
    print(f"   Consenso: indicadores={CONSENSUS_INDICATORS_REQUIRED}/4")
    print(f"   Confirmação: preço={MOMENTUM_CONFIRMATION_PRICE_FACTOR}, volume={MOMENTUM_CONFIRMATION_VOLUME_FACTOR}")
    print(f"   Saída: threshold={EXIT_CONFIDENCE_THRESHOLD}, confirmação={EXIT_CONFIRMATION_THRESHOLD}")
    print(f"   RSI crítico: força={RSI_CRITICAL_STRENGTH}")
    print(f"   Dados: buffer={MIN_DATA_BUFFER}, EMA fallback={FALLBACK_EMA_FILTER}")
    
    print(f"\n📈 PADRÕES E ANÁLISES:")
    print(f"   Volatilidade mín: {MIN_VOLATILITY_FOR_PATTERNS}")
    print(f"   Tendência: threshold={TREND_CHANGE_THRESHOLD}, lookback={TREND_ANALYSIS_LOOKBACK}")
    print(f"   Divergência: preço={DIVERGENCE_PRICE_THRESHOLD}, volume={DIVERGENCE_VOLUME_THRESHOLD}, períodos={DIVERGENCE_LOOKBACK_PERIODS}")
    print(f"   Volatilidade: período={VOLATILITY_CALCULATION_PERIOD}")
    print(f"{'='*60}\n")

# =============================================================================
# 2. FUNÇÕES DE ANÁLISE MULTI-TIMEFRAME
# =============================================================================

def fetch_multi_timeframe_data(client, symbol: str) -> dict:
    """
    Busca dados de múltiplos timeframes para análise integrada.
    
    Returns:
        dict: {
            'primary': DataFrame,     # 1m - para sinais precisos
            'secondary': DataFrame,   # 5m - para contexto
            'confirmation': DataFrame # 15m - para filtro de tendência
        }
    """
    # Importar função de fetch aqui para evitar dependência circular
    try:
        from utils.data import fetch_data
    except ImportError:
        print("⚠️  Erro: Não foi possível importar fetch_data. Análise multi-timeframe desabilitada.")
        return None
    
    if not client:
        print("⚠️  Cliente da exchange não fornecido para análise multi-timeframe")
        return None
    
    timeframes = {
        'primary': PRIMARY_TIMEFRAME,
        'secondary': SECONDARY_TIMEFRAME, 
        'confirmation': CONFIRMATION_TIMEFRAME
    }
    
    # Limites para cada timeframe - mais dados para timeframes maiores
    limits = {
        'primary': 100,      # 1m - últimas 100 velas (1h40min)
        'secondary': 200,    # 5m - últimas 200 velas (16h40min)
        'confirmation': 300  # 15m - últimas 300 velas (75 horas)
    }
    
    multi_data = {}
    
    for tf_name, tf_interval in timeframes.items():
        try:
            data = fetch_data(client, symbol, timeframe=tf_interval, limit=limits[tf_name])
            if data is not None and len(data) > 0:
                multi_data[tf_name] = data
                print(f"✅ Dados {tf_interval} carregados: {len(data)} velas")
            else:
                print(f"⚠️  Falha ao carregar dados {tf_interval} para {symbol}")
                return None
        except Exception as e:
            print(f"❌ Erro ao buscar dados {tf_interval}: {e}")
            return None
    
    return multi_data if len(multi_data) == 3 else None

def analyze_higher_timeframe_trend(confirmation_data: pd.DataFrame) -> dict:
    """
    Analisa a tendência no timeframe de confirmação (15m) para filtrar sinais.
    
    Returns:
        dict: {
            'trend': 'BULLISH'|'BEARISH'|'SIDEWAYS',
            'strength': float (0-1),
            'price_vs_ema': 'ABOVE'|'BELOW'|'NEUTRAL',
            'ema_slope': 'UP'|'DOWN'|'FLAT',
            'support_level': float,
            'resistance_level': float
        }
    """
    if confirmation_data is None or len(confirmation_data) < EMA_FILTER + 10:
        return {
            'trend': 'SIDEWAYS',
            'strength': 0.0,
            'price_vs_ema': 'NEUTRAL',
            'ema_slope': 'FLAT',
            'support_level': 0.0,
            'resistance_level': 0.0
        }
    
    current_price = confirmation_data['close'].iloc[-1]
    
    # Calcular EMA de tendência no timeframe de confirmação
    ema_trend = confirmation_data['close'].ewm(span=EMA_FILTER).mean()
    current_ema = ema_trend.iloc[-1]
    previous_ema = ema_trend.iloc[-10]  # EMA de 10 períodos atrás
    
    # Determinar posição do preço vs EMA
    price_vs_ema_pct = (current_price - current_ema) / current_ema
    
    if price_vs_ema_pct > 0.002:  # +0.2%
        price_vs_ema = 'ABOVE'
    elif price_vs_ema_pct < -0.002:  # -0.2%
        price_vs_ema = 'BELOW'
    else:
        price_vs_ema = 'NEUTRAL'
    
    # Determinar inclinação da EMA
    ema_slope_pct = (current_ema - previous_ema) / previous_ema
    
    if ema_slope_pct > 0.001:  # +0.1%
        ema_slope = 'UP'
    elif ema_slope_pct < -0.001:  # -0.1%
        ema_slope = 'DOWN'
    else:
        ema_slope = 'FLAT'
    
    # Determinar tendência geral e força
    trend = 'SIDEWAYS'
    strength = 0.0
    
    if price_vs_ema == 'ABOVE' and ema_slope == 'UP':
        trend = 'BULLISH'
        strength = min(abs(price_vs_ema_pct) + abs(ema_slope_pct), 1.0)
    elif price_vs_ema == 'BELOW' and ema_slope == 'DOWN':
        trend = 'BEARISH'
        strength = min(abs(price_vs_ema_pct) + abs(ema_slope_pct), 1.0)
    elif price_vs_ema == 'ABOVE' or ema_slope == 'UP':
        trend = 'BULLISH'
        strength = min((abs(price_vs_ema_pct) + abs(ema_slope_pct)) * 0.5, 0.7)
    elif price_vs_ema == 'BELOW' or ema_slope == 'DOWN':
        trend = 'BEARISH'
        strength = min((abs(price_vs_ema_pct) + abs(ema_slope_pct)) * 0.5, 0.7)
    
    # Calcular níveis de suporte e resistência básicos
    recent_data = confirmation_data.iloc[-20:]  # Últimas 20 velas do timeframe de confirmação
    support_level = recent_data['low'].min()
    resistance_level = recent_data['high'].max()
    
    return {
        'trend': trend,
        'strength': strength,
        'price_vs_ema': price_vs_ema,
        'ema_slope': ema_slope,
        'support_level': support_level,
        'resistance_level': resistance_level,
        'current_ema': current_ema,
        'price_vs_ema_pct': price_vs_ema_pct,
        'ema_slope_pct': ema_slope_pct
    }

def calculate_multi_timeframe_signal(multi_data: dict) -> dict:
    """
    Análise integrada multi-timeframe que filtra sinais do timeframe primário
    com base na tendência dos timeframes superiores.
    
    Returns:
        dict: {
            'signal': 'COMPRAR'|'VENDER'|'AGUARDAR',
            'confidence': float (0-1),
            'primary_analysis': dict,
            'trend_filter': dict,
            'mta_approved': bool,
            'description': str
        }
    """
    if not multi_data or 'primary' not in multi_data:
        return {
            'signal': 'AGUARDAR',
            'confidence': 0.0,
            'primary_analysis': {},
            'trend_filter': {},
            'mta_approved': False,
            'description': 'Dados multi-timeframe insuficientes'
        }
    
    # 1. Análise no timeframe primário (1m)
    primary_analysis = calculate_integrated_signal(multi_data['primary'])
    
    # 2. Análise da tendência no timeframe de confirmação (15m)
    trend_filter = analyze_higher_timeframe_trend(multi_data['confirmation'])
    
    # 3. Análise do contexto no timeframe secundário (5m)
    secondary_analysis = calculate_integrated_signal(multi_data['secondary'])
    
    print(f"🔍 ANÁLISE MULTI-TIMEFRAME:")
    print(f"   📊 Primário ({PRIMARY_TIMEFRAME}): {primary_analysis['signal']} (conf: {primary_analysis['confidence']:.2f})")
    print(f"   📈 Secundário ({SECONDARY_TIMEFRAME}): {secondary_analysis['signal']} (conf: {secondary_analysis['confidence']:.2f})")
    print(f"   🎯 Tendência ({CONFIRMATION_TIMEFRAME}): {trend_filter['trend']} (força: {trend_filter['strength']:.2f})")
    print(f"   📍 Preço vs EMA{EMA_FILTER}: {trend_filter['price_vs_ema']} ({trend_filter['price_vs_ema_pct']:.3f}%)")
    
    # 4. Aplicar filtros multi-timeframe
    mta_approved = False
    final_signal = 'AGUARDAR'
    final_confidence = 0.0
    
    # Regras de filtro multi-timeframe
    if primary_analysis['signal'] == 'COMPRAR':
        # Para sinais de COMPRA: aceitar se tendência não for claramente bearish
        if trend_filter['trend'] in ['BULLISH', 'SIDEWAYS']:
            # Bonus se timeframe secundário também concorda
            if secondary_analysis['signal'] == 'COMPRAR':
                mta_approved = True
                final_signal = 'COMPRAR'
                final_confidence = min(primary_analysis['confidence'] * 1.2, 1.0)  # Bonus 20%
                description = f"MTA: COMPRA confirmada - Primário + Secundário + Tendência {trend_filter['trend']}"
            elif trend_filter['trend'] == 'BULLISH' and trend_filter['strength'] > 0.3:
                mta_approved = True
                final_signal = 'COMPRAR' 
                final_confidence = primary_analysis['confidence']
                description = f"MTA: COMPRA aprovada - Tendência {CONFIRMATION_TIMEFRAME} BULLISH forte"
            elif trend_filter['price_vs_ema'] == 'ABOVE':
                mta_approved = True
                final_signal = 'COMPRAR'
                final_confidence = primary_analysis['confidence'] * 0.8  # Penalidade 20%
                description = f"MTA: COMPRA aprovada - Preço acima da EMA{EMA_FILTER} no {CONFIRMATION_TIMEFRAME}"
            else:
                description = f"MTA: COMPRA rejeitada - Tendência {CONFIRMATION_TIMEFRAME} não favorável"
        else:
            description = f"MTA: COMPRA rejeitada - Tendência {CONFIRMATION_TIMEFRAME} BEARISH"
    
    elif primary_analysis['signal'] == 'VENDER':
        # Para sinais de VENDA: aceitar se tendência não for claramente bullish
        if trend_filter['trend'] in ['BEARISH', 'SIDEWAYS']:
            # Bonus se timeframe secundário também concorda
            if secondary_analysis['signal'] == 'VENDER':
                mta_approved = True
                final_signal = 'VENDER'
                final_confidence = min(primary_analysis['confidence'] * 1.2, 1.0)  # Bonus 20%
                description = f"MTA: VENDA confirmada - Primário + Secundário + Tendência {trend_filter['trend']}"
            elif trend_filter['trend'] == 'BEARISH' and trend_filter['strength'] > 0.3:
                mta_approved = True
                final_signal = 'VENDER'
                final_confidence = primary_analysis['confidence']
                description = f"MTA: VENDA aprovada - Tendência {CONFIRMATION_TIMEFRAME} BEARISH forte"
            elif trend_filter['price_vs_ema'] == 'BELOW':
                mta_approved = True
                final_signal = 'VENDER'
                final_confidence = primary_analysis['confidence'] * 0.8  # Penalidade 20%
                description = f"MTA: VENDA aprovada - Preço abaixo da EMA{EMA_FILTER} no {CONFIRMATION_TIMEFRAME}"
            else:
                description = f"MTA: VENDA rejeitada - Tendência {CONFIRMATION_TIMEFRAME} não favorável"
        else:
            description = f"MTA: VENDA rejeitada - Tendência {CONFIRMATION_TIMEFRAME} BULLISH"
    
    else:
        description = f"MTA: Sinal primário neutro - Aguardando oportunidade"
    
    print(f"   ✅ Resultado MTA: {final_signal} (aprovado: {mta_approved}) - {description}")
    
    return {
        'signal': final_signal,
        'confidence': final_confidence,
        'primary_analysis': primary_analysis,
        'secondary_analysis': secondary_analysis,
        'trend_filter': trend_filter,
        'mta_approved': mta_approved,
        'description': description
    }

# =============================================================================
# 3. FUNÇÕES DOS INDICADORES TÉCNICOS CENTRALIZADOS
# =============================================================================

def calculate_rsi(data: pd.Series, period: int = None) -> pd.Series:
    """Calcula o Índice de Força Relativa (RSI) usando configurações centralizadas."""
    if period is None:
        period = RSI_PERIOD
    
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.Series, fast: int = None, slow: int = None, signal: int = None) -> dict:
    """Calcula MACD usando configurações centralizadas."""
    if fast is None:
        fast = MACD_FAST
    if slow is None:
        slow = MACD_SLOW
    if signal is None:
        signal = MACD_SIGNAL
    
    ema_fast = data.ewm(span=fast).mean()
    ema_slow = data.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_bollinger_bands(data: pd.Series, period: int = None, std_dev: float = None) -> dict:
    """Calcula Bandas de Bollinger usando configurações centralizadas."""
    if period is None:
        period = BB_PERIOD
    if std_dev is None:
        std_dev = BB_STD
    
    sma = data.rolling(window=period).mean()
    rolling_std = data.rolling(window=period).std()
    
    upper_band = sma + (rolling_std * std_dev)
    lower_band = sma - (rolling_std * std_dev)
    
    return {
        'upper': upper_band,
        'middle': sma,
        'lower': lower_band
    }

def calculate_ema(data: pd.Series, short: int = None, long: int = None, filter_period: int = None) -> dict:
    """Calcula EMAs usando configurações centralizadas."""
    if short is None:
        short = EMA_SHORT
    if long is None:
        long = EMA_LONG
    if filter_period is None:
        filter_period = EMA_FILTER
    
    ema_short = data.ewm(span=short).mean()
    ema_long = data.ewm(span=long).mean()
    ema_filter = data.ewm(span=filter_period).mean()
    
    return {
        'ema_short': ema_short,
        'ema_long': ema_long,
        'ema_filter': ema_filter
    }

def analyze_rsi_signal(rsi_value: float) -> dict:
    """Analisa sinal do RSI baseado nas configurações centralizadas."""
    if np.isnan(rsi_value):
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'RSI inválido'}
    
    if rsi_value <= RSI_OVERSOLD:
        strength = (RSI_OVERSOLD - rsi_value) / RSI_OVERSOLD
        return {
            'signal': 'COMPRAR',
            'strength': min(strength, 1.0),
            'description': f'RSI sobrevendido ({rsi_value:.1f})'
        }
    elif rsi_value >= RSI_OVERBOUGHT:
        strength = (rsi_value - RSI_OVERBOUGHT) / (100 - RSI_OVERBOUGHT)
        return {
            'signal': 'VENDER',
            'strength': min(strength, 1.0),
            'description': f'RSI sobrecomprado ({rsi_value:.1f})'
        }
    else:
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': f'RSI neutro ({rsi_value:.1f})'}

def analyze_macd_signal(macd_data: dict) -> dict:
    """Analisa sinal do MACD."""
    if len(macd_data['macd']) < 2:
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'Dados insuficientes para MACD'}
    
    current_macd = macd_data['macd'].iloc[-1]
    current_signal = macd_data['signal'].iloc[-1]
    previous_macd = macd_data['macd'].iloc[-2]
    previous_signal = macd_data['signal'].iloc[-2]
    histogram = macd_data['histogram'].iloc[-1]
    
    # Cruzamento de alta: MACD cruza acima da linha de sinal
    if previous_macd <= previous_signal and current_macd > current_signal:
        strength = min(abs(histogram) / abs(current_macd) if current_macd != 0 else 0, 1.0)
        return {
            'signal': 'COMPRAR',
            'strength': strength,
            'description': 'MACD cruzou acima da linha de sinal'
        }
    
    # Cruzamento de baixa: MACD cruza abaixo da linha de sinal
    elif previous_macd >= previous_signal and current_macd < current_signal:
        strength = min(abs(histogram) / abs(current_macd) if current_macd != 0 else 0, 1.0)
        return {
            'signal': 'VENDER',
            'strength': strength,
            'description': 'MACD cruzou abaixo da linha de sinal'
        }
    
    # Histograma crescente/decrescente
    elif histogram > 0:
        strength = min(histogram / abs(current_macd) if current_macd != 0 else 0, 0.5)
        return {
            'signal': 'COMPRAR',
            'strength': strength,
            'description': f'MACD histograma positivo ({histogram:.4f})'
        }
    elif histogram < 0:
        strength = min(abs(histogram) / abs(current_macd) if current_macd != 0 else 0, 0.5)
        return {
            'signal': 'VENDER',
            'strength': strength,
            'description': f'MACD histograma negativo ({histogram:.4f})'
        }
    
    return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'MACD neutro'}

def analyze_bollinger_signal(current_price: float, bb_data: dict) -> dict:
    """Analisa sinal das Bandas de Bollinger."""
    if np.isnan(current_price) or len(bb_data['upper']) == 0:
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'Dados insuficientes para Bollinger'}
    
    upper = bb_data['upper'].iloc[-1]
    middle = bb_data['middle'].iloc[-1]
    lower = bb_data['lower'].iloc[-1]
    
    if np.isnan(upper) or np.isnan(middle) or np.isnan(lower):
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'Bollinger Bands inválidas'}
    
    band_width = upper - lower
    
    # Preço próximo à banda inferior (oversold)
    if current_price <= lower:
        distance_ratio = (lower - current_price) / band_width if band_width > 0 else 0
        return {
            'signal': 'COMPRAR',
            'strength': min(distance_ratio * 2, 1.0),
            'description': f'Preço na banda inferior ({current_price:.4f} <= {lower:.4f})'
        }
    
    # Preço próximo à banda superior (overbought)
    elif current_price >= upper:
        distance_ratio = (current_price - upper) / band_width if band_width > 0 else 0
        return {
            'signal': 'VENDER',
            'strength': min(distance_ratio * 2, 1.0),
            'description': f'Preço na banda superior ({current_price:.4f} >= {upper:.4f})'
        }
    
    # Preço cruzando a média móvel
    elif abs(current_price - middle) / band_width < 0.1:  # Próximo da média
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': f'Preço próximo da média ({current_price:.4f} ≈ {middle:.4f})'}
    
    return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'Bollinger neutro'}

def analyze_ema_signal(current_price: float, ema_data: dict) -> dict:
    """Analisa sinal das EMAs."""
    if np.isnan(current_price) or len(ema_data['ema_short']) < 2:
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'Dados insuficientes para EMA'}
    
    ema_short_current = ema_data['ema_short'].iloc[-1]
    ema_long_current = ema_data['ema_long'].iloc[-1]
    ema_filter_current = ema_data['ema_filter'].iloc[-1]
    
    ema_short_previous = ema_data['ema_short'].iloc[-2]
    ema_long_previous = ema_data['ema_long'].iloc[-2]
    
    if any(np.isnan([ema_short_current, ema_long_current, ema_filter_current])):
        return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'EMAs inválidas'}
    
    # Cruzamento dourado: EMA curta cruza acima da EMA longa
    if ema_short_previous <= ema_long_previous and ema_short_current > ema_long_current:
        # Confirmar com filtro de tendência
        if current_price > ema_filter_current:
            strength = min((ema_short_current - ema_long_current) / ema_long_current, 1.0)
            return {
                'signal': 'COMPRAR',
                'strength': abs(strength),
                'description': f'Cruzamento dourado confirmado (EMA{EMA_SHORT} > EMA{EMA_LONG} > EMA{EMA_FILTER})'
            }
    
    # Cruzamento da morte: EMA curta cruza abaixo da EMA longa
    elif ema_short_previous >= ema_long_previous and ema_short_current < ema_long_current:
        # Confirmar com filtro de tendência
        if current_price < ema_filter_current:
            strength = min((ema_long_current - ema_short_current) / ema_long_current, 1.0)
            return {
                'signal': 'VENDER',
                'strength': abs(strength),
                'description': f'Cruzamento da morte confirmado (EMA{EMA_SHORT} < EMA{EMA_LONG} < EMA{EMA_FILTER})'
            }
    
    # Sinal baseado em posição relativa das EMAs
    if ema_short_current > ema_long_current > ema_filter_current:
        strength = min((ema_short_current - ema_long_current) / ema_long_current * 0.5, 0.5)
        return {
            'signal': 'COMPRAR',
            'strength': abs(strength),
            'description': f'Tendência de alta (EMA{EMA_SHORT} > EMA{EMA_LONG} > EMA{EMA_FILTER})'
        }
    elif ema_short_current < ema_long_current < ema_filter_current:
        strength = min((ema_long_current - ema_short_current) / ema_long_current * 0.5, 0.5)
        return {
            'signal': 'VENDER',
            'strength': abs(strength),
            'description': f'Tendência de baixa (EMA{EMA_SHORT} < EMA{EMA_LONG} < EMA{EMA_FILTER})'
        }
    
    return {'signal': 'NEUTRO', 'strength': 0.0, 'description': 'EMAs neutras'}

def calculate_integrated_signal(market_data: pd.DataFrame) -> dict:
    """
    Calcula sinal integrado usando os 4 indicadores técnicos com seus pesos configurados.
    
    Returns:
        dict: {
            'signal': 'COMPRAR'|'VENDER'|'NEUTRO',
            'confidence': float (0-1),
            'indicators': dict,
            'weighted_score': float
        }
    """
    # Requisito mínimo mais flexível - reduzir para funcionar com menos dados
    # Requisito mínimo configurável através de settings
    min_required = max(RSI_PERIOD, MACD_SLOW, BB_PERIOD, FALLBACK_EMA_FILTER) + MIN_DATA_BUFFER
    
    if market_data is None or len(market_data) < min_required:
        return {
            'signal': 'NEUTRO',
            'confidence': 0.0,
            'indicators': {},
            'weighted_score': 0.0,
            'description': f'Dados insuficientes para análise integrada (mín. {min_required}, atual: {len(market_data) if market_data is not None else 0})'
        }
    
    current_price = market_data['close'].iloc[-1]
    
    # 1. Calcular todos os indicadores
    rsi_values = calculate_rsi(market_data['close'])
    macd_data = calculate_macd(market_data['close'])
    bb_data = calculate_bollinger_bands(market_data['close'])
    ema_data = calculate_ema(market_data['close'])
    
    # 2. Analisar sinais individuais
    rsi_signal = analyze_rsi_signal(rsi_values.iloc[-1])
    macd_signal = analyze_macd_signal(macd_data)
    bb_signal = analyze_bollinger_signal(current_price, bb_data)
    ema_signal = analyze_ema_signal(current_price, ema_data)
    
    # 3. Calcular score ponderado
    signal_weights = {
        'RSI': RSI_WEIGHT,
        'MACD': MACD_WEIGHT,
        'BB': BB_WEIGHT,
        'EMA': EMA_WEIGHT
    }
    
    signals = {
        'RSI': rsi_signal,
        'MACD': macd_signal,
        'BB': bb_signal,
        'EMA': ema_signal
    }
    
    weighted_score = 0.0
    total_weight = 0.0
    
    for indicator, signal_data in signals.items():
        weight = signal_weights[indicator]
        strength = signal_data['strength']
        
        if signal_data['signal'] == 'COMPRAR':
            weighted_score += weight * strength
        elif signal_data['signal'] == 'VENDER':
            weighted_score -= weight * strength
        
        total_weight += weight
    
    # 4. Determinar sinal final - Thresholds configuráveis
    if weighted_score > INTEGRATED_SIGNAL_THRESHOLD_BUY:
        final_signal = 'COMPRAR'
        confidence = min(weighted_score * CONFIDENCE_MULTIPLIER, 1.0)
    elif weighted_score < INTEGRATED_SIGNAL_THRESHOLD_SELL:
        final_signal = 'VENDER'
        confidence = min(abs(weighted_score) * CONFIDENCE_MULTIPLIER, 1.0)
    else:
        final_signal = 'NEUTRO'
        confidence = 0.0
    
    # 5. Criar descrição detalhada
    indicator_descriptions = []
    for indicator, signal_data in signals.items():
        if signal_data['signal'] != 'NEUTRO':
            indicator_descriptions.append(f"{indicator}: {signal_data['description']}")
    
    # DEBUG: Mostrar detalhes dos indicadores
    debug_details = []
    for indicator, signal_data in signals.items():
        debug_details.append(f"{indicator}={signal_data['signal']}({signal_data['strength']:.2f})")
    
    description = f"Score: {weighted_score:.3f} | " + " | ".join(indicator_descriptions)
    debug_description = f"[{' | '.join(debug_details)}] -> {description}"
    
    return {
        'signal': final_signal,
        'confidence': confidence,
        'indicators': signals,
        'weighted_score': weighted_score,
        'description': description,
        'debug_description': debug_description,
        'weights_used': signal_weights
    }

# =============================================================================
# 3. FUNÇÕES AUXILIARES DE ANÁLISE COMPLEMENTARES
# =============================================================================

def analyze_volume_price_divergence(market_data: pd.DataFrame, lookback_periods: int = None) -> dict:
    """
    Análise clássica de divergência entre preço e osciladores (RSI).
    Procura por:
    - Divergência Baixista: Topos mais altos no preço + Topos mais baixos no RSI
    - Divergência Altista: Fundos mais baixos no preço + Fundos mais altos no RSI
    
    Returns:
        dict: {
            'bullish_divergence': bool,
            'bearish_divergence': bool, 
            'strength': float,
            'price_peaks': list,
            'rsi_peaks': list,
            'price_troughs': list,
            'rsi_troughs': list
        }
    """
    if lookback_periods is None:
        lookback_periods = DIVERGENCE_LOOKBACK_PERIODS
        
    if len(market_data) < lookback_periods + RSI_PERIOD + 5:
        return {
            'bullish_divergence': False, 
            'bearish_divergence': False, 
            'strength': 0,
            'price_peaks': [],
            'rsi_peaks': [],
            'price_troughs': [],
            'rsi_troughs': []
        }
    
    # Calcular RSI para análise de divergência
    rsi_values = calculate_rsi(market_data['close'])
    
    # Usar dados recentes para análise
    recent_data = market_data.iloc[-lookback_periods:].copy()
    recent_rsi = rsi_values.iloc[-lookback_periods:]
    
    # Identificar picos (topos) e vales (fundos) no preço
    price_peaks = []
    price_troughs = []
    rsi_peaks = []
    rsi_troughs = []
    
    # Buscar picos e vales com janela mínima de 3 períodos
    for i in range(2, len(recent_data) - 2):
        price = recent_data['close'].iloc[i]
        rsi = recent_rsi.iloc[i]
        
        # Identificar picos (topos)
        if (price > recent_data['close'].iloc[i-1] and 
            price > recent_data['close'].iloc[i-2] and
            price > recent_data['close'].iloc[i+1] and 
            price > recent_data['close'].iloc[i+2]):
            price_peaks.append((i, price))
            rsi_peaks.append((i, rsi))
        
        # Identificar vales (fundos)
        if (price < recent_data['close'].iloc[i-1] and 
            price < recent_data['close'].iloc[i-2] and
            price < recent_data['close'].iloc[i+1] and 
            price < recent_data['close'].iloc[i+2]):
            price_troughs.append((i, price))
            rsi_troughs.append((i, rsi))
    
    bullish_divergence = False
    bearish_divergence = False
    strength = 0.0
    
    # Análise de Divergência Baixista (Bearish)
    # Preço fazendo topos mais altos, RSI fazendo topos mais baixos
    if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
        # Pegar os dois últimos picos
        last_price_peak = price_peaks[-1][1]
        prev_price_peak = price_peaks[-2][1]
        last_rsi_peak = rsi_peaks[-1][1] 
        prev_rsi_peak = rsi_peaks[-2][1]
        
        # Divergência baixista: preço subindo, RSI descendo
        if (last_price_peak > prev_price_peak and 
            last_rsi_peak < prev_rsi_peak):
            price_change_pct = (last_price_peak - prev_price_peak) / prev_price_peak
            rsi_change = prev_rsi_peak - last_rsi_peak
            
            # Verificar se as diferenças são significativas
            if price_change_pct > DIVERGENCE_PRICE_THRESHOLD and rsi_change > 5:
                bearish_divergence = True
                strength = min((price_change_pct + rsi_change/100) / 2, 1.0)
                print(f"🔴 DIVERGÊNCIA BAIXISTA: Preço +{price_change_pct:.2%}, RSI -{rsi_change:.1f}")
    
    # Análise de Divergência Altista (Bullish)
    # Preço fazendo fundos mais baixos, RSI fazendo fundos mais altos
    if len(price_troughs) >= 2 and len(rsi_troughs) >= 2:
        # Pegar os dois últimos vales
        last_price_trough = price_troughs[-1][1]
        prev_price_trough = price_troughs[-2][1]
        last_rsi_trough = rsi_troughs[-1][1]
        prev_rsi_trough = rsi_troughs[-2][1]
        
        # Divergência altista: preço descendo, RSI subindo
        if (last_price_trough < prev_price_trough and 
            last_rsi_trough > prev_rsi_trough):
            price_change_pct = (prev_price_trough - last_price_trough) / prev_price_trough
            rsi_change = last_rsi_trough - prev_rsi_trough
            
            # Verificar se as diferenças são significativas
            if price_change_pct > DIVERGENCE_PRICE_THRESHOLD and rsi_change > 5:
                bullish_divergence = True
                strength = min((price_change_pct + rsi_change/100) / 2, 1.0)
                print(f"🟢 DIVERGÊNCIA ALTISTA: Preço -{price_change_pct:.2%}, RSI +{rsi_change:.1f}")
    
    return {
        'bullish_divergence': bullish_divergence,
        'bearish_divergence': bearish_divergence,
        'strength': strength,
        'price_peaks': price_peaks,
        'rsi_peaks': rsi_peaks,
        'price_troughs': price_troughs,
        'rsi_troughs': rsi_troughs,
        'total_peaks': len(price_peaks),
        'total_troughs': len(price_troughs)
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

def analyze_trend_context(market_data: pd.DataFrame, lookback: int = None) -> str:
    """Analisa o contexto de tendência para os últimos períodos"""
    if lookback is None:
        lookback = TREND_ANALYSIS_LOOKBACK
        
    if len(market_data) < lookback:
        return 'sideways'
    
    recent_data = market_data.iloc[-lookback:]
    first_close = recent_data['close'].iloc[0]
    last_close = recent_data['close'].iloc[-1]
    
    trend_change = (last_close - first_close) / first_close
    
    if trend_change > TREND_CHANGE_THRESHOLD:  # Configurável via settings
        return 'uptrend'
    elif trend_change < -TREND_CHANGE_THRESHOLD:  # Configurável via settings
        return 'downtrend'
    else:
        return 'sideways'

def calculate_volatility_score(market_data: pd.DataFrame, period: int = None) -> float:
    """
    Calcula uma pontuação de volatilidade baseada no desvio padrão dos retornos.
    """
    if period is None:
        period = VOLATILITY_CALCULATION_PERIOD
        
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

# =============================================================================
# 5. FUNÇÕES PRINCIPAIS DE SINALIZAÇÃO - COM ANÁLISE MULTI-TIMEFRAME
# =============================================================================

def find_integrated_momentum_signal_mta(client, symbol: str, market_data: pd.DataFrame = None) -> str:
    """
    Versão Multi-TimeFrame (MTA) da análise integrada.
    Combina análise técnica dos 4 indicadores com filtros de tendência multi-timeframe.
    
    Args:
        client: Cliente da exchange para buscar dados de múltiplos timeframes
        symbol: Símbolo do ativo
        market_data: Dados do timeframe primário (opcional, será buscado se não fornecido)
    
    Returns:
        str: 'COMPRAR'|'VENDER'|'AGUARDAR'
    """
    # 1. Buscar dados multi-timeframe
    if client:
        print(f"🔍 INICIANDO ANÁLISE MULTI-TIMEFRAME para {symbol}")
        multi_data = fetch_multi_timeframe_data(client, symbol)
        
        if multi_data:
            # Usar análise multi-timeframe completa
            mta_result = calculate_multi_timeframe_signal(multi_data)
            
            if mta_result['mta_approved']:
                print(f"✅ MTA APROVADO: {mta_result['signal']} | "
                      f"Confiança: {mta_result['confidence']:.2f} | "
                      f"{mta_result['description']}")
                return mta_result['signal']
            else:
                print(f"❌ MTA REJEITADO: {mta_result['description']}")
                return 'AGUARDAR'
        else:
            print(f"⚠️  Falha na coleta multi-timeframe. Usando análise single-timeframe de fallback.")
    else:
        print(f"⚠️  Cliente não fornecido. Usando análise single-timeframe.")
    
    # 2. Fallback para análise single-timeframe se MTA falhar
    if market_data is not None:
        return find_integrated_momentum_signal_legacy(market_data)
    else:
        print(f"❌ Dados insuficientes para análise de {symbol}")
        return 'AGUARDAR'

def find_integrated_momentum_signal_legacy(market_data: pd.DataFrame) -> str:
    """
    Versão original da análise integrada (mantida para compatibilidade e fallback).
    """
    # 1. Análise técnica integrada usando os 4 indicadores
    integrated_analysis = calculate_integrated_signal(market_data)
    
    # DEBUG: Sempre mostrar resultado da análise integrada
    print(f"🔍 ANÁLISE INTEGRADA (LEGACY): {integrated_analysis['signal']} | "
          f"Score={integrated_analysis['weighted_score']:.3f} | "
          f"Confiança={integrated_analysis['confidence']:.2f}")
    
    # DEBUG: Mostrar detalhes dos indicadores se disponível
    if 'debug_description' in integrated_analysis:
        print(f"   ➤ Detalhes: {integrated_analysis['debug_description']}")
    
    # Se há dados insuficientes, usar fallback diretamente
    if 'Dados insuficientes' in integrated_analysis.get('description', ''):
        print(f"⚠️  {integrated_analysis['description']}")
        momentum_signal = find_momentum_signal_legacy(market_data)
        if momentum_signal != 'AGUARDAR':
            print(f"📈 FALLBACK: Usando sinal de momentum tradicional - {momentum_signal}")
            return momentum_signal
        return 'AGUARDAR'
    
    # 2. Se há sinal claro nos indicadores técnicos, confirmar com momentum
    if integrated_analysis['signal'] != 'NEUTRO':
        momentum_confirmation = analyze_momentum_confirmation(market_data, integrated_analysis['signal'])
        
        if momentum_confirmation:
            print(f"✅ SINAL INTEGRADO ({integrated_analysis['signal']}): "
                  f"Confiança={integrated_analysis['confidence']:.2f} | "
                  f"{integrated_analysis['description']}")
            return integrated_analysis['signal']
        else:
            # Se confiança for muito alta, aceitar mesmo sem confirmação de momentum
            if integrated_analysis['confidence'] >= HIGH_CONFIDENCE_THRESHOLD:
                print(f"✅ SINAL INTEGRADO DE ALTA CONFIANÇA ({integrated_analysis['signal']}): "
                      f"Confiança={integrated_analysis['confidence']:.2f} | "
                      f"{integrated_analysis['description']}")
                return integrated_analysis['signal']
            # Se confiança for moderada mas todos indicadores apontam na mesma direção
            elif integrated_analysis['confidence'] >= MEDIUM_CONFIDENCE_THRESHOLD:
                # Contar quantos indicadores concordam
                signals_list = [data['signal'] for data in integrated_analysis['indicators'].values()]
                target_signal = integrated_analysis['signal']
                agreement_count = sum(1 for s in signals_list if s == target_signal)
                
                if agreement_count >= CONSENSUS_INDICATORS_REQUIRED:
                    print(f"✅ SINAL INTEGRADO POR CONSENSO ({integrated_analysis['signal']}): "
                          f"Confiança={integrated_analysis['confidence']:.2f} | "
                          f"{agreement_count}/4 indicadores concordam")
                    return integrated_analysis['signal']
                else:
                    print(f"⚠️  Sinal técnico {integrated_analysis['signal']} rejeitado: falta consenso "
                          f"({agreement_count}/4 indicadores) e confirmação de momentum")
            else:
                print(f"⚠️  Sinal técnico {integrated_analysis['signal']} rejeitado por falta de confirmação de momentum "
                      f"(confiança: {integrated_analysis['confidence']:.2f})")
    
    # 3. Se não há sinal claro nos indicadores técnicos OU sinal foi rejeitado, usar análise de momentum tradicional
    momentum_signal = find_momentum_signal_legacy(market_data)
    if momentum_signal != 'AGUARDAR':
        print(f"📈 FALLBACK: Usando sinal de momentum tradicional - {momentum_signal}")
        return momentum_signal
    
    return 'AGUARDAR'

def find_integrated_momentum_signal(market_data: pd.DataFrame) -> str:
    """
    Função principal de análise - agora redireciona para a versão legacy para compatibilidade.
    Para usar análise multi-timeframe, use find_integrated_momentum_signal_mta().
    
    AVISO: Esta função sempre usa análise single-timeframe.
    Para análise multi-timeframe, use find_integrated_momentum_signal_mta(client, symbol, market_data)
    """
    print("⚠️  USANDO ANÁLISE SINGLE-TIMEFRAME (LEGACY) - Para MTA, use find_integrated_momentum_signal_mta()")
    return find_integrated_momentum_signal_legacy(market_data)

def find_momentum_signal_legacy(market_data: pd.DataFrame) -> str:
    """
    Análise de momentum tradicional (mantida para compatibilidade e backup).
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
    
    if average_volume == 0 or np.isnan(average_volume):
        volume_multiplier = 999.99  # Valor alto mas finito para representar volume muito acima da média
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
    
    print(f"Análise de MOMENTUM LEGACY: Variação Preço={price_change_pct:.2f}%, Vol. Multiplicador={volume_multiplier:.2f}x, Tendência Recente={recent_price_trend}")

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

def analyze_momentum_confirmation(market_data: pd.DataFrame, signal: str) -> bool:
    """
    Confirma sinal técnico com análise de momentum e volume.
    """
    if len(market_data) < max(PRICE_CHANGE_PERIOD_MINUTES, VOLUME_AVERAGE_PERIOD_MINUTES) + 1:
        return False
    
    latest_candle = market_data.iloc[-1]
    current_price = latest_candle['close']
    current_volume = latest_candle['volume']
    
    # Calcular mudança de preço
    price_N_periods_ago = market_data['close'].iloc[-1 - PRICE_CHANGE_PERIOD_MINUTES]
    if price_N_periods_ago == 0:
        return False
    
    price_change_pct = ((current_price / price_N_periods_ago) - 1) * 100
    
    # Calcular volume com tratamento para casos extremos
    previous_candles = market_data.iloc[-1 - VOLUME_AVERAGE_PERIOD_MINUTES:-1]
    average_volume = previous_candles['volume'].mean()
    
    if average_volume == 0 or np.isnan(average_volume):
        # Se volume médio é zero, aceitar qualquer volume atual > 0 como positivo
        volume_multiplier = 999.99 if current_volume > 0 else 0
    else:
        volume_multiplier = current_volume / average_volume
    
    print(f"🔍 CONFIRMAÇÃO DE MOMENTUM: Sinal={signal}, Preço={price_change_pct:.2f}%, Volume={volume_multiplier:.2f}x")
    
    # Confirmação para sinais de COMPRA - Critérios mais flexíveis
    if signal == 'COMPRAR':
        momentum_ok = price_change_pct >= PRICE_CHANGE_THRESHOLD * 0.3  # Reduzido de 50% para 30%
        volume_ok = volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD * 0.5  # Reduzido de 70% para 50%
        confirmation = momentum_ok and volume_ok
        print(f"   ➤ COMPRA: Momentum OK={momentum_ok} ({price_change_pct:.2f}% >= {PRICE_CHANGE_THRESHOLD * 0.3:.2f}%), "
              f"Volume OK={volume_ok} ({volume_multiplier:.2f}x >= {VOLUME_MULTIPLIER_THRESHOLD * 0.5:.2f}x)")
        return confirmation
    
    # Confirmação para sinais de VENDA - Critérios mais flexíveis
    elif signal == 'VENDER':
        momentum_ok = price_change_pct <= -PRICE_CHANGE_THRESHOLD * 0.3  # Reduzido de 50% para 30%
        volume_ok = volume_multiplier >= VOLUME_MULTIPLIER_THRESHOLD * 0.5  # Reduzido de 70% para 50%
        confirmation = momentum_ok and volume_ok
        print(f"   ➤ VENDA: Momentum OK={momentum_ok} ({price_change_pct:.2f}% <= {-PRICE_CHANGE_THRESHOLD * 0.3:.2f}%), "
              f"Volume OK={volume_ok} ({volume_multiplier:.2f}x >= {VOLUME_MULTIPLIER_THRESHOLD * 0.5:.2f}x)")
        return confirmation
    
    return False

# Alias para compatibilidade com código existente
def find_momentum_signal(market_data: pd.DataFrame) -> str:
    """
    Função principal de análise que usa a versão integrada com os 4 indicadores.
    """
    return find_integrated_momentum_signal(market_data)

def find_integrated_exhaustion_signal_mta(client, symbol: str, position_side: str, market_data: pd.DataFrame = None) -> bool:
    """
    Análise de saída multi-timeframe que considera a tendência dos timeframes superiores.
    
    Args:
        client: Cliente da exchange
        symbol: Símbolo do ativo  
        position_side: 'LONG' ou 'SHORT'
        market_data: Dados do timeframe primário (opcional)
    
    Returns:
        bool: True se deve sair da posição
    """
    # 1. Buscar dados multi-timeframe
    if client:
        print(f"🚪 ANÁLISE DE SAÍDA MULTI-TIMEFRAME ({position_side}) para {symbol}")
        multi_data = fetch_multi_timeframe_data(client, symbol)
        
        if multi_data:
            # Análise de saída no timeframe primário
            primary_exit = find_integrated_exhaustion_signal_legacy(multi_data['primary'], position_side)
            
            # Análise da tendência no timeframe de confirmação
            trend_filter = analyze_higher_timeframe_trend(multi_data['confirmation'])
            
            print(f"   📊 Saída Primária ({PRIMARY_TIMEFRAME}): {primary_exit}")
            print(f"   🎯 Tendência ({CONFIRMATION_TIMEFRAME}): {trend_filter['trend']} (força: {trend_filter['strength']:.2f})")
            
            # Aplicar filtros de saída multi-timeframe
            if primary_exit:
                # Se análise primária sugere saída, verificar se é confirmada pela tendência
                if position_side == 'LONG':
                    # Para LONG: confirmar saída se tendência virou bearish ou está enfraquecendo
                    if (trend_filter['trend'] == 'BEARISH' or 
                        trend_filter['price_vs_ema'] == 'BELOW' or
                        trend_filter['ema_slope'] == 'DOWN'):
                        print(f"✅ SAÍDA MTA CONFIRMADA (LONG): Tendência {CONFIRMATION_TIMEFRAME} desfavorável")
                        return True
                    else:
                        print(f"⚠️  SAÍDA MTA PARCIAL (LONG): Aguardando confirmação de tendência")
                        return trend_filter['strength'] < 0.3  # Sair se tendência fraca
                
                elif position_side == 'SHORT':
                    # Para SHORT: confirmar saída se tendência virou bullish ou está fortalecendo
                    if (trend_filter['trend'] == 'BULLISH' or 
                        trend_filter['price_vs_ema'] == 'ABOVE' or
                        trend_filter['ema_slope'] == 'UP'):
                        print(f"✅ SAÍDA MTA CONFIRMADA (SHORT): Tendência {CONFIRMATION_TIMEFRAME} desfavorável")
                        return True
                    else:
                        print(f"⚠️  SAÍDA MTA PARCIAL (SHORT): Aguardando confirmação de tendência")
                        return trend_filter['strength'] < 0.3  # Sair se tendência fraca
            
            # Se não há sinal de saída primário, verificar se tendência mudou drasticamente
            elif trend_filter['strength'] > 0.6:  # Tendência muito forte contra a posição
                if ((position_side == 'LONG' and trend_filter['trend'] == 'BEARISH') or
                    (position_side == 'SHORT' and trend_filter['trend'] == 'BULLISH')):
                    print(f"🚨 SAÍDA MTA POR MUDANÇA DE TENDÊNCIA: {trend_filter['trend']} forte no {CONFIRMATION_TIMEFRAME}")
                    return True
            
            return False
        else:
            print(f"⚠️  Falha na coleta multi-timeframe para saída. Usando análise single-timeframe.")
    
    # 2. Fallback para análise single-timeframe
    if market_data is not None:
        return find_integrated_exhaustion_signal_legacy(market_data, position_side)
    else:
        print(f"❌ Dados insuficientes para análise de saída de {symbol}")
        return False

def find_integrated_exhaustion_signal_legacy(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Análise integrada de saída usando os 4 indicadores técnicos centralizados (versão original).
    """
    # 1. Análise técnica integrada
    integrated_analysis = calculate_integrated_signal(market_data)
    
    # DEBUG: Mostrar análise de saída
    print(f"🚪 ANÁLISE DE SAÍDA INTEGRADA LEGACY ({position_side}): {integrated_analysis['signal']} | "
          f"Score={integrated_analysis['weighted_score']:.3f} | "
          f"Confiança={integrated_analysis['confidence']:.2f}")
    
    # 2. Verificar se o sinal integrado sugere saída - Critérios mais flexíveis
    signal_suggests_exit = False
    
    if position_side == 'LONG':
        # Sair de posição longa se sinal técnico for de VENDA com confiança moderada
        if integrated_analysis['signal'] == 'VENDER' and integrated_analysis['confidence'] >= EXIT_CONFIDENCE_THRESHOLD:
            print(f"🚪 SINAL DE SAÍDA INTEGRADO (LONG): Indicadores técnicos sugerem VENDA "
                  f"(confiança: {integrated_analysis['confidence']:.2f})")
            signal_suggests_exit = True
    
    elif position_side == 'SHORT':
        # Sair de posição curta se sinal técnico for de COMPRA com confiança moderada
        if integrated_analysis['signal'] == 'COMPRAR' and integrated_analysis['confidence'] >= EXIT_CONFIDENCE_THRESHOLD:
            print(f"🚪 SINAL DE SAÍDA INTEGRADO (SHORT): Indicadores técnicos sugerem COMPRA "
                  f"(confiança: {integrated_analysis['confidence']:.2f})")
            signal_suggests_exit = True
    
    # 3. Se análise integrada sugere saída, confirmar com momentum
    if signal_suggests_exit:
        momentum_confirms_exit = detect_momentum_exhaustion(market_data, position_side)
        if momentum_confirms_exit:
            print(f"✅ SAÍDA CONFIRMADA: Indicadores técnicos + momentum de exaustão")
            return True
        else:
            print(f"⚠️  Saída parcialmente confirmada: Aguardando confirmação de momentum")
            # Considera saída com confiança moderada também
            return integrated_analysis['confidence'] >= EXIT_CONFIRMATION_THRESHOLD
    
    # 4. Verificar condições individuais de indicadores críticos - Mais flexível
    indicators = integrated_analysis['indicators']
    
    # RSI crítico - Reduzir threshold
    if position_side == 'LONG':
        rsi_critical = (indicators.get('RSI', {}).get('signal') == 'VENDER' and 
                       indicators.get('RSI', {}).get('strength', 0) >= RSI_CRITICAL_STRENGTH)
        if rsi_critical:
            print(f"🚪 SINAL DE SAÍDA (LONG): RSI crítico - {indicators['RSI']['description']}")
            return True
    
    elif position_side == 'SHORT':
        rsi_critical = (indicators.get('RSI', {}).get('signal') == 'COMPRAR' and 
                       indicators.get('RSI', {}).get('strength', 0) >= RSI_CRITICAL_STRENGTH)
        if rsi_critical:
            print(f"🚪 SINAL DE SAÍDA (SHORT): RSI crítico - {indicators['RSI']['description']}")
            return True
    
    # 5. Fallback para análise de exaustão tradicional
    return find_exhaustion_signal_legacy(market_data, position_side)

def find_integrated_exhaustion_signal(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Função principal de análise de saída - agora redireciona para a versão legacy para compatibilidade.
    Para usar análise multi-timeframe, use find_integrated_exhaustion_signal_mta().
    """
    return find_integrated_exhaustion_signal_legacy(market_data, position_side)

def find_exhaustion_signal_legacy(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Análise de exaustão tradicional (mantida para compatibilidade e backup).
    """
    if market_data is None or len(market_data) < RSI_PERIOD + 1:
        print("Dados insuficientes para análise de saída. Mantendo posição.")
        return False

    # 1. Calcular o RSI
    market_data = market_data.copy()  # Evitar warning de modificação
    market_data['rsi'] = calculate_rsi(market_data['close'], RSI_PERIOD)
    current_rsi = market_data['rsi'].iloc[-1]
    
    if np.isnan(current_rsi):
        return False

    # 2. Verificar exaustão de momentum
    momentum_exhausted = detect_momentum_exhaustion(market_data, position_side)

    print(f"Análise de SAÍDA LEGACY ({position_side}): RSI={current_rsi:.2f}, Momentum Exausto={momentum_exhausted}")

    # 3. Lógica de Decisão de Saída Tradicional
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

# Alias para compatibilidade com código existente
def find_exhaustion_signal(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Função principal de análise de saída - agora redireciona para a versão integrada.
    Para usar análise multi-timeframe, use find_integrated_exhaustion_signal_mta().
    """
    return find_integrated_exhaustion_signal_legacy(market_data, position_side)

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
    Versão aprimorada da detecção de momentum que utiliza análise integrada.
    Mantida para compatibilidade, mas agora usa a análise integrada como base.
    """
    return find_integrated_momentum_signal(market_data)

def find_comprehensive_signal(market_data: pd.DataFrame, client=None, symbol: str = None) -> str:
    """
    Análise mais abrangente que combina a análise integrada com padrões de reversão.
    Agora suporta análise multi-timeframe quando client e symbol são fornecidos.
    
    Args:
        market_data: Dados do timeframe primário
        client: Cliente da exchange (opcional, para análise multi-timeframe)
        symbol: Símbolo do ativo (opcional, para análise multi-timeframe)
    
    Returns:
        str: 'COMPRAR'|'VENDER'|'AGUARDAR'
    """
    # 1. Tentar análise multi-timeframe primeiro se client e symbol disponíveis
    if client and symbol:
        print(f"🚀 USANDO ANÁLISE MULTI-TIMEFRAME para {symbol}")
        mta_signal = find_integrated_momentum_signal_mta(client, symbol, market_data)
        if mta_signal != 'AGUARDAR':
            return mta_signal
        print(f"🔄 MTA retornou AGUARDAR, tentando análise complementar...")
    else:
        print("⚠️  Client/Symbol não fornecidos, usando análise single-timeframe")
        
    # 2. Análise integrada single-timeframe como fallback
    integrated_signal = find_integrated_momentum_signal_legacy(market_data)
    
    if integrated_signal != 'AGUARDAR':
        return integrated_signal
    
    # 3. Se não há sinal claro, verificar padrões de reversão
    reversal_patterns = detect_reversal_patterns(market_data)
    volatility = calculate_volatility_score(market_data)
    
    # Só considerar padrões de reversão se a volatilidade for adequada
    if volatility > MIN_VOLATILITY_FOR_PATTERNS:  # Configurável via settings
        if reversal_patterns['bullish_reversal']:
            print(f"🔄 Padrão de reversão ALTISTA detectado: {reversal_patterns['pattern_name']}")
            return 'COMPRAR'
        elif reversal_patterns['bearish_reversal']:
            print(f"🔄 Padrão de reversão BAIXISTA detectado: {reversal_patterns['pattern_name']}")
            return 'VENDER'
    
    return 'AGUARDAR'

def find_comprehensive_exit_signal(market_data: pd.DataFrame, position_side: str) -> bool:
    """
    Análise avançada de saída que usa a análise integrada como base.
    """
    return find_integrated_exhaustion_signal_legacy(market_data, position_side)

# =============================================================================
# 5. FUNÇÕES DE UTILIDADE E RELATÓRIOS
# =============================================================================

def generate_technical_analysis_report(market_data: pd.DataFrame, symbol: str = "Unknown", multi_data: dict = None) -> dict:
    """
    Gera um relatório completo da análise técnica integrada, incluindo dados multi-timeframe se disponíveis.
    """
    # Requisito mínimo mais flexível
    # Requisito mínimo configurável
    min_required = max(RSI_PERIOD, MACD_SLOW, BB_PERIOD, FALLBACK_EMA_FILTER) + MIN_DATA_BUFFER
    
    if market_data is None or len(market_data) < min_required:
        return {
            'symbol': symbol,
            'status': 'ERRO',
            'message': f'Dados insuficientes para análise completa (mín. {min_required}, atual: {len(market_data) if market_data is not None else 0})',
            'timestamp': pd.Timestamp.now()
        }
    
    # Análise integrada
    integrated_analysis = calculate_integrated_signal(market_data)
    
    # Análise de momentum integrada para comparação
    momentum_signal = find_integrated_momentum_signal_legacy(market_data)
    
    # Padrões de reversão
    reversal_patterns = detect_reversal_patterns(market_data)
    
    # Divergências (agora usando análise clássica)
    divergence_analysis = analyze_volume_price_divergence(market_data)
    
    # Volatilidade
    volatility = calculate_volatility_score(market_data)
    
    # Tendência
    trend_context = analyze_trend_context(market_data)
    
    # Preço atual
    current_price = market_data['close'].iloc[-1]
    
    report = {
        'symbol': symbol,
        'timestamp': pd.Timestamp.now(),
        'current_price': current_price,
        'status': 'OK',
        
        # Análise integrada principal
        'integrated_analysis': {
            'signal': integrated_analysis['signal'],
            'confidence': integrated_analysis['confidence'],
            'weighted_score': integrated_analysis['weighted_score'],
            'description': integrated_analysis['description']
        },
        
        # Detalhes dos indicadores
        'indicators': {
            'RSI': {
                'value': integrated_analysis['indicators']['RSI'].get('strength', 0),
                'signal': integrated_analysis['indicators']['RSI'].get('signal', 'NEUTRO'),
                'strength': integrated_analysis['indicators']['RSI'].get('strength', 0),
                'description': integrated_analysis['indicators']['RSI'].get('description', '')
            },
            'MACD': {
                'signal': integrated_analysis['indicators']['MACD'].get('signal', 'NEUTRO'),
                'strength': integrated_analysis['indicators']['MACD'].get('strength', 0),
                'description': integrated_analysis['indicators']['MACD'].get('description', '')
            },
            'BB': {
                'signal': integrated_analysis['indicators']['BB'].get('signal', 'NEUTRO'),
                'strength': integrated_analysis['indicators']['BB'].get('strength', 0),
                'description': integrated_analysis['indicators']['BB'].get('description', '')
            },
            'EMA': {
                'signal': integrated_analysis['indicators']['EMA'].get('signal', 'NEUTRO'),
                'strength': integrated_analysis['indicators']['EMA'].get('strength', 0),
                'description': integrated_analysis['indicators']['EMA'].get('description', '')
            }
        },
        
        # Análises complementares
        'momentum_legacy': momentum_signal,
        'reversal_patterns': reversal_patterns,
        'divergence_analysis': divergence_analysis,
        'volatility': volatility,
        'trend_context': trend_context,
        
        # Pesos utilizados
        'weights': integrated_analysis.get('weights_used', {}),
        
        # Recomendação final
        'recommendation': {
            'action': integrated_analysis['signal'],
            'confidence_level': 'HIGH' if integrated_analysis['confidence'] >= 0.7 else 
                              'MEDIUM' if integrated_analysis['confidence'] >= 0.4 else 'LOW',
            'risk_assessment': 'HIGH' if volatility > 0.05 else 
                             'MEDIUM' if volatility > 0.02 else 'LOW'
        }
    }
    
    # Adicionar análise multi-timeframe se disponível
    if multi_data:
        mta_result = calculate_multi_timeframe_signal(multi_data)
        trend_filter = analyze_higher_timeframe_trend(multi_data['confirmation'])
        
        report['multi_timeframe'] = {
            'available': True,
            'primary_tf': PRIMARY_TIMEFRAME,
            'secondary_tf': SECONDARY_TIMEFRAME,
            'confirmation_tf': CONFIRMATION_TIMEFRAME,
            'mta_signal': mta_result['signal'],
            'mta_confidence': mta_result['confidence'],
            'mta_approved': mta_result['mta_approved'],
            'trend_filter': trend_filter,
            'description': mta_result['description']
        }
        
        # Atualizar recomendação final se MTA estiver disponível
        if mta_result['mta_approved']:
            report['recommendation']['action'] = mta_result['signal']
            report['recommendation']['mta_enhanced'] = True
        else:
            report['recommendation']['mta_enhanced'] = False
            report['recommendation']['mta_rejection_reason'] = mta_result['description']
    else:
        report['multi_timeframe'] = {
            'available': False,
            'reason': 'Dados multi-timeframe não fornecidos'
        }
    
    return report

def print_analysis_summary(market_data: pd.DataFrame, symbol: str = "Unknown"):
    """
    Imprime um resumo da análise técnica de forma organizada.
    """
    report = generate_technical_analysis_report(market_data, symbol)
    
    if report['status'] != 'OK':
        print(f"❌ Erro na análise de {symbol}: {report['message']}")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 RELATÓRIO DE ANÁLISE TÉCNICA - {symbol}")
    print(f"{'='*60}")
    print(f"⏰ Timestamp: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"� Preço Atual: ${report['current_price']:.4f}")
    print(f"📈 Tendência: {report['trend_context']}")
    print(f"📊 Volatilidade: {report['volatility']:.4f}")
    
    print(f"\n🎯 SINAL INTEGRADO:")
    print(f"   ➤ Ação: {report['integrated_analysis']['signal']}")
    print(f"   ➤ Confiança: {report['integrated_analysis']['confidence']:.2f}")
    print(f"   ➤ Score: {report['integrated_analysis']['weighted_score']:.3f}")
    
    print(f"\n📈 INDICADORES TÉCNICOS:")
    for indicator, data in report['indicators'].items():
        emoji = "🟢" if data['signal'] == 'COMPRAR' else "🔴" if data['signal'] == 'VENDER' else "⚪"
        strength = data.get('strength', 0)  # Usar get() com valor padrão
        print(f"   {emoji} {indicator}: {data['signal']} (força: {strength:.2f})")
        if data.get('description'):
            print(f"      └─ {data['description']}")
    
    print(f"\n📈 ANÁLISES COMPLEMENTARES:")
    print(f"   📊 Momentum Legacy: {report['momentum_legacy']}")
    
    if report['reversal_patterns']['pattern_name'] != 'none':
        pattern_emoji = "🟢" if report['reversal_patterns']['bullish_reversal'] else "🔴"
        print(f"   {pattern_emoji} Padrão de Reversão: {report['reversal_patterns']['pattern_name']}")
    
    if report['divergence_analysis']['bullish_divergence'] or report['divergence_analysis']['bearish_divergence']:
        div_type = "Altista" if report['divergence_analysis']['bullish_divergence'] else "Baixista"
        print(f"   ⚠️  Divergência {div_type} detectada")
    
    print(f"\n💡 RECOMENDAÇÃO FINAL:")
    rec = report['recommendation']
    action_emoji = "🟢" if rec['action'] == 'COMPRAR' else "🔴" if rec['action'] == 'VENDER' else "⚪"
    print(f"   {action_emoji} Ação: {rec['action']}")
    print(f"   🎯 Nível de Confiança: {rec['confidence_level']}")
    print(f"   ⚠️  Avaliação de Risco: {rec['risk_assessment']}")
    print(f"{'='*60}\n")

def print_analysis_summary_mta(market_data: pd.DataFrame, symbol: str = "Unknown", multi_data: dict = None):
    """
    Versão melhorada da função de resumo que inclui análise multi-timeframe.
    """
    report = generate_technical_analysis_report(market_data, symbol, multi_data)
    
    if report['status'] != 'OK':
        print(f"❌ Erro na análise de {symbol}: {report['message']}")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 RELATÓRIO DE ANÁLISE TÉCNICA MTA - {symbol}")
    print(f"{'='*60}")
    print(f"⏰ Timestamp: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Preço Atual: ${report['current_price']:.4f}")
    print(f"📈 Tendência: {report['trend_context']}")
    print(f"📊 Volatilidade: {report['volatility']:.4f}")
    
    # Mostrar informações multi-timeframe se disponível
    if report['multi_timeframe']['available']:
        mta = report['multi_timeframe']
        print(f"\n🔍 ANÁLISE MULTI-TIMEFRAME:")
        print(f"   📊 Timeframes: {mta['primary_tf']} | {mta['secondary_tf']} | {mta['confirmation_tf']}")
        print(f"   🎯 Sinal MTA: {mta['mta_signal']} (confiança: {mta['mta_confidence']:.2f})")
        print(f"   ✅ Aprovado: {mta['mta_approved']}")
        print(f"   📍 Tendência {mta['confirmation_tf']}: {mta['trend_filter']['trend']} (força: {mta['trend_filter']['strength']:.2f})")
        print(f"   💡 {mta['description']}")
    else:
        print(f"\n⚠️  ANÁLISE MULTI-TIMEFRAME: {report['multi_timeframe']['reason']}")
    
    print(f"\n🎯 SINAL INTEGRADO:")
    print(f"   ➤ Ação: {report['integrated_analysis']['signal']}")
    print(f"   ➤ Confiança: {report['integrated_analysis']['confidence']:.2f}")
    print(f"   ➤ Score: {report['integrated_analysis']['weighted_score']:.3f}")
    
    print(f"\n📈 INDICADORES TÉCNICOS:")
    for indicator, data in report['indicators'].items():
        emoji = "🟢" if data['signal'] == 'COMPRAR' else "🔴" if data['signal'] == 'VENDER' else "⚪"
        strength = data.get('strength', 0)
        print(f"   {emoji} {indicator}: {data['signal']} (força: {strength:.2f})")
        if data.get('description'):
            print(f"      └─ {data['description']}")
    
    print(f"\n📈 ANÁLISES COMPLEMENTARES:")
    print(f"   📊 Momentum Legacy: {report['momentum_legacy']}")
    
    if report['reversal_patterns']['pattern_name'] != 'none':
        pattern_emoji = "🟢" if report['reversal_patterns']['bullish_reversal'] else "🔴"
        print(f"   {pattern_emoji} Padrão de Reversão: {report['reversal_patterns']['pattern_name']}")
    
    # Mostrar divergências clássicas melhoradas
    div_analysis = report['divergence_analysis']
    if div_analysis['bullish_divergence']:
        print(f"   🟢 Divergência Altista RSI detectada (força: {div_analysis['strength']:.2f})")
        print(f"      └─ Picos analisados: {div_analysis['total_peaks']} | Vales analisados: {div_analysis['total_troughs']}")
    elif div_analysis['bearish_divergence']:
        print(f"   🔴 Divergência Baixista RSI detectada (força: {div_analysis['strength']:.2f})")
        print(f"      └─ Picos analisados: {div_analysis['total_peaks']} | Vales analisados: {div_analysis['total_troughs']}")
    
    print(f"\n💡 RECOMENDAÇÃO FINAL:")
    rec = report['recommendation']
    action_emoji = "🟢" if rec['action'] == 'COMPRAR' else "🔴" if rec['action'] == 'VENDER' else "⚪"
    print(f"   {action_emoji} Ação: {rec['action']}")
    print(f"   🎯 Nível de Confiança: {rec['confidence_level']}")
    print(f"   ⚠️  Avaliação de Risco: {rec['risk_assessment']}")
    
    if 'mta_enhanced' in rec:
        if rec['mta_enhanced']:
            print(f"   🚀 Status: ✅ Confirmado por análise multi-timeframe")
        else:
            print(f"   ⚠️  Status: ❌ Rejeitado por análise multi-timeframe")
            print(f"      └─ Motivo: {rec.get('mta_rejection_reason', 'Não especificado')}")
    
    print(f"{'='*60}\n")

# =============================================================================
# 6. EXEMPLO DE USO DAS NOVAS FUNÇÕES MULTI-TIMEFRAME
# =============================================================================

def example_multi_timeframe_usage():
    """
    Exemplo de como usar as novas funções de análise multi-timeframe.
    """
    print("="*60)
    print("📚 EXEMPLO DE USO - ANÁLISE MULTI-TIMEFRAME")
    print("="*60)
    
    example_code = '''
# EXEMPLO 1: Análise de entrada multi-timeframe
from binance.client import Client

# Configurar cliente (substitua pelas suas credenciais)
client = Client('api_key', 'api_secret')
symbol = 'BTCUSDT'

# Método 1: Análise completa multi-timeframe (RECOMENDADO)
signal = find_integrated_momentum_signal_mta(client, symbol)
print(f"Sinal MTA: {signal}")

# Método 2: Análise manual dos timeframes
multi_data = fetch_multi_timeframe_data(client, symbol)
if multi_data:
    mta_result = calculate_multi_timeframe_signal(multi_data)
    print_analysis_summary_mta(multi_data['primary'], symbol, multi_data)

# EXEMPLO 2: Análise de saída multi-timeframe
position_side = 'LONG'  # ou 'SHORT'
should_exit = find_integrated_exhaustion_signal_mta(client, symbol, position_side)
print(f"Deve sair da posição {position_side}: {should_exit}")

# EXEMPLO 3: Análise de tendência em timeframe superior
trend_analysis = analyze_higher_timeframe_trend(multi_data['confirmation'])
print(f"Tendência 15m: {trend_analysis['trend']} (força: {trend_analysis['strength']:.2f})")

# EXEMPLO 4: Análise de divergência clássica melhorada
divergence = analyze_volume_price_divergence(multi_data['primary'])
if divergence['bullish_divergence']:
    print(f"🟢 Divergência altista detectada com {divergence['total_peaks']} picos")
elif divergence['bearish_divergence']:
    print(f"🔴 Divergência baixista detectada com {divergence['total_troughs']} vales")
'''
    
    print(example_code)
    print("="*60)
    print("🔧 PRINCIPAIS MELHORIAS IMPLEMENTADAS:")
    print("✅ 1. Análise Multi-Timeframe Real (MTA)")
    print("   • Coleta dados de 1m, 5m e 15m simultaneamente")
    print("   • Filtra sinais do 1m com base na tendência do 15m")
    print("   • Confirma com contexto do 5m")
    print("")
    print("✅ 2. Análise de Divergência Clássica")
    print("   • Detecta topos/fundos em preço e RSI")
    print("   • Identifica divergências bullish e bearish reais")
    print("   • Reduz falsos positivos significativamente")
    print("")
    print("📊 CONFIGURAÇÕES UTILIZADAS:")
    print(f"   • Timeframe Primário: {PRIMARY_TIMEFRAME} (sinais)")
    print(f"   • Timeframe Secundário: {SECONDARY_TIMEFRAME} (contexto)")
    print(f"   • Timeframe Confirmação: {CONFIRMATION_TIMEFRAME} (filtro de tendência)")
    print(f"   • EMA Filtro: {EMA_FILTER} períodos no timeframe de confirmação")
    print("="*60)

if __name__ == "__main__":
    print_current_settings()
    example_multi_timeframe_usage()