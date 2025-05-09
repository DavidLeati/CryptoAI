from libs import pd, np

def calculate_indicators(df):
    df = df.copy()

    # RSI - Relative Strength Index
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD - Moving Average Convergence Divergence
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26

    # EMA 20 - Exponential Moving Average
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    
    # ATR - Average True Range
    df['H-L'] = df['high'] - df['low']
    df['H-PC'] = (df['high'] - df['close'].shift()).abs()
    df['L-PC'] = (df['low'] - df['close'].shift()).abs()
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=14).mean()

    # Volatilidade com base em retornos
    df['Volatility'] = df['close'].pct_change().rolling(window=30).std()

    # Mudança de volume
    df['Volume_Change'] = df['volume'].pct_change().round(6)

    # Target - variação positiva acima de 0.01%
    df['Price_Change'] = df['close'].pct_change()
    df['Target'] = (df['Price_Change'] > 0.0001).astype(int)

    # Normalização Logarítmica
    df['volume'] = np.log1p(df['volume'])
    df['Volume_Change'] = np.log1p(np.abs(df['Volume_Change'])) * np.sign(df['Volume_Change'])

    # Stochastic Oscillator (STOCH)
    low_14 = df['low'].rolling(window=14).min()
    high_14 = df['high'].rolling(window=14).max()
    df['STOCH'] = (df['close'] - low_14) / (high_14 - low_14) * 100

    # On-Balance Volume (OBV)
    df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()

    # Rate of Change (ROC)
    df['ROC'] = df['close'].pct_change(periods=12) * 100

    # Average Directional Index (ADX)
    df['ADX'] = df['ATR'].rolling(window=14).mean()

    # Momentum (Preço atual - preço de 10 períodos atrás)
    df['Momentum'] = df['close'] - df['close'].shift(10)
    
    return df.dropna()
