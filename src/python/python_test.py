import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from itertools import islice
from pathlib import Path
from typing import List, Tuple
import json
import random


def set_process_count(count: int = None) -> int:
    """Configure the number of processes to use."""
    if count is None:
        return mp.cpu_count()
    return min(count, mp.cpu_count())


def fibonacci_serial(n: int) -> int:
    """Calculate nth Fibonacci number serially."""
    if n <= 1:
        return n
    return fibonacci_serial(n - 1) + fibonacci_serial(n - 2)


def fibonacci_dynamic(n: int) -> int:
    """Calculate nth Fibonacci number using dynamic programming."""
    if n <= 1:
        return n
    fib = [0] * (n + 1)
    fib[1] = 1
    for i in range(2, n + 1):
        fib[i] = fib[i - 1] + fib[i - 2]
    return fib[n]


def fibonacci_chunk(range_tuple: Tuple[int, int]) -> List[int]:
    """Calculate Fibonacci numbers for a range."""
    start, end = range_tuple
    fib = [0] * (end + 1)
    if start <= 1 and end >= 1:
        fib[1] = 1
    for i in range(max(2, start), end + 1):
        fib[i] = fib[i - 1] + fib[i - 2]
    return fib[start : end + 1]


def fibonacci_parallel(n: int, process_count: int) -> List[int]:
    """Parallel implementation of Fibonacci using chunks."""
    # For small n, just use the serial implementation
    if n < 100:
        return [fibonacci_dynamic(i) for i in range(n)]

    # Create chunks to distribute work
    chunk_size = max(1, n // process_count)
    chunks = []
    for i in range(0, n, chunk_size):
        end = min(i + chunk_size, n)
        chunks.append((i, end))

    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=process_count) as executor:
        results = list(executor.map(fibonacci_chunk, chunks))

    # Combine results
    return [item for sublist in results for item in sublist]


def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def find_primes_serial(limit: int) -> List[int]:
    """Find all primes up to limit."""
    return [n for n in range(2, limit + 1) if is_prime(n)]


def find_primes_range(range_tuple: Tuple[int, int]) -> List[int]:
    """Find primes in a specific range."""
    start, end = range_tuple
    return [n for n in range(start, end + 1) if is_prime(n)]


def find_primes_parallel(limit: int, process_count: int) -> List[int]:
    """Find primes in parallel using chunk ranges."""
    # For small ranges, just use serial implementation
    if limit < 10000:
        return find_primes_serial(limit)

    # For larger ranges, split work into chunks larger than the overhead
    chunk_size = max(5000, limit // process_count)
    chunks = []
    for start in range(2, limit + 1, chunk_size):
        end = min(start + chunk_size - 1, limit)
        chunks.append((start, end))

    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=process_count) as executor:
        results = list(executor.map(find_primes_range, chunks))

    # Combine results (already in order by chunk)
    all_primes = []
    for chunk_primes in results:
        all_primes.extend(chunk_primes)

    return all_primes


def quicksort_serial(arr: List[int]) -> List[int]:
    """Serial quicksort implementation."""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort_serial(left) + middle + quicksort_serial(right)


def quicksort_chunk(arr: List[int]) -> List[int]:
    """Process a chunk for quicksort."""
    return quicksort_serial(arr)


def quicksort_parallel(arr: List[int], depth: int = 2, process_count: int = 4) -> List[int]:
    """Simple parallel quicksort with limited depth."""
    # Base case: small array or max depth reached
    if len(arr) <= 100000 or depth <= 0:
        return quicksort_serial(arr)

    # Partition the array
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    # Only process large partitions in parallel
    if len(left) > 50000 and len(right) > 50000:
        with ProcessPoolExecutor(max_workers=2) as executor:
            future_left = executor.submit(quicksort_parallel, left, depth - 1, process_count)
            right_result = quicksort_serial(right)
            left_result = future_left.result()
            return left_result + middle + right_result

    # For smaller partitions, just use serial
    return quicksort_serial(left) + middle + quicksort_serial(right)


def run_tests(process_count: int = None) -> None:
    """Run all benchmarking tests."""
    # Set process count
    num_processes = set_process_count(process_count)
    print(f"Running with {num_processes} processes")

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Test parameters
    PRIME_LIMIT = 100000
    SORT_SIZE = 1000000
    FIB_N = 35  # Fibonacci sequence up to n

    results = {
        "language": "Python",
        "primes_serial": 0,
        "primes_parallel": 0,
        "sort_serial": 0,
        "sort_parallel": 0,
        "fibonacci_serial": 0,
        "fibonacci_parallel": 0,
        "process_count": num_processes,
    }

    # Fibonacci sequence test
    print("\nPython Fibonacci Sequence Test")
    start_time = time.time()
    fib_serial = fibonacci_dynamic(FIB_N)  # noqa: F841
    results["fibonacci_serial"] = time.time() - start_time
    print(f"Serial Time (Dynamic): {results['fibonacci_serial']:.4f} seconds")

    start_time = time.time()
    fib_parallel = fibonacci_parallel(FIB_N, num_processes)  # noqa: F841
    results["fibonacci_parallel"] = time.time() - start_time
    print(f"Parallel Time: {results['fibonacci_parallel']:.4f} seconds")

    # Prime numbers test
    print("\nPython Prime Numbers Test")
    start_time = time.time()
    primes_serial = find_primes_serial(PRIME_LIMIT)  # noqa: F841
    results["primes_serial"] = time.time() - start_time
    print(f"Serial Time: {results['primes_serial']:.4f} seconds")

    start_time = time.time()
    primes_parallel = find_primes_parallel(PRIME_LIMIT, num_processes)  # noqa: F841
    results["primes_parallel"] = time.time() - start_time
    print(f"Parallel Time: {results['primes_parallel']:.4f} seconds")

    # QuickSort test
    print("\nPython QuickSort Test")
    test_array = [random.randint(1, 1000000) for _ in range(SORT_SIZE)]
    array_copy = test_array.copy()

    start_time = time.time()
    sorted_serial = quicksort_serial(test_array)  # noqa: F841
    results["sort_serial"] = time.time() - start_time
    print(f"Serial Time: {results['sort_serial']:.4f} seconds")

    start_time = time.time()
    sorted_parallel = quicksort_parallel(array_copy, depth=2, process_count=num_processes)  # noqa: F841
    results["sort_parallel"] = time.time() - start_time
    print(f"Parallel Time: {results['sort_parallel']:.4f} seconds")

    # Write results to JSON file
    with open("logs/python_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    import sys

    process_count = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_tests(process_count)