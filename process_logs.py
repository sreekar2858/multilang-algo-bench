import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def process_logs():
    # Dictionary to store results from each language
    results = {
        'Language': [],
        'Test': [],
        'Mode': [],
        'Time': [],
        'Threads': []
    }
    
    # Process all log files
    log_dir = Path('logs')
    for log_file in log_dir.glob('*.json'):
        with open(log_file, 'r') as f:
            data = json.load(f)
            language = data['language']
            threads = data.get('thread_count', data.get('process_count', 0))
            
            # Process tests only if the data exists
            if 'fibonacci_serial' in data and 'fibonacci_parallel' in data:
                results['Language'].extend([language, language])
                results['Test'].extend(['Fibonacci', 'Fibonacci'])
                results['Mode'].extend(['Serial', 'Parallel'])
                results['Time'].extend([data['fibonacci_serial'], data['fibonacci_parallel']])
                results['Threads'].extend([threads, threads])
            
            if 'primes_serial' in data and 'primes_parallel' in data:
                results['Language'].extend([language, language])
                results['Test'].extend(['Primes', 'Primes'])
                results['Mode'].extend(['Serial', 'Parallel'])
                results['Time'].extend([data['primes_serial'], data['primes_parallel']])
                results['Threads'].extend([threads, threads])
            
            if 'sort_serial' in data and 'sort_parallel' in data:
                results['Language'].extend([language, language])
                results['Test'].extend(['QuickSort', 'QuickSort'])
                results['Mode'].extend(['Serial', 'Parallel'])
                results['Time'].extend([data['sort_serial'], data['sort_parallel']])
                results['Threads'].extend([threads, threads])
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Create comparison plots
    plot_comparisons(df)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("==================")
    for test in ['Fibonacci', 'Primes', 'QuickSort']:
        test_df = df[df['Test'] == test]
        if len(test_df) > 0:  # Only print statistics if we have data for this test
            print(f"\n{test} Test:")
            for mode in ['Serial', 'Parallel']:
                mode_df = test_df[test_df['Mode'] == mode]
                if len(mode_df) > 0:  # Only print mode if we have data
                    print(f"\n{mode} Mode:")
                    print(mode_df.sort_values('Time')[[
                        'Language', 'Time', 'Threads'
                    ]].to_string(index=False, float_format=lambda x: '{:.6f}'.format(x)))

def plot_comparisons(df):
    # Set up the plot style
    plt.style.use('default')  # Using default style instead of seaborn
    
    # Create figure and determine which tests have data
    available_tests = df['Test'].unique()
    num_tests = len(available_tests)
    fig = plt.figure(figsize=(12, 5*num_tests))
    
    # Plot each test that has data
    for i, test in enumerate(available_tests, 1):
        test_df = df[df['Test'] == test]
        ax = fig.add_subplot(num_tests, 1, i)
        plot_grouped_bars(ax, test_df, f'{test} Test')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('benchmark_results.png')
    print("\nResults plot saved as 'benchmark_results.png'")

def plot_grouped_bars(ax, df, title):
    languages = df['Language'].unique()
    x = range(len(languages))
    width = 0.35
    
    serial = df[df['Mode'] == 'Serial']['Time'].values
    parallel = df[df['Mode'] == 'Parallel']['Time'].values
    threads = df[df['Mode'] == 'Parallel']['Threads'].values
    
    ax.bar([i - width/2 for i in x], serial, width, label='Serial')
    ax.bar([i + width/2 for i in x], parallel, width, label='Parallel')
    
    ax.set_ylabel('Time (seconds)')
    ax.set_title(f'{title}\n(Parallel using {threads} threads/processes per language)')
    ax.set_xticks(x)
    ax.set_xticklabels(languages)
    ax.legend()

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    process_logs()