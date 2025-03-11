import os
import subprocess
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

def main():
    tsp_files = get_tsp_files()
    
    for tsp_file in tsp_files:
        print(f"\nProcessing {tsp_file}...")
        
        for algo_name, config in ALGORITHMS.items():
            print(f"  Running {algo_name} algorithm...")
            results = []
            
            param_names = list(config['params'].keys())
            param_values = list(config['params'].values())
            
            for combination in product(*param_values):
                params = dict(zip(param_names, combination))
                
                try:
                    distance = run_experiment(config, tsp_file, params)
                    if distance:
                        results.append((params, distance))
                except subprocess.CalledProcessError as e:
                    print(f"Error with {params}: {e}")
            
            if results:
                plot_results(results, algo_name, tsp_file)

if __name__ == "__main__":
    main()