import json
import math
import os
import random
import subprocess
from random import randint

import matplotlib.pyplot as plt
import re
from itertools import product
from collections import defaultdict

INPUT_DIR = "tsp_maps"
RESULTS_DIR = "results"
ALGORITHMS = {
    'genetic': {
        'exec': './genetic',
        'params': {
            '-pop': [100, 200],
            '-mut': [0.01, 0.05],
            '-elite': [5, 10]
        }
    },
    'annealing': {
        'exec': './annealing',
        'params': {
            '-temp': [10000, 50000],
            '-cooling': [0.999, 0.9999],
            '-iters': [10000]
        }
    },
    'aco': {
        'exec': './aco',
        'params': {
            '-ants': [50, 100],
            '-alpha': [1, 2],
            '-beta': [2, 5]
        }
    }
}


def get_tsp_files():
    """Get all .tsp files in input directory"""
    return [f for f in os.listdir(INPUT_DIR) if f.endswith('.tsp')]


def run_experiment(algorithm, tsp_file, params):
    """Execute Go program for a specific TSP file"""
    cmd = [algorithm['exec'], '-input', os.path.join(INPUT_DIR, tsp_file)]
    for k, v in params.items():
        cmd.extend([k, str(v)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )

    match = re.search(r'Best route distance: (\d+\.\d+)', result.stdout)
    return float(match.group(1)) if match else None


def plot_results(results, algorithm, tsp_file):
    """Generate plots for specific TSP file"""
    plt.figure(figsize=(12, 6))
    os.makedirs(os.path.join(RESULTS_DIR, tsp_file), exist_ok=True)

    param_groups = defaultdict(list)
    for params, distance in results:
        main_param = list(params.keys())[0]
        param_groups[main_param].append((params[main_param], distance))

    for i, (param, values) in enumerate(param_groups.items(), 1):
        plt.subplot(1, len(param_groups), i)
        x, y = zip(*sorted(values))
        plt.plot(x, y, 'o-')
        plt.xlabel(param)
        plt.ylabel('Distance')
        plt.title(f'{tsp_file} - {param} vs Distance')

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, tsp_file, f'{algorithm}.png'))
    plt.close()


# def choose_best_hyperparameter():
#     tsp_files = get_tsp_files()
#     for tsp_file in tsp_files:
#
#         for _ in range(10):


def main():
    tsp_files = get_tsp_files()
    answer = {}
    for tsp_file in tsp_files:
        print(f"\nProcessing {tsp_file}...")
        qdt_points = int(re.search(r"\d+", tsp_file).group())
        answer[tsp_file.split(".tsp")[0]] = {}
        for algo_name, config in ALGORITHMS.items():
            print(f"  Running {algo_name} algorithm...")
            results = []

            shortest_distance = math.inf
            shortest_hyperparameters = {}
            if algo_name == "genetic":
                for _ in range(20):
                    population_size = randint(qdt_points * 2, qdt_points * 6)
                    mutation_rate = random.uniform(0, 1)
                    elite = random.randint(2, population_size // 10)
                    hyperparameters = {
                        '-pop': population_size,
                        '-mut': mutation_rate,
                        '-elite': elite
                    }
                    distance = run_experiment(config, tsp_file, {
                        '-pop': population_size,
                        '-mut': mutation_rate,
                        '-elite': elite
                    })
                    print(distance)
                    print(hyperparameters)
                    if distance < shortest_distance:
                        shortest_distance = distance
                        shortest_hyperparameters = hyperparameters

                print("Melhores hyperparametros do algoritmo genetico")
                print(shortest_distance)
                print(shortest_hyperparameters)
                answer[tsp_file.split(".tsp")[0]]["genetic"] = {"shortest_distance": shortest_distance, "params": shortest_hyperparameters}
            elif algo_name == "aco":
                for _ in range(40):
                    ants = randint(qdt_points * 2, qdt_points * 6)
                    alfa = random.uniform(1, 5)
                    beta = random.uniform(1, 5)
                    hyperparameters = {
                        '-ants': ants,
                        '-alpha': alfa,
                        '-beta': beta,
                        "-iters": 500
                    }
                    distance = run_experiment(config, tsp_file, hyperparameters)
                    print(distance)
                    print(hyperparameters)
                    if distance < shortest_distance:
                        shortest_distance = distance
                        shortest_hyperparameters = hyperparameters
                print("Melhores hyperparametros do algoritmo genetico")
                print(shortest_distance)
                print(shortest_hyperparameters)
                answer[tsp_file.split(".tsp")[0]]["aco"] = {
                "shortest_distance" : shortest_distance, "params": shortest_hyperparameters
                }
            elif algo_name == "annealing":
                for _ in range(20):
                    temperature = random.uniform(10000, 100000)
                    cooling = random.uniform(0.9, 0.9999)

                    hyperparameters = {
                        "-temp": temperature,
                        "-cooling": cooling
                    }
                    distance = run_experiment(config, tsp_file, hyperparameters)
                    print(distance)
                    print(hyperparameters)
                    if distance < shortest_distance:
                        shortest_distance = distance
                        shortest_hyperparameters = hyperparameters

                    print("Melhores hyperparametros do anneling")
                    print(shortest_distance)
                    print(shortest_hyperparameters)
                    answer[tsp_file.split(".tsp")[0]]["annealing"] = {
                        "shortest_distance": shortest_distance, "params": shortest_hyperparameters
                    }

    with open("best_hyperparameters2.json", "w") as f:
        f.write(json.dumps(answer))
if __name__ == "__main__":
    main()
