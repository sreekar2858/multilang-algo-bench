import json
import pandas as pd
from pathlib import Path
import os
import matplotlib.pyplot as plt
import numpy as np


def process_logs():
    # Dictionary to store results from each language
    results = {
        "Language": [],
        "Test": [],
        "Mode": [],
        "Time": [],
        "Threads": [],
    }

    # Get the root directory and logs directory
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"
    
    # Process all log files
    for log_file in log_dir.glob("*.json"):
        with open(log_file) as f:
            data = json.load(f)
            language = data["language"]
            threads = data.get("thread_count", data.get("process_count", 0))

            # Process tests only if the data exists
            if "fibonacci_serial" in data and "fibonacci_parallel" in data:
                results["Language"].extend([language, language])
                results["Test"].extend(["Fibonacci", "Fibonacci"])
                results["Mode"].extend(["Serial", "Parallel"])
                results["Time"].extend([data["fibonacci_serial"], data["fibonacci_parallel"]])
                results["Threads"].extend([threads, threads])

            if "primes_serial" in data and "primes_parallel" in data:
                results["Language"].extend([language, language])
                results["Test"].extend(["Primes", "Primes"])
                results["Mode"].extend(["Serial", "Parallel"])
                results["Time"].extend([data["primes_serial"], data["primes_parallel"]])
                results["Threads"].extend([threads, threads])

            if "sort_serial" in data and "sort_parallel" in data:
                results["Language"].extend([language, language])
                results["Test"].extend(["QuickSort", "QuickSort"])
                results["Mode"].extend(["Serial", "Parallel"])
                results["Time"].extend([data["sort_serial"], data["sort_parallel"]])
                results["Threads"].extend([threads, threads])

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Print summary statistics
    print("\nSummary Statistics:")
    print("==================")
    for test in ["Fibonacci", "Primes", "QuickSort"]:
        test_df = df[df["Test"] == test]
        if len(test_df) > 0:  # Only print statistics if we have data for this test
            print(f"\n{test} Test:")
            for mode in ["Serial", "Parallel"]:
                mode_df = test_df[test_df["Mode"] == mode]
                if len(mode_df) > 0:  # Only print mode if we have data
                    print(f"\n{mode} Mode:")
                    print(
                        mode_df.sort_values("Time")[["Language", "Time", "Threads"]].to_string(
                            index=False, float_format=lambda x: "{:.6f}".format(x)
                        )
                    )
                    
    # Calculate speedup for each language and test
    print("\nSpeedup Factors (Serial/Parallel):")
    print("================================")
    languages = df["Language"].unique()
    for language in languages:
        print(f"\n{language}:")
        for test in ["Fibonacci", "Primes", "QuickSort"]:
            lang_test_df = df[(df["Language"] == language) & (df["Test"] == test)]
            if len(lang_test_df) == 2:  # Only if we have both serial and parallel
                serial_time = lang_test_df[lang_test_df["Mode"] == "Serial"]["Time"].iloc[0]
                parallel_time = lang_test_df[lang_test_df["Mode"] == "Parallel"]["Time"].iloc[0]
                if parallel_time > 0:  # Avoid division by zero
                    speedup = serial_time / parallel_time
                    print(f"  {test}: {speedup:.2f}x")
                else:
                    print(f"  {test}: ∞ (parallel time ≈ 0)")

def read_json_files(logs_dir='logs'):
    results = {}
    for file in os.listdir(logs_dir):
        if file.endswith('_results.json'):
            with open(os.path.join(logs_dir, file), 'r') as f:
                results[file.split('_')[0]] = json.load(f)
    return results

def create_comparison_data(results):
    # Use Python as the baseline for comparison
    baseline = results['python']
    comparison = {}
    
    for lang, data in results.items():
        comparison[lang] = {
            'primes': {
                'serial': baseline['primes_serial'] / data['primes_serial'],
                'parallel': baseline['primes_parallel'] / data['primes_parallel']
            },
            'sort': {
                'serial': baseline['sort_serial'] / data['sort_serial'],
                'parallel': baseline['sort_parallel'] / data['sort_parallel']
            },
            'fibonacci': {
                'serial': baseline['fibonacci_serial'] / data['fibonacci_serial'],
                'parallel': baseline['fibonacci_parallel'] / data['fibonacci_parallel']
            }
        }
    
    return comparison

def plot_results(results):
    languages = list(results.keys())
    tests = ['primes', 'sort', 'fibonacci']
    x = np.arange(len(languages))
    width = 0.2
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Serial tests
    for i, test in enumerate(tests):
        times = [results[lang][f'{test}_serial'] for lang in languages]
        ax1.bar(x + i*width, times, width, label=test.capitalize())
    
    ax1.set_ylabel('Time (seconds)')
    ax1.set_title('Serial Performance Comparison')
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(languages)
    ax1.legend()
    
    # Parallel tests
    for i, test in enumerate(tests):
        times = [results[lang][f'{test}_parallel'] for lang in languages]
        ax2.bar(x + i*width, times, width, label=test.capitalize())
    
    ax2.set_ylabel('Time (seconds)')
    ax2.set_title('Parallel Performance Comparison')
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(languages)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('performance_comparison.png')

def main():
    # Read all results
    results = read_json_files()
    
    # Create plots
    plot_results(results)
    
    # Generate comparison data
    comparison = create_comparison_data(results)
    
    # Save comparison data
    with open('performance_ratio.json', 'w') as f:
        json.dump(comparison, f, indent=2)

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    process_logs()
    main()