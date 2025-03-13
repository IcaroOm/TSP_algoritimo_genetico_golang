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


def compute_percentage_time_difference(exec_times):
    """
    Calcula a diferença percentual entre o tempo médio do algoritmo mais lento e do mais rápido.
    """
    avg_times = {}
    for algo, times in exec_times.items():
        valid_times = [t for t in times.values() if t is not None]
        if valid_times:
            avg_times[algo] = sum(valid_times) / len(valid_times)
        else:
            avg_times[algo] = None

    valid_avg_times = {algo: t for algo, t in avg_times.items() if t is not None}
    if not valid_avg_times:
        print("Não há tempos de execução válidos para comparação.")
        return

    fastest_algo = min(valid_avg_times, key=valid_avg_times.get)
    slowest_algo = max(valid_avg_times, key=valid_avg_times.get)
    fastest_time = valid_avg_times[fastest_algo]
    slowest_time = valid_avg_times[slowest_algo]
    percentage_difference = ((slowest_time - fastest_time) / fastest_time) * 100

    print("Análise de tempos:")
    print(f"  Algoritmo mais rápido: {fastest_algo} (média: {fastest_time:.2f} s)")
    print(f"  Algoritmo mais lento:  {slowest_algo} (média: {slowest_time:.2f} s)")
    print(f"  Diferença percentual de tempo: {percentage_difference:.2f}%")


def compute_critical_difference(distancias):
    """
    Utiliza a fórmula de diferença crítica (Critical Difference) conforme Demsar (2006) para comparar os
    algoritmos com base na menor distância encontrada.

    Passos:
      - Seleciona os conjuntos de dados (TSPs) onde todos os algoritmos possuem valor de distância.
      - Para cada conjunto, gera o ranking (menor distância = melhor rank).
      - Calcula a média dos rankings para cada algoritmo.
      - Computa o Critical Difference (CD) pela fórmula:
            CD = q_alpha * sqrt(k*(k+1)/(6*N))
        onde k é o número de algoritmos, N é o número de conjuntos e q_alpha é o valor crítico
        (para k = 3 e nível de significância de 0.05, pode-se usar q_alpha ≈ 2.343).
      - Compara o algoritmo com menor média de ranking com os demais.
    """
    # Determinar os conjuntos de dados comuns
    common_datasets = None
    for algo, dist in distancias.items():
        dataset_set = set(dist.keys())
        if common_datasets is None:
            common_datasets = dataset_set
        else:
            common_datasets = common_datasets.intersection(dataset_set)
    if not common_datasets:
        print("Não há conjuntos de dados comuns para comparação de distâncias.")
        return

    # Gerar os rankings para cada conjunto de dados
    # Para cada TSP, ordena os algoritmos pela distância (menor é melhor)
    ranks = {algo: [] for algo in distancias.keys()}
    for tsp in common_datasets:
        # Lista de (algoritmo, distância) para este TSP
        resultados = [(algo, distancias[algo][tsp]) for algo in distancias if distancias[algo][tsp] is not None]
        resultados.sort(key=lambda x: x[1])

        # Atribuição de ranks com tratamento de empates
        i = 0
        cur_ranks = {}
        while i < len(resultados):
            tie_start = i
            tie_value = resultados[i][1]
            while i < len(resultados) and resultados[i][1] == tie_value:
                i += 1
            tie_end = i
            avg_rank = (tie_start + tie_end + 1) / 2.0  # ranks iniciam em 1
            for j in range(tie_start, tie_end):
                algo_nome = resultados[j][0]
                cur_ranks[algo_nome] = avg_rank
        # Armazena o ranking para cada algoritmo
        for algo, rank in cur_ranks.items():
            ranks[algo].append(rank)

    # Calcula a média dos rankings para cada algoritmo
    avg_ranks = {algo: (sum(ranks_list) / len(ranks_list)) if len(ranks_list) > 0 else None
                 for algo, ranks_list in ranks.items()}
    print("\nAnálise de distâncias (médias dos rankings):")
    for algo, avg in avg_ranks.items():
        print(f"  {algo}: {avg:.2f}")

    # Número de algoritmos (k) e número de conjuntos (N)
    k = len(avg_ranks)
    N = len(common_datasets)
    # Para k = 3 e nível de significância 0.05, usa-se q_alpha ≈ 2.343 (segundo Demsar, 2006)
    q_alpha = 2.343
    CD = q_alpha * ((k * (k + 1)) / (6 * N)) ** 0.5
    print(f"\nCritical Difference (CD): {CD:.3f}")

    # Identifica o melhor algoritmo (menor média de ranking) e compara com os demais
    best_algo = min(avg_ranks, key=avg_ranks.get)
    print(f"\nMelhor algoritmo (menor média de ranking): {best_algo} ({avg_ranks[best_algo]:.2f})")
    for algo, rank in avg_ranks.items():
        if algo == best_algo:
            continue
        diff = rank - avg_ranks[best_algo]
        if diff > CD:
            print(f"  A diferença entre {best_algo} e {algo} é significativa (diferença = {diff:.2f} > CD)")
        else:
            print(f"  A diferença entre {best_algo} e {algo} NÃO é significativa (diferença = {diff:.2f} <= CD)")


def main():
    # Lê os hiperparâmetros a partir do arquivo JSON
    hyper_data = ler_hyperparametros()

    # Dicionários para armazenar os tempos de execução e as distâncias
    exec_times = {"genetic": {}, "annealing": {}, "aco": {}}
    distancias = {"genetic": {}, "annealing": {}, "aco": {}}

    # Para cada mapa presente no arquivo JSON (ex.: "eil51", "berlin52", etc.)
    for tsp_name, algos in hyper_data.items():
        tsp_file = os.path.join(INPUT_DIR, tsp_name + ".tsp")
        for algo in ["genetic", "annealing", "aco"]:
            if algo not in algos:
                continue
            # Recupera os hiperparâmetros e a menor distância encontrada
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
                print(f"  Tempo de execução: {tempo:.2f} s")
            except Exception as e:
                print(f"Erro ao executar {algo} para {tsp_name}: {e}")
                exec_times[algo][tsp_name] = None

    # Gera os gráficos
    plot_tempo_execucao(exec_times)
    plot_distancias(distancias)
    print("\nGráficos gerados na pasta:", RESULTS_DIR)

    # Análise de diferença percentual de tempo
    print("\n--- Diferença Percentual de Tempo entre o Algoritmo mais rápido e o mais lento ---")
    compute_percentage_time_difference(exec_times)

    # Análise utilizando a fórmula de diferença crítica (Critical Difference) para as distâncias
    print("\n--- Análise com Diferença Crítica (Critical Difference) para as Menores Distâncias ---")
    compute_critical_difference(distancias)


if __name__ == "__main__":
    main()
