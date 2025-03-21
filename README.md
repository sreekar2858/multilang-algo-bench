# multilang-algo-bench

🚀 Multi-language benchmark suite comparing serial vs parallel algorithm implementations in C, C++, Go, Java, Python, and Rust.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Lint](https://github.com/sreekar2858/multilang-algo-bench/actions/workflows/lint.yml/badge.svg)](https://github.com/sreekar2858/multilang-algo-bench/actions/workflows/lint.yml)
[![Languages](https://img.shields.io/badge/languages-6-blue)](https://github.com/sreekar2858/multilang-algo-bench)

A comprehensive benchmarking suite that implements and compares the performance of classic algorithms across multiple programming languages. The project features:

- 🔍 Three classic algorithms: Fibonacci, Prime Numbers, and QuickSort
- ⚡ Both serial and parallel implementations for each algorithm
- 📊 Performance benchmarking and comparison across 6 languages
- 📈 Visualization tools for analyzing results
- 🛠️ Configurable thread/processor count for parallel tests
- ✨ Consistent code formatting and linting across all languages

Speed Comparison Tests
=====================

This project implements three algorithmic tests (Fibonacci sequence, prime number calculation, and QuickSort) in both serial and parallel versions across multiple programming languages.

## Project Structure

```
multilang-algo-bench/
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
├── .clang-format     # C/C++ formatting rules
├── .flake8          # Python linting configuration
├── checkstyle.xml   # Java style checking rules
├── pyproject.toml   # Python black formatter config
├── rustfmt.toml     # Rust formatting rules
└── README.md         # This file
```

## Prerequisites:
- C: GCC or compatible C compiler with pthread support
- C++: A modern C++ compiler (C++17 or later)
- Go: Go 1.14 or later
- Python: Python 3.6 or later with pandas
- Rust: Rust 1.31 or later (needs Cargo)
- Java: JDK 8 or later with org.json library

### Dependencies

For Rust, you'll need these dependencies (already in Cargo.toml):
```toml
[dependencies]
rayon = "1.7"
rand = "0.8"
serde_json = "1.0"
num_cpus = "1.0"
```

For Python, install required packages:
```bash
pip install pandas
```

For Java:
- org.json library (provided as json.jar)
- checkstyle for code quality

## Cluster/HPC Environment Notes

When running on a cluster or HPC environment, you may need to load the appropriate modules:

```bash
# For Rust
module load Rust/1.65.0  # or another available version

# For Java 
module load Java/11.0.2  # or Java/13.0.2 or higher

# For Go
module load Go  # load appropriate Go module if available
```

## Compilation Instructions:

C:
```bash
gcc -O3 src/c/c_test.c -o bin/c_test -pthread -lm
```

C++:
```bash
g++ -O3 -std=c++17 src/cpp/cpp_test.cpp -o bin/cpp_test -pthread
```

Go:
```bash
cd src/go
go build -o ../../bin/go_test benchmark.go
```

Rust:
```bash
cd src/rust
cargo build --release
cp target/release/speed_comparison ../../bin/rust_test
```

Java:
```bash
# For Java 11 or higher
javac -cp json.jar src/java/JavaTest.java -d bin

# For Java 8 (if needed for compatibility)
javac -source 1.8 -target 1.8 -cp json.jar src/java/JavaTest.java -d bin
```

Python:
```bash
# Python scripts are run directly from source
```

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
bin/go_test [num_processors]
```

Rust:
```bash
bin/rust_test [num_threads]
```

Java:
```bash
cd bin
java -cp .:../json.jar JavaTest [num_processors]
```

Python:
```bash
python3 src/python/python_test.py [num_processors]
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
python3 process_logs.py
```

This will:
1. Read all benchmark results from the logs directory
2. Generate comparative statistics for all three tests
3. Display thread/processor count used by each implementation

## Troubleshooting

- **Segmentation Faults in C**: The C implementation has improved memory management and thread synchronization to prevent segmentation faults.
- **Path Issues**: All implementations now handle paths properly, ensuring results are written to the correct logs directory regardless of where the executable is run from.
- **Java Compatibility**: For older Java versions (8), compile with `-source 1.8 -target 1.8` flags.
- **Go Path Issues**: If you encounter "module not found" errors in Go, ensure you're using the correct path structure or update the go.mod file.
- **Rust Parallel Functions**: The Rust fibonacci_parallel function has been optimized to handle array bounds properly when working with chunks.

## Implementation Details:
- The parallel versions utilize:
  * C: POSIX threads (pthreads) for multi-threading
  * C++: std::async and futures for task parallelism
  * Go: goroutines and channels for concurrent execution
  * Python: multiprocessing for parallel processing
  * Rust: rayon for parallel iterators and join patterns
  * Java: Fork/Join framework and parallel streams

## Performance Insights:

- Fibonacci calculation is fastest in Rust, C, and C++ for serial execution.
- Prime number calculation shows excellent parallel speedup in Go, C++, and Python.
- QuickSort sees significant speedup in C++, Python, and Java when running in parallel.
- The overhead of parallelization makes the parallel Fibonacci implementation slower than the serial version in most languages due to the small workload.

## Performance Results

Below are the performance ratios relative to Python (Python = 1.0, higher numbers mean faster performance):

### Serial Implementation Performance

| Language | Fibonacci | Prime Numbers | QuickSort |
|----------|-----------|---------------|-----------|
| Rust     | 16.50x    | 8.82x         | 34.47x    |
| C++      | 3.40x     | 10.36x        | 33.02x    |
| C        | 3.70x     | 10.67x        | 37.50x    |
| Go       | 8.24x     | 5.66x         | 7.47x     |
| Java     | 2.52x     | 4.00x         | 20.52x    |
| Python   | 1.00x     | 1.00x         | 1.00x     |

### Parallel Implementation Performance

| Language | Fibonacci | Prime Numbers | QuickSort |
|----------|-----------|---------------|-----------|
| Rust     | 0.10x     | 7.42x         | 21.08x    |
| C++      | 0.05x     | 9.26x         | 38.01x    |
| C        | 0.02x     | 1.77x         | 17.99x    |
| Go       | 0.75x     | 9.74x         | 5.61x     |
| Java     | 0.01x     | 0.16x         | 20.01x    |
| Python   | 1.00x     | 1.00x         | 1.00x     |

Key observations:
- In serial implementations, Rust shows exceptional performance for Fibonacci (16.50x faster than Python)
- C++ and C excel at QuickSort in both serial and parallel implementations (33-38x faster than Python)
- For prime numbers, C++ and C lead in serial performance, while Go and C++ lead in parallel
- Parallel Fibonacci shows lower performance ratios due to overhead outweighing benefits for small workloads
- Java maintains consistent QuickSort performance in both serial and parallel implementations

Note: Higher numbers indicate better performance relative to Python. Numbers less than 1.0 indicate slower performance than the Python baseline.