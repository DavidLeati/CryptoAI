from libs import Pipeline, TimeSeriesSplit, MinMaxScaler, MLPRegressor
from libs import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import pandas as pd
from simular import simular_operacoes

class ModelTrainerMLP:
    """
    Classe para treinar e avaliar um modelo MLP para REGRESSÃO de séries temporais financeiras.
    Prevê a variação percentual do preço de fechamento.
    """
    def __init__(self, df: pd.DataFrame):
        """
        Inicializa a classe com o DataFrame.

        Args:
            df (pd.DataFrame): DataFrame contendo pelo menos a coluna 'close' e as features.
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Entrada 'df' deve ser um pandas DataFrame.")
        if 'close' not in df.columns:
            raise ValueError("DataFrame deve conter a coluna 'close'.")

        self.df_original = df.copy() # Guarda o original se precisar
        self.df = df.copy()

        # --- Criação do Target de Regressão ---
        # Calcula a variação percentual do 'close'
        self.df['target'] = self.df['close'].pct_change()

        # --- Tratamento de NaNs e Infinitos ---
        # Remove o NaN inicial gerado pelo pct_change()
        self.df.dropna(subset=['target'], inplace=True)
        # Garante que não há infinitos no target (pode ocorrer em casos raros)
        self.df.replace([np.inf, -np.inf], np.nan, inplace=True)
        self.df.dropna(subset=['target'], inplace=True)

        # --- Features Definidas ---
        self.feature_names = ['RSI', 'MACD', 'ATR', 'Volume_Change', 'STOCH', 'Momentum', 'Volatility']
        # Verifica se todas as features existem
        if not all(col in self.df.columns for col in self.feature_names):
            missing_cols = [col for col in self.feature_names if col not in self.df.columns]
            raise ValueError(f"Colunas de features faltando no DataFrame: {missing_cols}")

        # --- Atributos para dados de treino/teste ---
        self.X_train, self.X_test, self.y_train, self.y_test = None, None, None, None
        self.model = None # Para guardar o modelo treinado

    def _preparar_dados(self):
        """
        Prepara os dados X e y, tratando NaNs e infinitos nas features.
        Retorna X e y prontos para divisão treino/teste.
        """
        # Seleciona as features
        X = self.df[self.feature_names].copy()
        y = self.df['target'].copy()

        # Limpa valores infinitos e NaNs nas FEATURES
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        # Guarda os índices antes de dropar NaNs das features
        original_index = X.index
        X.dropna(inplace=True)
        # Ajusta y para corresponder aos índices restantes em X
        y = y.loc[X.index]

        # Verifica se ainda há dados após a limpeza
        if X.empty or y.empty:
            raise ValueError("Não restaram dados após remover NaNs/Infinitos nas features.")

        print(f"Dados preparados: {X.shape[0]} amostras.")
        return X, y

    def avaliar_modelo_regressao(self, nome_modelo: str, y_true: pd.Series, y_pred: np.ndarray):
        """
        Avalia o modelo de regressão usando métricas apropriadas.

        Args:
            nome_modelo (str): Nome do modelo para exibição.
            y_true (pd.Series): Valores reais do target.
            y_pred (np.ndarray): Valores previstos pelo modelo.
        """
        print(f"\n--- Avaliação do Modelo de Regressão: {nome_modelo} ---")

        # Calcula as métricas
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        # Imprime as métricas formatadas
        print(f"Mean Squared Error (MSE):      {mse:.8f}")
        print(f"Root Mean Squared Error (RMSE):{rmse:.8f}")
        print(f"Mean Absolute Error (MAE):     {mae:.8f}")
        print(f"R² Score (Coefficient of Det.):{r2:.4f}")
        print("--------------------------------------------------")

        # Retorna um dicionário com as métricas (opcional)
        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2
        }

    def treinar_modelo(self, n_splits: int = 5):
        """
        Prepara os dados, treina o modelo MLPRegressor usando TimeSeriesSplit
        e avalia no último split de teste.

        Args:
            n_splits (int): Número de divisões para o TimeSeriesSplit.
        """
        X, y = self._preparar_dados()

        # Configura o TimeSeriesSplit para validação cruzada temporal
        tscv = TimeSeriesSplit(n_splits=n_splits)

        print(f"\nIniciando treinamento com TimeSeriesSplit (usando o último split para teste final)...")

        # Pega os índices do ÚLTIMO split para ter um conjunto de treino e teste final
        # A estrutura original do seu código treinava apenas no último split, vamos manter isso
        # Se quisesse validação cruzada completa, o treino/avaliação seria DENTRO do loop
        all_splits = list(tscv.split(X))
        if not all_splits:
             raise ValueError("TimeSeriesSplit não gerou nenhuma divisão. Verifique o tamanho dos dados.")
        train_index, test_index = all_splits[-1] # Pega o último split

        self.X_train, self.X_test = X.iloc[train_index], X.iloc[test_index]
        self.y_train, self.y_test = y.iloc[train_index], y.iloc[test_index]

        print(f"Tamanho do treino: {len(self.X_train)}, Tamanho do teste: {len(self.X_test)}")

        if len(self.X_train) == 0 or len(self.X_test) == 0:
            raise ValueError("Conjunto de treino ou teste está vazio após o split. Aumente os dados ou diminua n_splits.")

        # --- Treinamento do Pipeline com MLPRegressor ---
        print("Treinando o modelo MLPRegressor...")
        # Cria o Pipeline: Scaler + Modelo
        pipeline = Pipeline([
            ('scaler', MinMaxScaler()), # Ou RobustScaler() se preferir
            ('mlp', MLPRegressor(
                hidden_layer_sizes=(100, 50),  # Arquitetura da rede
                activation='relu',          # Função de ativação
                solver='adam',              # Otimizador
                alpha=0.001,                # Regularização L2
                batch_size='auto',          # Tamanho do batch (auto é geralmente 200 ou len(treino))
                learning_rate='adaptive',   # Taxa de aprendizado adaptativa
                learning_rate_init=0.001,   # Taxa de aprendizado inicial
                max_iter=500,               # Número máximo de épocas
                shuffle=True,               # Embaralhar dados a cada época
                random_state=42,            # Para reprodutibilidade
                early_stopping=True,        # Parar cedo se não houver melhora
                n_iter_no_change=10,        # Número de iterações sem melhora para parar
                validation_fraction=0.1,    # Fração de dados de treino para validação interna
                tol=1e-4                    # Tolerância para convergência
            ))
        ])

        # Treina o pipeline com os dados de treino
        self.model = pipeline.fit(self.X_train, self.y_train)
        print("Modelo treinado com sucesso.")

        # --- Previsão e Avaliação ---
        print("Realizando previsões no conjunto de teste...")
        y_pred = self.model.predict(self.X_test)

        # Avalia usando as métricas de REGRESSÃO
        self.avaliar_modelo_regressao("MLP Regressor (Último Split)", self.y_test, y_pred)

        # --- Simulação ---
        # Certifique-se que simular_operacoes pode usar y_pred (predições de retorno)
        # e o DataFrame correspondente ao teste (df.loc[self.X_test.index])
        try:
            print("\nExecutando simulação de operações...")
            # Passa o slice do DataFrame original correspondente ao teste
            df_teste_com_close = self.df_original.loc[self.X_test.index]
            simular_operacoes(df_teste_com_close, y_pred)
            print("Simulação concluída.")
        except Exception as e:
            print(f"Erro ao executar simular_operacoes: {e}")
            print("Verifique se a função 'simular_operacoes' está adaptada para predições de regressão.")

        return self.model # Retorna o modelo treinado