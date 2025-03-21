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
Speed_Comparison/
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
- Go: Go 1.24.1 or later
- Python: Python 3.6 or later with pandas and matplotlib
- Rust: Rust 1.31 or later (needs Cargo)
- Java: JDK 11 or later with org.json library

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
pip install pandas matplotlib flake8 black
```

For Java:
- org.json library (provided as json.jar)
- checkstyle for code quality

## Development Setup

### Code Quality Tools

The project uses several linting and formatting tools:
- C/C++: clang-format with Google style
- Python: black formatter and flake8 linter
- Go: gofmt and go vet
- Java: checkstyle
- Rust: rustfmt and clippy

All formatting configurations are provided in the respective config files (.clang-format, pyproject.toml, etc.).

## Quick Start

Clone the repository:
```bash
git clone https://github.com/yourusername/multilang-algo-bench.git
cd multilang-algo-bench
```

## Compilation Instructions:

C:
```bash
gcc -O3 src/c/c_test.c -o c_test -pthread -lm
./c_test [num_threads]
```

C++:
```bash
g++ -O3 -std=c++17 src/cpp/cpp_test.cpp -o cpp_test -pthread
./cpp_test [num_threads]
```

Go:
```bash
cd src/go
go build -o go_test benchmark_test.go
./go_test [num_processors]
```

Rust:
```bash
cd src/rust
cargo build --release
cargo run --release -- [num_threads]
```

Java:
```bash
javac -cp json.jar src/java/JavaTest.java
java -cp json.jar:. JavaTest [num_processors]
```

Python:
```bash
python src/python/python_test.py [num_processors]
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
- Code Quality:
  * Consistent formatting across all languages
  * Automated linting in CI pipeline
  * Language-specific best practices enforcement
  * Clear and maintainable code structure
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