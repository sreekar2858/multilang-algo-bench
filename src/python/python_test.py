import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from itertools import islice
from pathlib import Path
from typing import List, Tuple
import json
import random
import os
import math  # Added for optimized prime check


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
    """Optimized check if a number is prime."""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    # Only check numbers of form 6k ± 1 up to sqrt(n)
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def find_primes_serial(limit: int) -> List[int]:
    """Find all primes up to limit with optimized algorithm."""
    if limit < 2:
        return []
    
    # Handle small primes directly
    if limit < 4:
        return [2] if limit == 2 else [2, 3]
    
    # Start with known small primes
    primes = [2, 3]
    
    # Only check odd numbers starting from 5
    for n in range(5, limit + 1, 2):
        if is_prime(n):
            primes.append(n)
    
    return primes


def find_primes_range(range_tuple: Tuple[int, int]) -> List[int]:
    """Find primes in a specific range with optimized algorithm."""
    start, end = range_tuple
    
    # Handle the case where start is even
    if start % 2 == 0 and start > 2:
        start += 1
    
    # Special case for 2
    if start <= 2 and end >= 2:
        primes = [2]
        start = 3  # Start checking from 3
    else:
        primes = []
    
    # Check only odd numbers
    for n in range(max(3, start), end + 1, 2):
        if is_prime(n):
            primes.append(n)
    
    return primes


def find_primes_parallel(limit: int, process_count: int) -> List[int]:
    """Find primes in parallel using optimized chunk ranges."""
    # For small ranges, just use serial implementation
    if limit < 10000:
        return find_primes_serial(limit)

    # Special handling for small primes
    result = []
    if limit >= 2:
        result.append(2)
    
    # Only process odd numbers in parallel
    start = 3
    end = limit
    
    # For larger ranges, split work into chunks larger than the overhead
    # Balance chunk size to reduce overhead but keep good parallelism
    chunk_size = max(10000, (end - start + 1) // (process_count // 2))
    chunks = []
    
    for chunk_start in range(start, end + 1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, end)
        chunks.append((chunk_start, chunk_end))

    # Reduce the number of workers for prime calculation to reduce overhead
    # Use fewer processes but with larger chunks for better efficiency
    num_workers = min(process_count, max(4, len(chunks)))
    
    # Process chunks in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(find_primes_range, chunks))

    # Combine results (already in order by chunk)
    for chunk_primes in results:
        result.extend(chunk_primes)

    return result


def quicksort_serial(arr: List[int]) -> List[int]:
    """Optimized serial quicksort implementation."""
    if len(arr) <= 1:
        return arr
    
    # Use median-of-three for better pivot selection
    mid = len(arr) // 2
    if len(arr) >= 3:
        first, middle, last = arr[0], arr[mid], arr[-1]
        if first <= middle <= last or last <= middle <= first:
            pivot = middle
        elif middle <= first <= last or last <= first <= middle:
            pivot = first
        else:
            pivot = last
    else:
        pivot = arr[mid]
    
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort_serial(left) + middle + quicksort_serial(right)


def quicksort_chunk(arr: List[int]) -> List[int]:
    """Process a chunk for quicksort."""
    return quicksort_serial(arr)


def quicksort_parallel(arr: List[int], depth: int = 2, process_count: int = 4) -> List[int]:
    """Optimized parallel quicksort with limited depth."""
    # Base case: small array or max depth reached
    if len(arr) <= 10000 or depth <= 0:  # Increased threshold for better performance
        return quicksort_serial(arr)

    # Use median-of-three for better pivot selection
    mid = len(arr) // 2
    if len(arr) >= 3:
        first, middle, last = arr[0], arr[mid], arr[-1]
        if first <= middle <= last or last <= middle <= first:
            pivot = middle
        elif middle <= first <= last or last <= first <= middle:
            pivot = first
        else:
            pivot = last
    else:
        pivot = arr[mid]

    # Partition the array
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]

    # Only process large partitions in parallel
    if len(left) > 10000 and len(right) > 10000:  # Increased threshold for better performance
        with ProcessPoolExecutor(max_workers=min(2, process_count)) as executor:
            future_left = executor.submit(quicksort_parallel, left, depth - 1, process_count)
            right_result = quicksort_parallel(right, depth - 1, process_count)
            left_result = future_left.result()
            return left_result + middle + right_result
    elif len(left) > 10000:
        # Only left side is large enough for parallel processing
        with ProcessPoolExecutor(max_workers=1) as executor:
            future_left = executor.submit(quicksort_parallel, left, depth - 1, process_count)
            right_result = quicksort_serial(right)
            left_result = future_left.result()
            return left_result + middle + right_result
    elif len(right) > 10000:
        # Only right side is large enough for parallel processing
        with ProcessPoolExecutor(max_workers=1) as executor:
            future_right = executor.submit(quicksort_parallel, right, depth - 1, process_count)
            left_result = quicksort_serial(left)
            right_result = future_right.result()
            return left_result + middle + right_result
    else:
        # For smaller partitions, just use serial
        return quicksort_serial(left) + middle + quicksort_serial(right)


def run_tests(process_count: int = None) -> None:
    """Run all benchmarking tests."""
    # Set process count
    num_processes = set_process_count(process_count)
    print(f"Running with {num_processes} processes")

    # Get the root directory of the project
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent.parent
    logs_dir = root_dir / "logs"
    
    # Create logs directory if it doesn't exist
    logs_dir.mkdir(exist_ok=True)

    # Test parameters
    PRIME_LIMIT = 100000
    SORT_SIZE = 1000000
    FIB_N = 100000  # Fibonacci sequence up to n

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
    with open(logs_dir / "python_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    import sys

    process_count = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_tests(process_count)