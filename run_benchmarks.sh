#!/bin/bash
# run_benchmarks.sh - Build and run all benchmarks across languages
# --------------------------------------------------------------

# Create directories if they don't exist
mkdir -p bin
mkdir -p logs

# Set the number of threads to use (defaults to all available)
# Can be overridden with ./run_benchmarks.sh <number_of_threads>
# or ./run_benchmarks.sh <benchmark_name> <number_of_threads>
if [[ "$1" =~ ^[0-9]+$ ]]; then
    THREADS=$1
    BENCHMARK=""
elif [[ -n "$1" && "$2" =~ ^[0-9]+$ ]]; then
    BENCHMARK=$1
    THREADS=$2
elif [[ -n "$1" && ! "$1" =~ ^[0-9]+$ ]]; then
    BENCHMARK=$1
    THREADS=$(nproc)
else
    THREADS=$(nproc)
    BENCHMARK=""
fi

echo "Using $THREADS threads for benchmarks"
[[ -n "$BENCHMARK" ]] && echo "Running only $BENCHMARK benchmark"

# Set the number of MPI processes (default to the same as threads)
MPI_PROCESSES=$THREADS

# Colors for prettier output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}=======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=======================================${NC}\n"
}

# Function to print status messages
status() {
    echo -e "${GREEN}[✓] $1${NC}"
}

# Function to print warnings
warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Function to print errors
error() {
    echo -e "${RED}[✗] $1${NC}"
}

# Check if required commands are available
check_command() {
    if ! command -v $1 &> /dev/null; then
        warning "$1 not found. $2 will be skipped."
        return 1
    fi
    return 0
}

# Run a command with error handling
run_with_error_handling() {
    "$@"
    local status=$?
    if [ $status -ne 0 ]; then
        error "Command failed with exit code $status: $*"
        return $status
    fi
    return 0
}

# First check if all required tools are available
print_header "Checking build requirements"

C_AVAILABLE=true
if ! check_command gcc "C benchmark"; then
    C_AVAILABLE=false
fi

CPP_AVAILABLE=true
if ! check_command g++ "C++ benchmark"; then
    CPP_AVAILABLE=false
fi

GO_AVAILABLE=true
if ! check_command go "Go benchmark"; then
    GO_AVAILABLE=false
fi

RUST_AVAILABLE=true
if ! check_command cargo "Rust benchmark"; then
    RUST_AVAILABLE=false
fi

JAVA_AVAILABLE=true
if ! check_command javac "Java benchmark"; then
    JAVA_AVAILABLE=false
elif ! check_command java "Java benchmark"; then
    JAVA_AVAILABLE=false
fi

PYTHON_AVAILABLE=true
if ! check_command python3 "Python benchmark"; then
    PYTHON_AVAILABLE=false
else
    # Check for required Python packages
    if ! python3 -c "import pandas" &> /dev/null; then
        warning "Python pandas package not found. You may need to install it for result processing."
    fi
fi

MPI_AVAILABLE=true
if ! check_command mpicc "MPI C benchmark"; then
    MPI_AVAILABLE=false
elif ! check_command mpicxx "MPI C++ benchmark"; then
    MPI_AVAILABLE=false
elif ! check_command mpirun "MPI benchmark execution"; then
    MPI_AVAILABLE=false
fi

# Function to load modules for HPC environments if needed
load_modules() {
    # Uncomment and modify these lines if running on an HPC/cluster environment
    # module purge  # Clear any existing modules
    if command -v module &> /dev/null; then
        echo "Cluster environment detected. Loading modules..."
        module load GCC  # For C/C++
        module load Go  # For Go
        module load Rust  # For Rust
        module load Java  # For Java
        module load OpenMPI  # For MPI benchmarks
    fi
}

# Attempt to load modules if in a cluster environment
load_modules

# Build C benchmark
build_c() {
    print_header "Building C benchmark"
    if [ "$C_AVAILABLE" = true ]; then
        if run_with_error_handling gcc -O3 src/c/c_test.c -o bin/c_test -pthread -lm; then
            status "C benchmark built successfully"
            return 0
        else
            error "C benchmark build failed"
            return 1
        fi
    else
        error "Skipping C benchmark build"
        return 1
    fi
}

# Build C++ benchmark
build_cpp() {
    print_header "Building C++ benchmark"
    if [ "$CPP_AVAILABLE" = true ]; then
        if run_with_error_handling g++ -O3 -std=c++17 src/cpp/cpp_test.cpp -o bin/cpp_test -pthread; then
            status "C++ benchmark built successfully"
            return 0
        else
            error "C++ benchmark build failed"
            return 1
        fi
    else
        error "Skipping C++ benchmark build"
        return 1
    fi
}

# Build C MPI benchmark
build_c_mpi() {
    print_header "Building C MPI benchmark"
    if [ "$C_AVAILABLE" = true ] && [ "$MPI_AVAILABLE" = true ]; then
        if run_with_error_handling mpicc -O3 src/c/c_test_mpi.c -o bin/c_test_mpi -lm; then
            status "C MPI benchmark built successfully"
            return 0
        else
            error "C MPI benchmark build failed"
            return 1
        fi
    else
        error "Skipping C MPI benchmark build"
        return 1
    fi
}

# Build C++ MPI benchmark
build_cpp_mpi() {
    print_header "Building C++ MPI benchmark"
    if [ "$CPP_AVAILABLE" = true ] && [ "$MPI_AVAILABLE" = true ]; then
        if run_with_error_handling mpicxx -O3 -std=c++17 src/cpp/cpp_test_mpi.cpp -o bin/cpp_test_mpi; then
            status "C++ MPI benchmark built successfully"
            return 0
        else
            error "C++ MPI benchmark build failed"
            return 1
        fi
    else
        error "Skipping C++ MPI benchmark build"
        return 1
    fi
}

# Build Go benchmark
build_go() {
    print_header "Building Go benchmark"
    if [ "$GO_AVAILABLE" = true ]; then
        cd src/go
        if run_with_error_handling go build -o ../../bin/go_test benchmark.go; then
            cd ../..
            status "Go benchmark built successfully"
            return 0
        else
            cd ../..
            error "Go benchmark build failed"
            return 1
        fi
    else
        error "Skipping Go benchmark build"
        return 1
    fi
}

# Build Rust benchmark
build_rust() {
    print_header "Building Rust benchmark"
    if [ "$RUST_AVAILABLE" = true ]; then
        cd src/rust
        if run_with_error_handling cargo build --release; then
            cp target/release/speed_comparison ../../bin/rust_test
            cd ../..
            status "Rust benchmark built successfully"
            return 0
        else
            cd ../..
            error "Rust benchmark build failed"
            return 1
        fi
    else
        error "Skipping Rust benchmark build"
        return 1
    fi
}

# Build Java benchmark
build_java() {
    print_header "Building Java benchmark"
    if [ "$JAVA_AVAILABLE" = true ]; then
        # Check Java version to use appropriate compile flags
        JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | sed 's/^1\.//' | cut -d'.' -f1)
        
        if [ "$JAVA_VERSION" -lt 11 ]; then
            warning "Using Java 8 compatibility mode"
            if run_with_error_handling javac -source 1.8 -target 1.8 -cp json.jar src/java/JavaTest.java -d bin; then
                status "Java benchmark built successfully"
                return 0
            else
                error "Java benchmark build failed"
                return 1
            fi
        else
            if run_with_error_handling javac -cp json.jar src/java/JavaTest.java -d bin; then
                status "Java benchmark built successfully"
                return 0
            else
                error "Java benchmark build failed"
                return 1
            fi
        fi
    else
        error "Skipping Java benchmark build"
        return 1
    fi
}

# Run C benchmark
run_c() {
    print_header "Running C benchmark"
    if [ -f bin/c_test ]; then
        if run_with_error_handling bin/c_test $THREADS; then
            status "C benchmark completed"
            return 0
        else
            error "C benchmark failed during execution"
            return 1
        fi
    else
        error "C executable not found. Build may have failed."
        return 1
    fi
}

# Run C++ benchmark
run_cpp() {
    print_header "Running C++ benchmark"
    if [ -f bin/cpp_test ]; then
        if run_with_error_handling bin/cpp_test $THREADS; then
            status "C++ benchmark completed"
            return 0
        else
            error "C++ benchmark failed during execution"
            return 1
        fi
    else
        error "C++ executable not found. Build may have failed."
        return 1
    fi
}

# Run C MPI benchmark
run_c_mpi() {
    print_header "Running C MPI benchmark"
    if [ -f bin/c_test_mpi ]; then
        if run_with_error_handling mpirun -np $MPI_PROCESSES bin/c_test_mpi; then
            status "C MPI benchmark completed"
            return 0
        else
            error "C MPI benchmark failed during execution"
            return 1
        fi
    else
        error "C MPI executable not found. Build may have failed."
        return 1
    fi
}

# Run C++ MPI benchmark
run_cpp_mpi() {
    print_header "Running C++ MPI benchmark"
    if [ -f bin/cpp_test_mpi ]; then
        if run_with_error_handling mpirun -np $MPI_PROCESSES bin/cpp_test_mpi; then
            status "C++ MPI benchmark completed"
            return 0
        else
            error "C++ MPI benchmark failed during execution"
            return 1
        fi
    else
        error "C++ MPI executable not found. Build may have failed."
        return 1
    fi
}

# Run Go benchmark
run_go() {
    print_header "Running Go benchmark"
    if [ -f bin/go_test ]; then
        if run_with_error_handling bin/go_test $THREADS; then
            status "Go benchmark completed"
            return 0
        else
            error "Go benchmark failed during execution"
            return 1
        fi
    else
        error "Go executable not found. Build may have failed."
        return 1
    fi
}

# Run Rust benchmark
run_rust() {
    print_header "Running Rust benchmark"
    if [ -f bin/rust_test ]; then
        if run_with_error_handling bin/rust_test $THREADS; then
            status "Rust benchmark completed"
            return 0
        else
            error "Rust benchmark failed during execution"
            return 1
        fi
    else
        error "Rust executable not found. Build may have failed."
        return 1
    fi
}

# Run Java benchmark
run_java() {
    print_header "Running Java benchmark"
    if [ -f bin/JavaTest.class ]; then
        cd bin
        if run_with_error_handling java -cp .:../json.jar JavaTest $THREADS; then
            cd ..
            status "Java benchmark completed"
            return 0
        else
            cd ..
            error "Java benchmark failed during execution"
            return 1
        fi
    else
        error "Java class file not found. Build may have failed."
        return 1
    fi
}

# Run Python benchmark
run_python() {
    print_header "Running Python benchmark"
    if [ "$PYTHON_AVAILABLE" = true ]; then
        if run_with_error_handling /home/jp267451/miniconda3/bin/python3.12 src/python/python_test.py $THREADS; then
            status "Python benchmark completed"
            return 0
        else
            error "Python benchmark failed during execution"
            return 1
        fi
    else
        error "Python not available. Skipping Python benchmark."
        return 1
    fi
}

# Process results
process_results() {
    print_header "Processing benchmark results"
    if [ "$PYTHON_AVAILABLE" = true ]; then
        if run_with_error_handling /home/jp267451/miniconda3/bin/python3.12 process_logs.py; then
            status "Results processed successfully"
            echo -e "\nResults summary available in CSV files and have been printed above."
            return 0
        else
            error "Results processing failed"
            return 1
        fi
    else
        error "Python not available. Cannot process results."
        return 1
    fi
}

# Print usage information
print_usage() {
    echo "Usage: $0 [benchmark] [threads]"
    echo ""
    echo "Run the entire benchmark suite or a specific benchmark with the specified number of threads."
    echo ""
    echo "Arguments:"
    echo "  benchmark   Optional: Specific benchmark to run (c, cpp, c_mpi, cpp_mpi, go, rust, java, python)"
    echo "  threads     Optional: Number of threads to use (default: all available)"
    echo ""
    echo "Examples:"
    echo "  $0                     # Run all benchmarks with all available threads"
    echo "  $0 8                   # Run all benchmarks with 8 threads"
    echo "  $0 python              # Run only the Python benchmark with all available threads"
    echo "  $0 python 4            # Run only the Python benchmark with 4 threads"
    echo "  $0 c_mpi 4             # Run only the C MPI benchmark with 4 processes"
}

# Function to run a specific benchmark
run_benchmark() {
    local benchmark=$1
    local success=false
    
    case $benchmark in
        c)
            if build_c; then
                run_c && success=true
            fi
            ;;
        cpp)
            if build_cpp; then
                run_cpp && success=true
            fi
            ;;
        c_mpi)
            if build_c_mpi; then
                run_c_mpi && success=true
            fi
            ;;
        cpp_mpi)
            if build_cpp_mpi; then
                run_cpp_mpi && success=true
            fi
            ;;
        go)
            if build_go; then
                run_go && success=true
            fi
            ;;
        rust)
            if build_rust; then
                run_rust && success=true
            fi
            ;;
        java)
            if build_java; then
                run_java && success=true
            fi
            ;;
        python)
            run_python && success=true
            ;;
        all)
            run_all_benchmarks
            return $?
            ;;
        *)
            print_usage
            return 1
            ;;
    esac
    
    if [ "$success" = true ]; then
        status "$benchmark benchmark completed successfully"
        return 0
    else
        error "$benchmark benchmark failed"
        return 1
    fi
}

# Function to run all benchmarks
run_all_benchmarks() {
    local failed_benchmarks=()
    local success_count=0
    local total_count=0
    
    print_header "Building and running all benchmarks"
    
    # Build and run C
    if build_c; then
        if run_c; then
            ((success_count++))
        else
            failed_benchmarks+=("C (runtime)")
        fi
    else
        failed_benchmarks+=("C (build)")
    fi
    ((total_count++))
    
    # Build and run C++
    if build_cpp; then
        if run_cpp; then
            ((success_count++))
        else
            failed_benchmarks+=("C++ (runtime)")
        fi
    else
        failed_benchmarks+=("C++ (build)")
    fi
    ((total_count++))
    
    # Build and run C MPI if available
    if [ "$MPI_AVAILABLE" = true ]; then
        if build_c_mpi; then
            if run_c_mpi; then
                ((success_count++))
            else
                failed_benchmarks+=("C MPI (runtime)")
            fi
        else
            failed_benchmarks+=("C MPI (build)")
        fi
        ((total_count++))
        
        # Build and run C++ MPI
        if build_cpp_mpi; then
            if run_cpp_mpi; then
                ((success_count++))
            else
                failed_benchmarks+=("C++ MPI (runtime)")
            fi
        else
            failed_benchmarks+=("C++ MPI (build)")
        fi
        ((total_count++))
    else
        warning "MPI not available. Skipping MPI benchmarks."
    fi
    
    # Build and run Go
    if build_go; then
        if run_go; then
            ((success_count++))
        else
            failed_benchmarks+=("Go (runtime)")
        fi
    else
        failed_benchmarks+=("Go (build)")
    fi
    ((total_count++))
    
    # Build and run Rust
    if build_rust; then
        if run_rust; then
            ((success_count++))
        else
            failed_benchmarks+=("Rust (runtime)")
        fi
    else
        failed_benchmarks+=("Rust (build)")
    fi
    ((total_count++))
    
    # Build and run Java
    if build_java; then
        if run_java; then
            ((success_count++))
        else
            failed_benchmarks+=("Java (runtime)")
        fi
    else
        failed_benchmarks+=("Java (build)")
    fi
    ((total_count++))
    
    # Run Python
    if run_python; then
        ((success_count++))
    else
        failed_benchmarks+=("Python")
    fi
    ((total_count++))
    
    # Process results
    process_results
    
    print_header "Benchmark suite summary"
    echo "Completed: $success_count/$total_count benchmarks"
    
    if [ ${#failed_benchmarks[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}Failed benchmarks:${NC}"
        for failed in "${failed_benchmarks[@]}"; do
            echo "  - $failed"
        done
        echo ""
        echo "Check the error messages above for details."
        return 1
    else
        echo -e "\n${GREEN}All benchmarks completed successfully!${NC}"
        return 0
    fi
}

# Main script logic
if [[ "$1" == "help" || "$1" == "--help" || "$1" == "-h" ]]; then
    print_usage
    exit 0
fi

if [[ -n "$BENCHMARK" ]]; then
    # Run a specific benchmark
    run_benchmark "$BENCHMARK"
    exit_code=$?
else
    # Run all benchmarks
    run_all_benchmarks
    exit_code=$?
fi

if [ $exit_code -eq 0 ]; then
    print_header "Benchmark suite completed successfully"
    echo "Check the logs/ directory for detailed JSON results."
    echo "Check the CSV files for summarized data."
else
    print_header "Benchmark suite completed with errors"
    echo "Some benchmarks failed. See the error messages above."
    echo "Partial results may be available in the logs/ directory."
fi

exit $exit_code 