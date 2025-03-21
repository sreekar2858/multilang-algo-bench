import json
import pandas as pd
from pathlib import Path
import os


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


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    process_logs()