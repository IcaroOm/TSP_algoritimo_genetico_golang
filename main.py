import json
import subprocess
import time
import re
import os
import matplotlib.pyplot as plt

# Diretórios de entrada e resultados
INPUT_DIR = "tsp_maps"
RESULTS_DIR = "results"
HYPERPARAMETERS_FILE = "best_hyperparameters.json"  # ajuste o nome do arquivo se necessário

# Mapeamento dos executáveis dos algoritmos
ALGORITHMS_EXEC = {
    "genetic": "./genetic",
    "annealing": "./annealing",
    "aco": "./aco"
}

def extrair_numero(nome):
    """
    Extrai o número de pontos a partir do nome do arquivo (ex.: "eil51" -> 51)
    """
    m = re.search(r'\d+', nome)
    return int(m.group()) if m else None

def ler_hyperparametros():
    """
    Lê o arquivo JSON com os melhores hiperparâmetros.
    """
    with open(HYPERPARAMETERS_FILE, "r") as f:
        return json.load(f)

def medir_tempo_execucao(cmd):
    """
    Executa o comando utilizando subprocess e retorna o tempo de execução.
    """
    inicio = time.time()
    # Se necessário, capture a saída (supondo que os executáveis imprimam na saída padrão)
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    fim = time.time()
    return fim - inicio

def plot_tempo_execucao(exec_times):
    """
    Gera o gráfico de tempo de execução.
    exec_times: dicionário no formato {algoritmo: {nome_mapa: tempo, ...}, ...}
    """
    plt.figure(figsize=(10, 6))
    for algo, dados in exec_times.items():
        # Ordena os itens de acordo com o número de pontos
        items = sorted(dados.items(), key=lambda x: extrair_numero(x[0]))
        x = [extrair_numero(nome) for nome, _ in items]
        y = [tempo for _, tempo in items]
        plt.plot(x, y, marker="o", label=algo)
    plt.xlabel("Número de pontos")
    plt.ylabel("Tempo de execução (s)")
    plt.title("Tempo de execução dos algoritmos")
    plt.legend()
    plt.grid(True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(RESULTS_DIR, "tempos_execucao.png"))
    plt.close()

def plot_distancias(distancias):
    """
    Gera o gráfico de menores distâncias encontradas.
    distancias: dicionário no formato {algoritmo: {nome_mapa: distância, ...}, ...}
    """
    plt.figure(figsize=(10, 6))
    for algo, dados in distancias.items():
        # Ordena os itens de acordo com o número de pontos
        items = sorted(dados.items(), key=lambda x: extrair_numero(x[0]))
        x = [extrair_numero(nome) for nome, _ in items]
        y = [dist for _, dist in items]
        plt.plot(x, y, marker="o", label=algo)
    plt.xlabel("Número de pontos")
    plt.ylabel("Menor distância encontrada")
    plt.title("Menores distâncias por algoritmo")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, "distancias_minimas.png"))
    plt.close()

def main():
    # Lê os hiperparâmetros a partir do arquivo JSON
    hyper_data = ler_hyperparametros()

    # Dicionários para armazenar os tempos de execução e as distâncias
    exec_times = {"genetic": {}, "annealing": {}, "aco": {}}
    distancias = {"genetic": {}, "annealing": {}, "aco": {}}

    # Para cada mapa presente no arquivo JSON (por exemplo, "eil51", "berlin52", etc.)
    for tsp_name, algos in hyper_data.items():
        # Monta o caminho completo para o arquivo .tsp
        tsp_file = os.path.join(INPUT_DIR, tsp_name + ".tsp")
        for algo in ["genetic", "annealing", "aco"]:
            if algo not in algos:
                continue
            print(algos)
            # Recupera os hiperparâmetros e a menor distância encontrada
            print(algos[algo])
            params = algos[algo]["params"]
            if "shortest_distance" in algos[algo]:
                distancia = algos[algo]["shortest_distance"]
            elif "shortestDistance" in algos[algo]:
                distancia = algos[algo]["shortestDistance"]
            else:
                distancia = None
            distancias[algo][tsp_name] = distancia

            # Monta o comando: [executável, "-input", caminho_do_arquivo, ... hiperparâmetros]
            cmd = [ALGORITHMS_EXEC[algo], "-input", tsp_file]
            for chave, valor in params.items():
                cmd.extend([chave, str(valor)])
            print(f"Executando {algo} para {tsp_name} com o comando: {' '.join(cmd)}")

            try:
                tempo = medir_tempo_execucao(cmd)
                exec_times[algo][tsp_name] = tempo
                print(f"Tempo de execução: {tempo:.2f} s")
            except Exception as e:
                print(f"Erro ao executar {algo} para {tsp_name}: {e}")
                exec_times[algo][tsp_name] = None

    # Gera os gráficos
    plot_tempo_execucao(exec_times)
    plot_distancias(distancias)
    print("Gráficos gerados na pasta:", RESULTS_DIR)

if __name__ == "__main__":
    main()

