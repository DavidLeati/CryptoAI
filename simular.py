from libs import pd, np

def simular_operacoes(
    df: pd.DataFrame,
    predicoes: np.ndarray,
    capital_inicial: float = 100.0,
    alavancagem: float = 25.0,
    pct_operacao: float = 0.5,
    threshold_retorno_entrada: float = 0.0005,
    taxa_trade: float = 0.0002,
    atr_multiplier_tp: float = 4.0,
    atr_multiplier_sl: float = 2.0, 
    nivel_stop_trading_pct: float = 0.50
) -> tuple[pd.DataFrame, dict]:
    """
    Simula operações de trading baseadas em previsões de RETORNO PERCENTUAL,
    com gestão de capital, Take Profit e Stop Loss baseados em ATR, e custos.

    Args:
        df (pd.DataFrame): DataFrame com os dados de mercado (deve conter 'close',
                           'open_time' e 'ATR'). O índice deve ser sequencial.
        predicoes (np.ndarray): Array numpy com as previsões de retorno percentual.
        capital_inicial (float): Capital com que a simulação começa.
        alavancagem (float): Fator de alavancagem usado nas operações.
        pct_operacao (float): Percentual do capital disponível a ser arriscado por operação.
        threshold_retorno_entrada (float): Valor absoluto mínimo do retorno percentual
                                           previsto para iniciar uma operação.
        taxa_trade (float): Taxa de trading por lado da operação.
        atr_multiplier_tp (float): Multiplicador do valor do ATR para definir a distância
                                   do Take Profit a partir do preço de entrada.
        atr_multiplier_sl (float): Multiplicador do valor do ATR para definir a distância
                                   do Stop Loss a partir do preço de entrada.
        nivel_stop_trading_pct (float): Percentual de *perda* do capital inicial abaixo
                                        do qual a simulação para.

    Returns:
        tuple: Contendo:
            - pd.DataFrame: Histórico das operações realizadas.
            - dict: Métricas de desempenho da simulação.
    """
    # --- Validações Iniciais ---
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df deve ser um pandas DataFrame.")
    if not isinstance(predicoes, np.ndarray):
        try:
            predicoes = np.array(predicoes)
        except Exception as e:
            raise ValueError(f"predicoes devem ser um array numpy ou conversível para um. Erro: {e}")
    required_cols = ['close', 'open_time', 'ATR']
    if not all(col in df.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"DataFrame 'df' deve conter as colunas: {required_cols}. Faltando: {missing_cols}")
    if len(df) != len(predicoes):
        raise ValueError(f"Tamanho do DataFrame ({len(df)}) e das predições ({len(predicoes)}) não coincidem.")
    if not (0 < pct_operacao <= 1):
        raise ValueError("pct_operacao deve estar entre 0 (exclusivo) e 1 (inclusivo).")
    if threshold_retorno_entrada < 0:
        raise ValueError("threshold_retorno_entrada deve ser não-negativo.")
    # ***** NOVO: Validar multiplicador TP *****
    if atr_multiplier_tp <= 0:
        raise ValueError("atr_multiplier_tp deve ser positivo.")
    if atr_multiplier_sl <= 0:
        raise ValueError("atr_multiplier_sl deve ser positivo.")
    if atr_multiplier_tp <= atr_multiplier_sl:
        print(f"Aviso: atr_multiplier_tp ({atr_multiplier_tp}) não é maior que atr_multiplier_sl ({atr_multiplier_sl}). Isso pode limitar o potencial de lucro.")


    # --- Inicialização ---
    capital = capital_inicial
    operacoes = []
    operacao_aberta = None
    colunas = ['tempo_entrada', 'tempo_saida', 'direcao', 'preco_entrada',
               'preco_saida', 'valor_alocado_inicial', 'quantidade',
               'take_profit_preco', 'stop_loss_preco', 'lucro_bruto',
               'custo_total', 'lucro_liquido', 'capital_apos_operacao',
               'predicao_retorno_entrada', 'motivo_saida', 'ATR_entrada']

    df_sim = df.reset_index(drop=True)
    predicoes_sim = predicoes

    print(f"Iniciando simulação com Capital Inicial: {capital_inicial:.2f}, Threshold Entrada: {threshold_retorno_entrada:.4%}")
    # ***** ATUALIZADO PRINT *****
    print(f"TP: {atr_multiplier_tp} * ATR, SL: {atr_multiplier_sl} * ATR, Alavancagem: {alavancagem}x")

    # --- Loop Principal da Simulação ---
    for i in range(len(df_sim)):
        predicao_retorno = predicoes_sim[i]
        preco_atual = df_sim['close'].iloc[i]
        tempo_atual = df_sim['open_time'].iloc[i]
        atr_atual = df_sim['ATR'].iloc[i]

        if pd.isna(atr_atual) or atr_atual <= 0:
             continue

        # 1. Verificar e Processar Operação Aberta (Saída por TP/SL)
        #    (Lógica inalterada, pois compara com os preços TP/SL definidos na abertura)
        if operacao_aberta is not None:
            fechar = False
            preco_saida = preco_atual
            tempo_saida = tempo_atual
            motivo_saida = None

            if operacao_aberta['direcao'] == 'COMPRA':
                if preco_atual >= operacao_aberta['take_profit_preco']:
                    preco_saida = operacao_aberta['take_profit_preco']
                    fechar = True
                    motivo_saida = 'TP'
                elif preco_atual <= operacao_aberta['stop_loss_preco']:
                    preco_saida = operacao_aberta['stop_loss_preco']
                    fechar = True
                    motivo_saida = 'SL'
            elif operacao_aberta['direcao'] == 'VENDA':
                if preco_atual <= operacao_aberta['take_profit_preco']:
                    preco_saida = operacao_aberta['take_profit_preco']
                    fechar = True
                    motivo_saida = 'TP'
                elif preco_atual >= operacao_aberta['stop_loss_preco']:
                    preco_saida = operacao_aberta['stop_loss_preco']
                    fechar = True
                    motivo_saida = 'SL'

            if fechar:
                # Cálculos de Lucro/Custo (Inalterados)
                if operacao_aberta['direcao'] == 'COMPRA':
                    lucro_bruto = (preco_saida - operacao_aberta['preco_entrada']) * operacao_aberta['quantidade']
                else: # VENDA
                    lucro_bruto = (operacao_aberta['preco_entrada'] - preco_saida) * operacao_aberta['quantidade']

                custo_abertura = operacao_aberta['valor_alocado_inicial'] * taxa_trade
                valor_fechamento_alavancado = preco_saida * operacao_aberta['quantidade']
                custo_fechamento = valor_fechamento_alavancado * taxa_trade
                custo_total = custo_abertura + custo_fechamento

                lucro_liquido = lucro_bruto - custo_total
                capital += lucro_liquido

                operacoes.append([
                    operacao_aberta['tempo_entrada'], tempo_saida, operacao_aberta['direcao'],
                    round(operacao_aberta['preco_entrada'], 8), round(preco_saida, 8),
                    round(operacao_aberta['valor_alocado_inicial'], 2), round(operacao_aberta['quantidade'], 8),
                    round(operacao_aberta['take_profit_preco'], 8), round(operacao_aberta['stop_loss_preco'], 8),
                    round(lucro_bruto, 2), round(custo_total, 2), round(lucro_liquido, 2), round(capital, 2),
                    round(operacao_aberta['predicao_retorno_entrada'], 6), motivo_saida,
                    round(operacao_aberta['atr_entrada'], 8)
                ])
                operacao_aberta = None

                if capital <= capital_inicial * (1 - nivel_stop_trading_pct):
                   print(f"STOP GERAL ATINGIDO! Capital ({capital:.2f}) <= Nível de Stop ({capital_inicial * (1 - nivel_stop_trading_pct):.2f}). Encerrando.")
                   break

        # 2. Verificar Condição de Entrada (se não houver operação aberta)
        if operacao_aberta is None and capital > 0:
            direcao = None
            if predicao_retorno > threshold_retorno_entrada:
                direcao = 'COMPRA'
            elif predicao_retorno < -threshold_retorno_entrada:
                direcao = 'VENDA'

            if direcao:
                valor_alocado = capital * pct_operacao * alavancagem
                if valor_alocado <= 0: continue
                quantidade = valor_alocado / preco_atual

                # ***** ATUALIZADO: Cálculo do TP e SL baseado em ATR *****
                take_profit_distancia = atr_atual * atr_multiplier_tp
                stop_loss_distancia = atr_atual * atr_multiplier_sl

                if direcao == 'COMPRA':
                    take_profit_preco = preco_atual + take_profit_distancia # TP acima do preço
                    stop_loss_preco = preco_atual - stop_loss_distancia # SL abaixo do preço
                else: # VENDA
                    take_profit_preco = preco_atual - take_profit_distancia # TP abaixo do preço
                    stop_loss_preco = preco_atual + stop_loss_distancia # SL acima do preço

                # Segurança: garantir que SL/TP não sejam negativos ou zero
                if (direcao == 'COMPRA' and stop_loss_preco <= 0) or \
                   (direcao == 'VENDA' and take_profit_preco <= 0):
                    print(f"Aviso: TP ({take_profit_preco:.5f}) ou SL ({stop_loss_preco:.5f}) inválido (<=0) para {direcao} @ {preco_atual:.5f} com ATR {atr_atual:.5f}. Pulando operação.")
                    continue # Pula a operação se o TP ou SL for inválido

                # Abre a nova operação
                operacao_aberta = {
                    'tempo_entrada': tempo_atual, 'direcao': direcao, 'preco_entrada': preco_atual,
                    'quantidade': quantidade, 'valor_alocado_inicial': valor_alocado,
                    'take_profit_preco': take_profit_preco, # Usa TP calculado com ATR
                    'stop_loss_preco': stop_loss_preco,     # Usa SL calculado com ATR
                    'predicao_retorno_entrada': predicao_retorno,
                    'atr_entrada': atr_atual
                }
                # print(f"[{tempo_atual}] ABRIR {direcao} @ {preco_atual:.5f} (Pred: {predicao_retorno:.4%}) TP={take_profit_preco:.5f} SL={stop_loss_preco:.5f} (ATR={atr_atual:.5f})")


    # --- Pós-Loop: Fechar operação pendente ---
    if operacao_aberta is not None:
        print("Fechando operação pendente no final dos dados...")
        preco_saida = df_sim['close'].iloc[-1]
        tempo_saida = df_sim['open_time'].iloc[-1]
        motivo_saida = 'Fim dos Dados'

        # Cálculos de Lucro/Custo (Inalterados)
        if operacao_aberta['direcao'] == 'COMPRA':
            lucro_bruto = (preco_saida - operacao_aberta['preco_entrada']) * operacao_aberta['quantidade']
        else: # VENDA
            lucro_bruto = (operacao_aberta['preco_entrada'] - preco_saida) * operacao_aberta['quantidade']

        custo_abertura = operacao_aberta['valor_alocado_inicial'] * taxa_trade
        valor_fechamento_alavancado = preco_saida * operacao_aberta['quantidade']
        custo_fechamento = valor_fechamento_alavancado * taxa_trade
        custo_total = custo_abertura + custo_fechamento

        lucro_liquido = lucro_bruto - custo_total
        capital += lucro_liquido

        operacoes.append([
            operacao_aberta['tempo_entrada'], tempo_saida, operacao_aberta['direcao'],
            round(operacao_aberta['preco_entrada'], 8), round(preco_saida, 8),
            round(operacao_aberta['valor_alocado_inicial'], 2), round(operacao_aberta['quantidade'], 8),
            round(operacao_aberta['take_profit_preco'], 8), round(operacao_aberta['stop_loss_preco'], 8),
            round(lucro_bruto, 2), round(custo_total, 2), round(lucro_liquido, 2), round(capital, 2),
            round(operacao_aberta['predicao_retorno_entrada'], 6), motivo_saida,
            round(operacao_aberta['atr_entrada'], 8)
        ])
        operacao_aberta = None

    # --- Cálculo de Métricas Finais ---
    df_operacoes = pd.DataFrame(operacoes, columns=colunas)
    metricas = calcular_metricas_desempenho(df_operacoes, capital_inicial, capital) # Chama função externa

    # --- Output Final ---
    df_operacoes.to_csv('operacoes_simuladas_regressao_atr_tp_sl.csv', index=False) # Novo nome de arquivo
    print("\nSimulação concluída!")
    print("\nMétricas de Desempenho:")
    for key, value in metricas.items():
        if '%' in key: print(f"  {key}: {value:.2f}%")
        elif isinstance(value, float): print(f"  {key}: {value:.2f}")
        else: print(f"  {key}: {value}")

    return df_operacoes, metricas


# --- Função de Métricas (Inalterada) ---
def calcular_metricas_desempenho(df_operacoes: pd.DataFrame, capital_inicial: float, capital_final: float) -> dict:
    """Calcula métricas de desempenho a partir do DataFrame de operações."""
    if df_operacoes.empty:
        print("Nenhuma operação realizada para calcular métricas.")
        # Retorna métricas zeradas para evitar erros posteriores
        return {
            'capital_inicial': capital_inicial, 'capital_final': capital_final,
            'lucro_total_liquido': 0, 'retorno_percentual (%)': 0,
            'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
            'win_rate (%)': 0, 'total_profit': 0, 'total_loss': 0,
            'profit_factor': 0, 'average_win': 0, 'average_loss': 0,
            'max_drawdown (%)': 0, 'sharpe_ratio (aprox)': 0
        }

    total_trades = len(df_operacoes)
    winning_trades_df = df_operacoes[df_operacoes['lucro_liquido'] > 0]
    losing_trades_df = df_operacoes[df_operacoes['lucro_liquido'] <= 0]

    num_winning_trades = len(winning_trades_df)
    num_losing_trades = total_trades - num_winning_trades

    total_profit = winning_trades_df['lucro_liquido'].sum()
    total_loss = losing_trades_df['lucro_liquido'].sum()

    profit_factor = abs(total_profit / total_loss) if total_loss != 0 else np.inf
    avg_win = winning_trades_df['lucro_liquido'].mean() if num_winning_trades > 0 else 0
    avg_loss = losing_trades_df['lucro_liquido'].mean() if num_losing_trades > 0 else 0
    win_rate = (num_winning_trades / total_trades) * 100 if total_trades > 0 else 0

    equity_curve = pd.Series([capital_inicial] + df_operacoes['capital_apos_operacao'].tolist())
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max.replace(0, np.nan)
    max_drawdown_pct = abs(drawdown.min()) * 100 if not drawdown.isnull().all() else 0

    retornos_trades = df_operacoes['lucro_liquido'] / df_operacoes['capital_apos_operacao'].shift(1).fillna(capital_inicial)
    std_retornos = retornos_trades.std()
    sharpe_ratio_aprox = (retornos_trades.mean() / std_retornos) * np.sqrt(252) if std_retornos != 0 and not pd.isna(std_retornos) else 0

    metricas = {
        'capital_inicial': capital_inicial, 'capital_final': capital_final,
        'lucro_total_liquido': total_profit + total_loss,
        'retorno_percentual (%)': ((capital_final / capital_inicial) - 1) * 100 if capital_inicial > 0 else 0,
        'total_trades': total_trades, 'winning_trades': num_winning_trades,
        'losing_trades': num_losing_trades, 'win_rate (%)': win_rate,
        'total_profit': total_profit, 'total_loss': total_loss,
        'profit_factor': profit_factor, 'average_win': avg_win,
        'average_loss': avg_loss, 'max_drawdown (%)': max_drawdown_pct,
        'sharpe_ratio (aprox)': sharpe_ratio_aprox
    }
    return metricas