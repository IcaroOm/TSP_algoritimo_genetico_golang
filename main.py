import subprocess
import matplotlib.pyplot as plt
import re
from itertools import product
from collections import defaultdict

# Configuration for hyperparameter tuning
ALGORITHMS = {
    'genetic': {
        'exec': './genetic',
        'params': {
            '-pop': [50, 100, 200],
            '-mut': [0.01, 0.05, 0.1],
            '-elite': [5, 10]
        }
    },
    'annealing': {
        'exec': './annealing',
        'params': {
            '-temp': [10000, 50000],
            '-cooling': [0.999, 0.9999],
            '-iters': [10000, 50000]
        }
    },
    'aco': {
        'exec': './aco',
        'params': {
            '-ants': [20, 50, 100],
            '-alpha': [1, 2],
            '-beta': [2, 5]
        }
    }
}

def run_experiment(algorithm, params):
    """Execute Go program and parse output"""
    cmd = [algorithm['exec'], '-input', 'berlin52.tsp']
    for k, v in params.items():
        cmd.extend([k, str(v)])
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    )
    
    # Extract best distance from output
    match = re.search(r'Best route distance: (\d+\.\d+)', result.stdout)
    if match:
        return float(match.group(1))
    return None

def plot_results(results, algorithm):
    """Generate comparative plots"""
    plt.figure(figsize=(12, 6))
    
    # Group results by hyperparameter combinations
    param_groups = defaultdict(list)
    for params, distance in results:
        main_param = list(params.keys())[0]
        param_groups[main_param].append((params[main_param], distance))
    
    # Create subplots for each parameter
    for i, (param, values) in enumerate(param_groups.items(), 1):
        plt.subplot(1, len(param_groups), i)
        x, y = zip(*sorted(values))
        plt.plot(x, y, 'o-')
        plt.xlabel(param)
        plt.ylabel('Distance')
        plt.title(f'{algorithm} - {param} vs Distance')
    
    plt.tight_layout()
    plt.savefig(f'{algorithm}_comparison.png')
    plt.close()

def main():
    for algo_name, config in ALGORITHMS.items():
        print(f"\nRunning experiments for {algo_name} algorithm...")
        results = []
        
        # Generate all parameter combinations
        param_names = list(config['params'].keys())
        param_values = list(config['params'].values())
        
        for combination in product(*param_values):
            params = dict(zip(param_names, combination))
            
            print(f"Testing {params}...")
            try:
                distance = run_experiment(config, params)
                if distance:
                    results.append((params, distance))
            except subprocess.CalledProcessError as e:
                print(f"Error running {params}: {e}")
        
        # Generate plots for collected results
        plot_results(results, algo_name)

if __name__ == "__main__":
    main()