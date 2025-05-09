from modelos import ModelTrainerMLP
from data import get_historical_data
from indicadores import calculate_indicators
from libs import datetime, timedelta, timezone, np
import threading

time = (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%d')

df = get_historical_data("BTCUSDT", '5m', time)

df = calculate_indicators(df)

# Função que será executada pela thread do MLP
def run_mlp_trainer(trainer):
    """Executa o treinamento e resultados para o trainer MLP."""
    print("\n--- Thread MLP Iniciada ---")
    trainer.treinar_modelo()
    print("--- Thread MLP Finalizada ---")

if __name__ == '__main__':
    # Cria instâncias dos treinadores
    mlp_trainer_instance = ModelTrainerMLP(df)

    # Cria os objetos Thread
    # target: a função a ser executada pela thread
    # args: uma tupla de argumentos a serem passados para a função alvo
    thread_mlp = threading.Thread(target=run_mlp_trainer, args=(mlp_trainer_instance,))

    # Inicia as threads (elas começam a executar a função alvo)
    thread_mlp.start()

    # Espera ambas as threads completarem a execução antes que o programa principal termine
    thread_mlp.join()