use std::env;
use std::fs;
use std::path::Path;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;

use rayon::prelude::*;
use rand::Rng;
use serde_json::json;

static THREAD_COUNT: AtomicUsize = AtomicUsize::new(0);

fn set_thread_count(count: Option<usize>) {
    let num_threads = count.unwrap_or_else(num_cpus::get);
    THREAD_COUNT.store(num_threads, Ordering::SeqCst);
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build_global()
        .unwrap();
}

// Fibonacci implementations
fn fibonacci_serial(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    fibonacci_serial(n - 1) + fibonacci_serial(n - 2)
}

fn fibonacci_dynamic(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let mut fib = vec![0u64; (n + 1) as usize];
    fib[1] = 1;
    for i in 2..=n as usize {
        fib[i] = fib[i - 1] + fib[i - 2];
    }
    fib[n as usize]
}

fn fibonacci_chunk(start: u64, end: u64) -> Vec<u64> {
    let mut fib = vec![0u64; (end + 1) as usize];
    if start <= 1 && end >= 1 {
        fib[1] = 1;
    }
    for i in (2.max(start) as usize)..=(end as usize) {
        fib[i] = fib[i - 1] + fib[i - 2];
    }
    fib[start as usize..=end as usize].to_vec()
}

fn fibonacci_parallel(n: u64) -> Vec<u64> {
    let thread_count = THREAD_COUNT.load(Ordering::SeqCst);
    let chunk_size = (n / thread_count as u64).max(1);

    (0..thread_count)
        .into_par_iter()
        .map(|i| {
            let start = i as u64 * chunk_size;
            let end = ((i + 1) as u64 * chunk_size).min(n);
            fibonacci_chunk(start, end)
        })
        .reduce(Vec::new, |mut acc, chunk| {
            acc.extend(chunk);
            acc
        })
}

fn is_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    let sqrt_n = (n as f64).sqrt() as u64;
    for i in 2..=sqrt_n {
        if n % i == 0 {
            return false;
        }
    }
    true
}

fn find_primes_serial(limit: u64) -> Vec<u64> {
    (2..=limit).filter(|&n| is_prime(n)).collect()
}

fn find_primes_parallel(limit: u64) -> Vec<u64> {
    (2..=limit).into_par_iter().filter(|&n| is_prime(n)).collect()
}

fn quicksort_serial<T: Ord + Clone>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }

    let pivot = arr.len() - 1;
    let pivot = partition(arr, pivot);

    quicksort_serial(&mut arr[0..pivot]);
    quicksort_serial(&mut arr[pivot + 1..]);
}

fn partition<T: Ord + Clone>(arr: &mut [T], pivot: usize) -> usize {
    let pivot_value = arr[pivot].clone();
    let mut store_idx = 0;

    // Move pivot to end
    arr.swap(pivot, arr.len() - 1);

    // Move all elements smaller than pivot to the left
    for i in 0..arr.len() - 1 {
        if arr[i] <= pivot_value {
            arr.swap(i, store_idx);
            store_idx += 1;
        }
    }

    // Move pivot to its final position
    arr.swap(store_idx, arr.len() - 1);
    store_idx
}

fn quicksort_parallel<T: Ord + Clone + Send>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }

    let pivot = arr.len() - 1;
    let pivot = partition(arr, pivot);

    let (left, right) = arr.split_at_mut(pivot);
    rayon::join(
        || quicksort_parallel(left),
        || quicksort_parallel(&mut right[1..]),
    );
}

fn main() {
    // Parse command line argument for thread count
    let args: Vec<String> = env::args().collect();
    let thread_count = args.get(1).and_then(|s| s.parse().ok());

    set_thread_count(thread_count);
    println!("Running with {} threads", THREAD_COUNT.load(Ordering::SeqCst));

    const PRIME_LIMIT: u64 = 100_000;
    const SORT_SIZE: usize = 1_000_000;
    const FIB_N: u64 = 35;

    // Create logs directory if it doesn't exist
    fs::create_dir_all("logs")
        .unwrap_or_else(|e| println!("Warning: Could not create logs directory: {}", e));

    println!("\nRust Fibonacci Test");

    let start = Instant::now();
    let fib_serial = fibonacci_dynamic(FIB_N);
    let serial_time_fib = start.elapsed().as_secs_f64();
    println!("Serial Time (Dynamic): {:.4} seconds", serial_time_fib);

    let start = Instant::now();
    let fib_parallel = fibonacci_parallel(FIB_N);
    let parallel_time_fib = start.elapsed().as_secs_f64();
    println!("Parallel Time: {:.4} seconds", parallel_time_fib);

    println!("\nRust Prime Numbers Test");

    let start = Instant::now();
    let primes_serial = find_primes_serial(PRIME_LIMIT);
    let serial_time_primes = start.elapsed().as_secs_f64();
    println!("Serial Time: {:.4} seconds", serial_time_primes);

    let start = Instant::now();
    let primes_parallel = find_primes_parallel(PRIME_LIMIT);
    let parallel_time_primes = start.elapsed().as_secs_f64();
    println!("Parallel Time: {:.4} seconds", parallel_time_primes);

    println!("\nRust QuickSort Test");

    let mut rng = rand::thread_rng();
    let mut test_array: Vec<i32> = (0..SORT_SIZE).map(|_| rng.gen_range(1..=1_000_000)).collect();
    let mut array_copy = test_array.clone();

    let start = Instant::now();
    quicksort_serial(&mut test_array);
    let serial_time_sort = start.elapsed().as_secs_f64();
    println!("Serial Time: {:.4} seconds", serial_time_sort);

    let start = Instant::now();
    quicksort_parallel(&mut array_copy);
    let parallel_time_sort = start.elapsed().as_secs_f64();
    println!("Parallel Time: {:.4} seconds", parallel_time_sort);

    // Write results to JSON file
    let results = json!({
        "language": "Rust",
        "thread_count": THREAD_COUNT.load(Ordering::SeqCst),
        "fibonacci_serial": serial_time_fib,
        "fibonacci_parallel": parallel_time_fib,
        "primes_serial": serial_time_primes,
        "primes_parallel": parallel_time_primes,
        "sort_serial": serial_time_sort,
        "sort_parallel": parallel_time_sort
    });

    fs::write(
        Path::new("../../logs").join("rust_results.json"),
        serde_json::to_string_pretty(&results).unwrap(),
    )
    .unwrap_or_else(|e| println!("Error writing results: {}", e));
}
