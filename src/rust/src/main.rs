use std::env;
use std::fs;
use std::path::Path;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;
use std::path::PathBuf;

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
    // Allocate a vector large enough for the full range
    let mut fib = vec![0u64; (end + 1) as usize];
    
    // Initialize the first two Fibonacci numbers if they're in our range
    if start <= 1 && end >= 1 {
        fib[1] = 1;
    }
    
    // Calculate Fibonacci numbers in the range
    for i in (2.max(start) as usize)..=(end as usize) {
        if i >= 2 {
            fib[i] = fib[i - 1] + fib[i - 2];
        }
    }
    
    // Only return the relevant slice
    // Make sure the slice bounds are valid
    let start_idx = start as usize;
    let end_idx = end as usize;
    
    // Clone the slice to avoid returning a reference to the local vector
    fib[start_idx..=end_idx].to_vec()
}

fn fibonacci_parallel(n: u64) -> Vec<u64> {
    // For small n, just compute directly
    if n < 10 {
        let mut result = Vec::with_capacity((n + 1) as usize);
        for i in 0..=n {
            if i <= 1 {
                result.push(i);
            } else {
                result.push(result[(i-1) as usize] + result[(i-2) as usize]);
            }
        }
        return result;
    }

    let thread_count = THREAD_COUNT.load(Ordering::SeqCst);
    let chunk_size = (n / thread_count as u64).max(1);
    
    // Create ranges for each thread with evenly distributed work
    let ranges: Vec<(u64, u64)> = (0..thread_count)
        .map(|i| {
            let start = i as u64 * chunk_size;
            let end = ((i + 1) as u64 * chunk_size - 1).min(n);
            (start, end)
        })
        .filter(|(start, end)| start <= end) // Skip empty ranges
        .collect();
    
    // Process ranges in parallel
    let chunks: Vec<Vec<u64>> = ranges
        .into_par_iter()
        .map(|(start, end)| fibonacci_chunk(start, end))
        .collect();
    
    // Combine chunks in the correct order
    let mut result = Vec::with_capacity((n + 1) as usize);
    for chunk in chunks {
        result.extend(chunk);
    }
    
    // Ensure we have exactly n+1 elements (0 through n)
    if result.len() > (n + 1) as usize {
        result.truncate((n + 1) as usize);
    }
    
    result
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

    // Create logs directory with robust path handling
    let logs_dir = {
        // Get current executable path
        if let Ok(exe_path) = env::current_exe() {
            // Get parent directory (bin)
            if let Some(exe_dir) = exe_path.parent() {
                // Go up one level to project root
                if let Some(project_dir) = exe_dir.parent() {
                    // Create logs dir path
                    let logs_path = project_dir.join("logs");
                    fs::create_dir_all(&logs_path).unwrap_or_else(|e| {
                        eprintln!("Warning: Could not create logs directory: {}", e);
                    });
                    logs_path
                } else {
                    // Fallback to current directory
                    PathBuf::from("logs")
                }
            } else {
                // Fallback to current directory
                PathBuf::from("logs")
            }
        } else {
            // Fallback to current directory
            PathBuf::from("logs")
        }
    };

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

    // Write results to JSON file with robust path
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

    // First try the logs_dir path
    let result = fs::write(logs_dir.join("rust_results.json"), 
                         serde_json::to_string_pretty(&results).unwrap());
    
    if let Err(e) = result {
        // If that fails, try current directory
        eprintln!("Error writing to logs directory: {}", e);
        let current_dir_file = PathBuf::from("rust_results.json");
        fs::write(&current_dir_file, serde_json::to_string_pretty(&results).unwrap())
            .unwrap_or_else(|e2| {
                eprintln!("Error writing results: {}", e2);
            });
    } else {
        println!("Results written to {}", logs_dir.join("rust_results.json").display());
    }
}
