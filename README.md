# multilang-algo-bench

A comprehensive benchmark suite comparing algorithmic performance across multiple programming languages, implementing both serial and parallel versions of classic algorithms.

Speed Comparison Tests
=====================

This project implements three algorithmic tests (Fibonacci sequence, prime number calculation, and QuickSort) in both serial and parallel versions across multiple programming languages.

## Project Structure

```
Speed_Comparison/
├── bin/              # Compiled executables
├── logs/             # Benchmark results in JSON format
├── src/              # Source code organized by language
│   ├── c/            # C implementation
│   ├── cpp/          # C++ implementation
│   ├── go/           # Go implementation
│   ├── java/         # Java implementation
│   ├── python/       # Python implementation
│   └── rust/         # Rust implementation
├── benchmark_results.png  # Visualization of benchmark results
├── json.jar          # JSON library for Java
├── process_logs.py   # Script to process and visualize results
└── README.md         # This file
```

## Prerequisites:
- C: GCC or compatible C compiler with pthread support
- C++: A modern C++ compiler (C++17 or later)
- Go: Go 1.11 or later
- Python: Python 3.6 or later with pandas and matplotlib
- Rust: Rust 1.31 or later (needs Cargo)
- Java: JDK 8 or later with org.json library

For Rust, you'll need to add these dependencies to Cargo.toml:
```toml
[dependencies]
rayon = "1.7"
rand = "0.8"
serde_json = "1.0"
num_cpus = "1.0"
```

For Java, you'll need the org.json library in your classpath.

For Python, install required packages:
```bash
pip install pandas matplotlib
```

## Quick Start

Clone the repository:
```bash
git clone https://github.com/yourusername/multilang-algo-bench.git
cd multilang-algo-bench
```

## Compilation Instructions:

C:
```bash
cd src/c
gcc -O3 c_test.c -o ../../bin/c_test -pthread -lm
```

C++:
```bash
cd src/cpp
g++ -O3 -std=c++17 cpp_test.cpp -o ../../bin/cpp_test -pthread
```

Go:
```bash
cd src/go
go build -o ../../bin/go_benchmark go_benchmark.go
```

Rust:
```bash
cd src/rust
rustc -O rust_test.rs -o ../../bin/rust_test
# Or using Cargo if you have a Cargo.toml
# cargo build --release
```

Java:
```bash
cd src/java
javac -cp ../../json.jar JavaTest.java -d ../../bin
```

Python doesn't need compilation.

## Running the Tests:

All implementations support configuring the number of processors/threads via command line argument. If not specified, they will use all available processors.

C:
```bash
bin/c_test [num_threads]
```

C++:
```bash
bin/cpp_test [num_threads]
```

Go:
```bash
bin/go_benchmark [num_processors]
```

Rust:
```bash
bin/rust_test [num_threads]
# Or using Cargo
# cargo run --release -- [num_threads]
```

Java:
```bash
cd bin
java -cp .:../json.jar JavaTest [num_processors]
```

Python:
```bash
python src/python/python_test.py [num_processors]
```

## Tests and Algorithms:
1. Fibonacci Sequence:
   - Serial: Dynamic programming implementation
   - Parallel: Chunk-based calculation with configurable thread count
   - Test size: First 35 numbers in sequence

2. Prime Numbers:
   - Serial: Simple trial division
   - Parallel: Distributed workload across threads
   - Test size: Numbers up to 100,000

3. QuickSort:
   - Serial: Classic recursive implementation
   - Parallel: Multi-threaded with depth control
   - Test size: 1,000,000 random integers

## Analyzing Results:
After running the tests, each implementation will create a JSON log file in the `logs` directory. To analyze and visualize the results, run:

```bash
python process_logs.py
```

This will:
1. Read all benchmark results from the logs directory
2. Generate comparative statistics for all three tests
3. Create visualization plots saved as 'benchmark_results.png'
4. Display thread/processor count used by each implementation

## Implementation Details:
- The parallel versions utilize:
  * C: POSIX threads (pthreads) for multi-threading
  * C++: std::async and futures for task parallelism
  * Go: goroutines and channels for concurrent execution
  * Python: multiprocessing for parallel processing
  * Rust: rayon for parallel iterators and join patterns
  * Java: Fork/Join framework and parallel streams
- Optimizations include:
  * Dynamic programming for Fibonacci calculation
  * Threshold-based parallelization for sorting
  * Configurable thread/process count for all tests
  * Recursion depth control for parallel QuickSort
  * Memory-efficient chunk processing
  * Platform-specific processor detection
- Results logging includes:
  * Execution times for all tests (serial and parallel)
  * Thread/processor count used
  * JSON format for easy parsing and comparison
  * Visualization with comparative bar charts
- Cross-platform support:
  * Windows and POSIX systems supported
  * Automatic processor count detection
  * Consistent JSON output format
  * Platform-specific directory handling