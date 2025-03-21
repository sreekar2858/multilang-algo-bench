import json
import re
from pathlib import Path
import os
import matplotlib.pyplot as plt
import numpy as np
import re


def process_logs():
    # Dictionary to store results from each language
    results = {
        "Language": [],
        "Test": [],
        "Mode": [],
        "Time": [],
        "Threads": [],
    }

    # Dictionary to store consolidated results for JSON export
    consolidated_metrics = {
        "absolute_times": {},
        "speedup_factors": {},
        "mpi_comparisons": {},
        "relative_to_python": {}
    }

    # Get the root directory and logs directory
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"

    # Process all log files
    for log_file in log_dir.glob("*.json"):
        with open(log_file) as f:
            try:
                data = json.load(f)
                language = data["language"]
                threads = data.get("thread_count", data.get("process_count", 0))

                # Initialize language entry in consolidated metrics
                if language not in consolidated_metrics["absolute_times"]:
                    consolidated_metrics["absolute_times"][language] = {
                        "threads": threads,
                        "fibonacci": {"serial": None, "parallel": None},
                        "primes": {"serial": None, "parallel": None},
                        "quicksort": {"serial": None, "parallel": None}
                    }

                # Process tests only if the data exists
                if "fibonacci_serial" in data and "fibonacci_parallel" in data:
                    results["Language"].extend([language, language])
                    results["Test"].extend(["Fibonacci", "Fibonacci"])
                    results["Mode"].extend(["Serial", "Parallel"])
                    results["Time"].extend([data["fibonacci_serial"], data["fibonacci_parallel"]])
                    results["Threads"].extend([threads, threads])
                    
                    # Add to consolidated metrics
                    consolidated_metrics["absolute_times"][language]["fibonacci"]["serial"] = data["fibonacci_serial"]
                    consolidated_metrics["absolute_times"][language]["fibonacci"]["parallel"] = data["fibonacci_parallel"]

                if "primes_serial" in data and "primes_parallel" in data:
                    results["Language"].extend([language, language])
                    results["Test"].extend(["Primes", "Primes"])
                    results["Mode"].extend(["Serial", "Parallel"])
                    results["Time"].extend([data["primes_serial"], data["primes_parallel"]])
                    results["Threads"].extend([threads, threads])
                    
                    # Add to consolidated metrics
                    consolidated_metrics["absolute_times"][language]["primes"]["serial"] = data["primes_serial"]
                    consolidated_metrics["absolute_times"][language]["primes"]["parallel"] = data["primes_parallel"]

                if "sort_serial" in data and "sort_parallel" in data:
                    results["Language"].extend([language, language])
                    results["Test"].extend(["QuickSort", "QuickSort"])
                    results["Mode"].extend(["Serial", "Parallel"])
                    results["Time"].extend([data["sort_serial"], data["sort_parallel"]])
                    results["Threads"].extend([threads, threads])

                    # Add to consolidated metrics
                    consolidated_metrics["absolute_times"][language]["quicksort"]["serial"] = data["sort_serial"]
                    consolidated_metrics["absolute_times"][language]["quicksort"]["parallel"] = data["sort_parallel"]
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON in {log_file}")
                continue

    # Print summary statistics
    print("\nSummary Statistics:")
    print("==================")
    for test in ["Fibonacci", "Primes", "QuickSort"]:
        print(f"\n{test} Test:")
        for mode in ["Serial", "Parallel"]:
            print(f"\n{mode} Mode:")
            
            # Get the rows for this test and mode
            rows = []
            for i in range(len(results["Language"])):
                if results["Test"][i] == test and results["Mode"][i] == mode:
                    rows.append({
                        "Language": results["Language"][i],
                        "Time": results["Time"][i],
                        "Threads": results["Threads"][i]
                    })
            
            # Sort rows by time
            rows.sort(key=lambda x: x["Time"])
            
            # Format and print
            if rows:
                # Print header
                print(f"{'Language':<15} {'Time':<15} {'Threads'}")
                print("-" * 40)
                
                # Print rows
                for row in rows:
                    print(f"{row['Language']:<15} {row['Time']:<15.6f} {row['Threads']}")
            else:
                print("No data available")
                    
    # Calculate speedup for each language and test
    print("\nSpeedup Factors (Serial/Parallel):")
    print("================================")
    
    # Group by language and test
    languages = set(results["Language"])
    
    for language in sorted(languages):
        # Initialize speedup entry in consolidated metrics
        if language not in consolidated_metrics["speedup_factors"]:
            consolidated_metrics["speedup_factors"][language] = {
                "fibonacci": None,
                "primes": None,
                "quicksort": None
            }
        
        print(f"\n{language}:")
        for test in ["Fibonacci", "Primes", "QuickSort"]:
            test_key = test.lower()
            if test_key == "quicksort":
                test_key = "quicksort"
                
            # Find serial and parallel times for this language and test
            serial_time = None
            parallel_time = None
            
            for i in range(len(results["Language"])):
                if results["Language"][i] == language and results["Test"][i] == test:
                    if results["Mode"][i] == "Serial":
                        serial_time = results["Time"][i]
                    elif results["Mode"][i] == "Parallel":
                        parallel_time = results["Time"][i]
            
            if serial_time is not None and parallel_time is not None:
                if parallel_time > 0:  # Avoid division by zero
                    speedup = serial_time / parallel_time
                    print(f"  {test}: {speedup:.2f}x")
                    
                    # Add to consolidated metrics
                    consolidated_metrics["speedup_factors"][language][test_key] = speedup
                else:
                    print(f"  {test}: ∞ (parallel time ≈ 0)")
                    
                    # Add to consolidated metrics (using infinity)
                    consolidated_metrics["speedup_factors"][language][test_key] = float('inf')
    
    # Group MPI and non-MPI implementations for comparison
    print("\nMPI vs Non-MPI Comparison:")
    print("=========================")
    
    # Find matching MPI and non-MPI implementations
    mpi_langs = [lang for lang in languages if "MPI" in lang]
    regular_langs = [lang for lang in languages if "MPI" not in lang]
    
    # For each MPI implementation, find its regular counterpart
    for mpi_lang in mpi_langs:
        # Extract the base language name (remove " MPI" suffix)
        base_lang = re.sub(r' MPI$', '', mpi_lang)
        
        # Find the corresponding regular implementation
        if base_lang in regular_langs:
            # Initialize MPI comparison entry in consolidated metrics
            comparison_key = f"{base_lang}_vs_{mpi_lang.replace(' ', '_')}"
            consolidated_metrics["mpi_comparisons"][comparison_key] = {
                "fibonacci": {},
                "primes": {},
                "quicksort": {}
            }
            
            print(f"\n{base_lang} vs {mpi_lang}:")
            
            for test in ["Fibonacci", "Primes", "QuickSort"]:
                test_key = test.lower()
                if test_key == "quicksort":
                    test_key = "quicksort"
                    
                # Find serial and parallel times for both implementations
                mpi_serial = None
                mpi_parallel = None
                reg_serial = None
                reg_parallel = None
                
                for i in range(len(results["Language"])):
                    if results["Test"][i] == test:
                        if results["Language"][i] == mpi_lang:
                            if results["Mode"][i] == "Serial":
                                mpi_serial = results["Time"][i]
                            elif results["Mode"][i] == "Parallel":
                                mpi_parallel = results["Time"][i]
                        elif results["Language"][i] == base_lang:
                            if results["Mode"][i] == "Serial":
                                reg_serial = results["Time"][i]
                            elif results["Mode"][i] == "Parallel":
                                reg_parallel = results["Time"][i]
                
                # Calculate speedup ratios
                if all(x is not None for x in [mpi_serial, mpi_parallel, reg_serial, reg_parallel]):
                    mpi_speedup = mpi_serial / mpi_parallel if mpi_parallel > 0 else float('inf')
                    reg_speedup = reg_serial / reg_parallel if reg_parallel > 0 else float('inf')
                    
                    print(f"  {test}:")
                    print(f"    {base_lang} Serial: {reg_serial:.6f}s, Parallel: {reg_parallel:.6f}s, Speedup: {reg_speedup:.2f}x")
                    print(f"    {mpi_lang} Serial: {mpi_serial:.6f}s, Parallel: {mpi_parallel:.6f}s, Speedup: {mpi_speedup:.2f}x")
                    
                    # Calculate MPI vs regular ratio for parallel performance
                    if reg_parallel > 0 and mpi_parallel > 0:
                        parallel_ratio = reg_parallel / mpi_parallel
                        print(f"    MPI Parallel Performance Gain: {parallel_ratio:.2f}x")
                        
                        # Add to consolidated metrics
                        consolidated_metrics["mpi_comparisons"][comparison_key][test_key] = {
                            "regular": {
                                "serial": reg_serial,
                                "parallel": reg_parallel,
                                "speedup": reg_speedup
                            },
                            "mpi": {
                                "serial": mpi_serial,
                                "parallel": mpi_parallel,
                                "speedup": mpi_speedup
                            },
                            "mpi_performance_gain": parallel_ratio
                        }

    return consolidated_metrics, results


def read_json_files(logs_dir='logs'):
    """Read all JSON results files from the logs directory"""
    results = {}
    try:
        for file in os.listdir(logs_dir):
            if file.endswith('_results.json'):
                try:
                    with open(os.path.join(logs_dir, file), 'r') as f:
                        key = file.split('_')[0]
                        # Handle MPI variants by including 'mpi' in the key if present
                        if 'mpi' in file:
                            key += '_mpi'
                        results[key] = json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse JSON in {file}")
                    continue
    except FileNotFoundError:
        print(f"Warning: Logs directory '{logs_dir}' not found")
    
    return results


def create_comparison_data(results, consolidated_metrics):
    """Create relative performance comparison data using Python as baseline"""
    # Check if Python results exist to use as baseline
    if 'python' not in results:
        print("Python results not found, can't create relative comparison")
        return
    
    baseline = results['python']
    consolidated_metrics["relative_to_python"] = {}
    
    for lang, data in results.items():
        # Skip if required data is missing
        if not all(key in data for key in ["fibonacci_serial", "fibonacci_parallel", 
                                          "primes_serial", "primes_parallel", 
                                          "sort_serial", "sort_parallel"]):
            continue
        
        # Initialize language in relative performance metrics
        consolidated_metrics["relative_to_python"][lang] = {
            "fibonacci": {"serial": None, "parallel": None},
            "primes": {"serial": None, "parallel": None},
            "quicksort": {"serial": None, "parallel": None}
        }
        
        # Process Fibonacci test
        if baseline["fibonacci_serial"] > 0 and data["fibonacci_serial"] > 0:
            relative_perf = baseline["fibonacci_serial"] / data["fibonacci_serial"]
            consolidated_metrics["relative_to_python"][lang]["fibonacci"]["serial"] = relative_perf
        
        if baseline["fibonacci_parallel"] > 0 and data["fibonacci_parallel"] > 0:
            relative_perf = baseline["fibonacci_parallel"] / data["fibonacci_parallel"]
            consolidated_metrics["relative_to_python"][lang]["fibonacci"]["parallel"] = relative_perf
        
        # Process Primes test
        if baseline["primes_serial"] > 0 and data["primes_serial"] > 0:
            relative_perf = baseline["primes_serial"] / data["primes_serial"]
            consolidated_metrics["relative_to_python"][lang]["primes"]["serial"] = relative_perf
        
        if baseline["primes_parallel"] > 0 and data["primes_parallel"] > 0:
            relative_perf = baseline["primes_parallel"] / data["primes_parallel"]
            consolidated_metrics["relative_to_python"][lang]["primes"]["parallel"] = relative_perf
        
        # Process QuickSort test
        if baseline["sort_serial"] > 0 and data["sort_serial"] > 0:
            relative_perf = baseline["sort_serial"] / data["sort_serial"]
            consolidated_metrics["relative_to_python"][lang]["quicksort"]["serial"] = relative_perf
        
        if baseline["sort_parallel"] > 0 and data["sort_parallel"] > 0:
            relative_perf = baseline["sort_parallel"] / data["sort_parallel"]
            consolidated_metrics["relative_to_python"][lang]["quicksort"]["parallel"] = relative_perf


def create_bar_plots(results):
    """Create bar plots to visualize benchmark results"""
    # Extract unique languages and tests
    languages = list(sorted(set(results["Language"])))
    tests = ["Fibonacci", "Primes", "QuickSort"]
    
    # Set up plot colors and width
    colors = {
        "Serial": "blue",
        "Parallel": "orange"
    }
    bar_width = 0.35
    
    # Create figure with 3 subplots (one for each test)
    fig, axes = plt.subplots(len(tests), 1, figsize=(12, 15))
    fig.suptitle('Benchmark Results: Serial vs Parallel Execution Time', fontsize=16)
    
    # Create subplots for each test
    for i, test in enumerate(tests):
        ax = axes[i]
        
        # Filter data for this test
        test_data = {
            "Language": [],
            "Serial": [],
            "Parallel": []
        }
        
        for j, lang in enumerate(languages):
            serial_time = None
            parallel_time = None
            
            for k in range(len(results["Language"])):
                if results["Language"][k] == lang and results["Test"][k] == test:
                    if results["Mode"][k] == "Serial":
                        serial_time = results["Time"][k]
                    elif results["Mode"][k] == "Parallel":
                        parallel_time = results["Time"][k]
            
            if serial_time is not None and parallel_time is not None:
                test_data["Language"].append(lang)
                test_data["Serial"].append(serial_time)
                test_data["Parallel"].append(parallel_time)
        
        # Sort data by serial execution time
        indices = sorted(range(len(test_data["Serial"])), key=lambda k: test_data["Serial"][k])
        sorted_langs = [test_data["Language"][i] for i in indices]
        sorted_serial = [test_data["Serial"][i] for i in indices]
        sorted_parallel = [test_data["Parallel"][i] for i in indices]
        
        # Create x positions for bars
        x = np.arange(len(sorted_langs))
        
        # Plot bars
        ax.bar(x - bar_width/2, sorted_serial, bar_width, label='Serial', color=colors["Serial"])
        ax.bar(x + bar_width/2, sorted_parallel, bar_width, label='Parallel', color=colors["Parallel"])
        
        # Add labels and legend
        ax.set_title(f'{test} Test')
        ax.set_xlabel('Language')
        ax.set_ylabel('Execution Time (seconds)')
        ax.set_xticks(x)
        ax.set_xticklabels(sorted_langs, rotation=45)
        ax.legend()
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add value labels on top of bars
        for j, v in enumerate(sorted_serial):
            if v < 0.001:
                ax.text(j - bar_width/2, v + 0.00005, f'{v:.6f}', ha='center', va='bottom', fontsize=8, rotation=90)
            else:
                ax.text(j - bar_width/2, v + 0.00005, f'{v:.4f}', ha='center', va='bottom', fontsize=8, rotation=90)
        
        for j, v in enumerate(sorted_parallel):
            if v < 0.001:
                ax.text(j + bar_width/2, v + 0.00005, f'{v:.6f}', ha='center', va='bottom', fontsize=8, rotation=90)
            else:
                ax.text(j + bar_width/2, v + 0.00005, f'{v:.4f}', ha='center', va='bottom', fontsize=8, rotation=90)
    
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig('benchmark_results.png', dpi=300)
    print("\nVisualization saved as benchmark_results.png")
    
    # Create a speedup comparison plot
    create_speedup_plot(results, languages, tests)


def create_speedup_plot(results, languages, tests):
    """Create a bar plot showing speedup factors for each language and test"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Organize data for plotting
    plot_data = []
    for lang in sorted(languages):
        lang_data = {"Language": lang}
        for test in tests:
            serial_time = None
            parallel_time = None
            
            for i in range(len(results["Language"])):
                if results["Language"][i] == lang and results["Test"][i] == test:
                    if results["Mode"][i] == "Serial":
                        serial_time = results["Time"][i]
                    elif results["Mode"][i] == "Parallel":
                        parallel_time = results["Time"][i]
            
            if serial_time is not None and parallel_time is not None and parallel_time > 0:
                speedup = serial_time / parallel_time
                lang_data[test] = speedup
            else:
                lang_data[test] = 0
        
        plot_data.append(lang_data)
    
    # Determine positions for bars
    x = np.arange(len(plot_data))
    width = 0.25
    
    # Plot bars for each test
    for i, test in enumerate(tests):
        values = [data[test] for data in plot_data]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, values, width, label=test)
        
        # Add value labels on top of bars
        for j, v in enumerate(values):
            if v > 0:
                ax.text(j + offset, v + 0.05, f'{v:.2f}x', ha='center', va='bottom', fontsize=8)
    
    # Add reference line at y=1 (neutral speedup)
    ax.axhline(y=1, color='r', linestyle='-', alpha=0.3)
    
    # Add labels and legend
    ax.set_title('Speedup Factors (Serial/Parallel) by Language and Test')
    ax.set_xlabel('Language')
    ax.set_ylabel('Speedup Factor (higher is better)')
    ax.set_xticks(x)
    ax.set_xticklabels([data["Language"] for data in plot_data], rotation=45)
    ax.legend()
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('speedup_comparison.png', dpi=300)
    print("Speedup comparison visualization saved as speedup_comparison.png")

<<<<<<< HEAD

def create_mpi_comparison_plot(results, mpi_langs, regular_langs):
    """Create bar plots comparing MPI and non-MPI implementations"""
    # Find pairs of MPI and regular implementations
    mpi_pairs = []
    for mpi_lang in mpi_langs:
        base_lang = re.sub(r' MPI$', '', mpi_lang)
        if base_lang in regular_langs:
            mpi_pairs.append((base_lang, mpi_lang))
=======
def update_readme_performance_tables(comparison_data):
    """Updates the performance tables in README.md with the latest benchmark results"""
    readme_path = Path(__file__).parent / "README.md"
    
    if not readme_path.exists():
        print("README.md not found, skipping update.")
        return
    
    with open(readme_path, 'r') as f:
        readme_content = f.read()
    
    # Format serial implementation performance table
    serial_table = "| Language | Fibonacci | Prime Numbers | QuickSort |\n"
    serial_table += "|----------|-----------|---------------|----------|\n"
    
    for lang in ['rust', 'cpp', 'c', 'go', 'java', 'python']:
        lang_name = lang.capitalize()
        if lang == 'cpp':
            lang_name = "C++"
        
        fib_value = comparison_data[lang]['fibonacci']['serial']
        prime_value = comparison_data[lang]['primes']['serial']
        sort_value = comparison_data[lang]['sort']['serial']
        
        serial_table += f"| {lang_name}     | {fib_value:.2f}x   | {prime_value:.2f}x         | {sort_value:.2f}x    |\n"
    
    # Format parallel implementation performance table
    parallel_table = "| Language | Fibonacci | Prime Numbers | QuickSort |\n"
    parallel_table += "|----------|-----------|---------------|----------|\n"
    
    for lang in ['rust', 'cpp', 'c', 'go', 'java', 'python']:
        lang_name = lang.capitalize()
        if lang == 'cpp':
            lang_name = "C++"
        
        fib_value = comparison_data[lang]['fibonacci']['parallel']
        prime_value = comparison_data[lang]['primes']['parallel']
        sort_value = comparison_data[lang]['sort']['parallel']
        
        parallel_table += f"| {lang_name}     | {fib_value:.2f}x   | {prime_value:.2f}x         | {sort_value:.2f}x    |\n"
    
    # Generate key observations based on the data
    observations = []
    
    # Find highest serial fibonacci
    serial_fib_max = max(comparison_data.items(), key=lambda x: x[1]['fibonacci']['serial'])
    observations.append(f"- In serial implementations, {serial_fib_max[0].capitalize() if serial_fib_max[0] != 'cpp' else 'C++'} shows exceptional performance for Fibonacci ({serial_fib_max[1]['fibonacci']['serial']:.2f}x faster than Python)")
    
    # Find highest parallel quicksort
    parallel_qs_max = max(comparison_data.items(), key=lambda x: x[1]['sort']['parallel'])
    observations.append(f"- {parallel_qs_max[0].capitalize() if parallel_qs_max[0] != 'cpp' else 'C++'} excels at QuickSort in parallel implementation ({parallel_qs_max[1]['sort']['parallel']:.2f}x faster than Python)")
    
    # Find highest prime numbers (both)
    serial_prime_max = max(comparison_data.items(), key=lambda x: x[1]['primes']['serial'])
    parallel_prime_max = max(comparison_data.items(), key=lambda x: x[1]['primes']['parallel'])
    
    if serial_prime_max[0] == parallel_prime_max[0]:
        observations.append(f"- For prime numbers, {serial_prime_max[0].capitalize() if serial_prime_max[0] != 'cpp' else 'C++'} leads in both serial ({serial_prime_max[1]['primes']['serial']:.2f}x) and parallel ({parallel_prime_max[1]['primes']['parallel']:.2f}x) performance")
    else:
        observations.append(f"- {serial_prime_max[0].capitalize() if serial_prime_max[0] != 'cpp' else 'C++'} has the best serial prime number performance ({serial_prime_max[1]['primes']['serial']:.2f}x), while {parallel_prime_max[0].capitalize() if parallel_prime_max[0] != 'cpp' else 'C++'} leads in parallel ({parallel_prime_max[1]['primes']['parallel']:.2f}x)")
    
    # Find highest parallel fibonacci
    parallel_fib_max = max(comparison_data.items(), key=lambda x: x[1]['fibonacci']['parallel'])
    observations.append(f"- {parallel_fib_max[0].capitalize() if parallel_fib_max[0] != 'cpp' else 'C++'} shows the best parallel Fibonacci performance ({parallel_fib_max[1]['fibonacci']['parallel']:.2f}x faster than Python)")
    
    # Check for good Java performance in parallel quicksort (common case)
    if comparison_data['java']['sort']['parallel'] > 25:
        observations.append(f"- Java maintains strong QuickSort performance in parallel implementation ({comparison_data['java']['sort']['parallel']:.2f}x faster than Python)")
    
    observations_text = "\n".join(observations)
    
    # Note about the data
    note_text = "Note: Higher numbers indicate better performance relative to Python. Values are automatically extracted from the performance_ratio.json file."
    
    # Replace the performance sections using regex to find the correct location
    serial_pattern = r"### Serial Implementation Performance\s*\|\s*Language.*?\|\s*Python\s*\|\s*1\.00x\s*\|\s*1\.00x\s*\|\s*1\.00x\s*\|"
    parallel_pattern = r"### Parallel Implementation Performance\s*\|\s*Language.*?\|\s*Python\s*\|\s*1\.00x\s*\|\s*1\.00x\s*\|\s*1\.00x\s*\|"
    observations_pattern = r"Key observations:.*?Note:"
    
    new_serial_section = "### Serial Implementation Performance\n\n" + serial_table
    new_parallel_section = "### Parallel Implementation Performance\n\n" + parallel_table
    new_observations_section = "Key observations:\n" + observations_text + "\n\n" + note_text
    
    # Replace sections in the README
    readme_content = re.sub(serial_pattern, new_serial_section, readme_content, flags=re.DOTALL)
    readme_content = re.sub(parallel_pattern, new_parallel_section, readme_content, flags=re.DOTALL)
    readme_content = re.sub(observations_pattern, new_observations_section, readme_content, flags=re.DOTALL)
    
    # Write the updated README file
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print("README.md performance tables updated successfully with the latest benchmark results.")

def main():
    # Read all results
    results = read_json_files()
>>>>>>> 82243768be887e622aebfbf4e0cd541694e77a30
    
    if not mpi_pairs:
        return  # No MPI pairs found
    
    # Create figure
    fig, axes = plt.subplots(len(mpi_pairs), 3, figsize=(15, len(mpi_pairs) * 5))
    fig.suptitle('MPI vs Regular Implementation Comparison', fontsize=16)
    
<<<<<<< HEAD
    # Set test names 
    tests = ["Fibonacci", "Primes", "QuickSort"]
    
    # Only one pair, need to reshape axes
    if len(mpi_pairs) == 1:
        axes = np.array([axes])
    
    # Create plots for each pair and test
    for i, (reg_lang, mpi_lang) in enumerate(mpi_pairs):
        for j, test in enumerate(tests):
            ax = axes[i, j]
            
            # Get data for this pair and test
            reg_serial = None
            reg_parallel = None
            mpi_serial = None
            mpi_parallel = None
            
            for k in range(len(results["Language"])):
                if results["Test"][k] == test:
                    if results["Language"][k] == reg_lang:
                        if results["Mode"][k] == "Serial":
                            reg_serial = results["Time"][k]
                        elif results["Mode"][k] == "Parallel":
                            reg_parallel = results["Time"][k]
                    elif results["Language"][k] == mpi_lang:
                        if results["Mode"][k] == "Serial":
                            mpi_serial = results["Time"][k]
                        elif results["Mode"][k] == "Parallel":
                            mpi_parallel = results["Time"][k]
            
            # Skip if data is incomplete
            if any(x is None for x in [reg_serial, reg_parallel, mpi_serial, mpi_parallel]):
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
                continue
            
            # Calculate speedup factors
            reg_speedup = reg_serial / reg_parallel if reg_parallel > 0 else float('inf')
            mpi_speedup = mpi_serial / mpi_parallel if mpi_parallel > 0 else float('inf')
            parallel_gain = reg_parallel / mpi_parallel if mpi_parallel > 0 else float('inf')
            
            # Prepare data for plotting
            languages = [reg_lang, mpi_lang]
            serial_times = [reg_serial, mpi_serial]
            parallel_times = [reg_parallel, mpi_parallel]
            speedups = [reg_speedup, mpi_speedup]
            
            # Set positions for bars
            x = np.arange(len(languages))
            bar_width = 0.35
            
            # Create plot with two sets of bars
            ax.bar(x - bar_width/2, serial_times, bar_width, label='Serial', color='blue')
            ax.bar(x + bar_width/2, parallel_times, bar_width, label='Parallel', color='orange')
            
            # Add title and labels
            ax.set_title(f'{test} - {reg_lang} vs {mpi_lang}')
            ax.set_xlabel('Implementation')
            ax.set_ylabel('Execution Time (seconds)')
            ax.set_xticks(x)
            ax.set_xticklabels(languages)
            ax.legend()
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Annotate with speedup information
            for k, lang in enumerate(languages):
                ax.text(k, 0.85 * max(serial_times + parallel_times), 
                       f'Speedup: {speedups[k]:.2f}x', 
                       ha='center', va='center', bbox=dict(boxstyle='round', alpha=0.1))
            
            # Annotate performance gain
            ax.text(0.5, 0.95 * max(serial_times + parallel_times),
                  f'MPI Parallel Gain: {parallel_gain:.2f}x',
                  ha='center', va='center', 
                  bbox=dict(boxstyle='round', alpha=0.1, color='orange' if parallel_gain > 1 else 'gray'))
    
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig('mpi_comparison.png', dpi=300)
    print("MPI comparison visualization saved as mpi_comparison.png")

=======
    # Save comparison data
    with open('performance_ratio.json', 'w') as f:
        json.dump(comparison, f, indent=2)
    
    # Update README.md with the latest performance data
    update_readme_performance_tables(comparison)
>>>>>>> 82243768be887e622aebfbf4e0cd541694e77a30

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Process logs and generate summary
    consolidated_metrics, raw_results = process_logs()
    
    # Read all JSON results for additional processing
    json_results = read_json_files()
    
    # Create performance comparison data relative to Python
    create_comparison_data(json_results, consolidated_metrics)
    
    # Export all consolidated metrics to a single JSON file
    output_file = "benchmark_metrics.json"
    with open(output_file, 'w') as f:
        json.dump(consolidated_metrics, f, indent=2)
    
    print(f"\nAll benchmark metrics exported to {output_file}")
    print("The file includes:")
    print("  - Absolute execution times for all languages and tests")
    print("  - Speedup factors (serial/parallel) for each language")
    print("  - MPI vs non-MPI implementation comparisons")
    print("  - Performance relative to Python baseline")
    
    # Create visualizations
    try:
        # Extract MPI and regular languages for comparison
        languages = set(raw_results["Language"])
        mpi_langs = [lang for lang in languages if "MPI" in lang]
        regular_langs = [lang for lang in languages if "MPI" not in lang]
        
        create_bar_plots(raw_results)
        create_mpi_comparison_plot(raw_results, mpi_langs, regular_langs)
        print("\nVisualization completed successfully")
    except Exception as e:
        print(f"\nError creating visualizations: {str(e)}")
        print("JSON metrics were still exported successfully")