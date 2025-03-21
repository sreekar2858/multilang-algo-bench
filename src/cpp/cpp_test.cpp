#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <thread>
#include <algorithm>
#include <future>
#include <fstream>
#include <filesystem>

// Global variable for process count
unsigned int g_num_threads = std::thread::hardware_concurrency();

void set_thread_count(unsigned int count) {
    g_num_threads = count > 0 ? std::min(count, std::thread::hardware_concurrency()) : std::thread::hardware_concurrency();
}

// Fibonacci implementations
unsigned long long fibonacci_serial(int n) {
    if (n <= 1) return n;
    return fibonacci_serial(n - 1) + fibonacci_serial(n - 2);
}

unsigned long long fibonacci_dynamic(int n) {
    if (n <= 1) return n;
    std::vector<unsigned long long> fib(n + 1);
    fib[1] = 1;
    for (int i = 2; i <= n; i++) {
        fib[i] = fib[i-1] + fib[i-2];
    }
    return fib[n];
}

std::vector<unsigned long long> fibonacci_chunk(int start, int end) {
    std::vector<unsigned long long> fib(end + 1);
    if (start <= 1 && end >= 1) fib[1] = 1;
    for (int i = std::max(2, start); i <= end; i++) {
        fib[i] = fib[i-1] + fib[i-2];
    }
    return std::vector<unsigned long long>(fib.begin() + start, fib.begin() + end + 1);
}

std::vector<unsigned long long> fibonacci_parallel(int n) {
    int chunk_size = std::max(1, static_cast<int>(n / g_num_threads));
    std::vector<std::future<std::vector<unsigned long long>>> futures;
    
    for (int i = 0; i < n; i += chunk_size) {
        int end = std::min(i + chunk_size, n);
        futures.push_back(std::async(std::launch::async, fibonacci_chunk, i, end));
    }
    
    std::vector<unsigned long long> result;
    for (auto& future : futures) {
        auto chunk = future.get();
        result.insert(result.end(), chunk.begin(), chunk.end());
    }
    return result;
}

bool is_prime(int n) {
    if (n < 2) return false;
    for (int i = 2; i <= sqrt(n); i++) {
        if (n % i == 0) return false;
    }
    return true;
}

std::vector<int> find_primes_serial(int limit) {
    std::vector<int> primes;
    for (int n = 2; n <= limit; n++) {
        if (is_prime(n)) {
            primes.push_back(n);
        }
    }
    return primes;
}

std::vector<int> find_primes_parallel(int limit) {
    unsigned int num_threads = std::thread::hardware_concurrency();
    std::vector<std::future<std::vector<int>>> futures;
    std::vector<int> result;
    
    int chunk_size = limit / num_threads;
    
    for (unsigned int i = 0; i < num_threads; i++) {
        int start = i * chunk_size + 2;
        int end = (i == num_threads - 1) ? limit : (i + 1) * chunk_size + 1;
        
        futures.push_back(std::async(std::launch::async, [start, end]() {
            std::vector<int> local_primes;
            for (int n = start; n <= end; n++) {
                if (is_prime(n)) {
                    local_primes.push_back(n);
                }
            }
            return local_primes;
        }));
    }
    
    for (auto& future : futures) {
        auto partial_result = future.get();
        result.insert(result.end(), partial_result.begin(), partial_result.end());
    }
    
    std::sort(result.begin(), result.end());
    return result;
}

void quicksort_serial(std::vector<int>& arr, int low, int high) {
    if (low < high) {
        int pivot = arr[high];
        int i = low - 1;
        
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                std::swap(arr[i], arr[j]);
            }
        }
        std::swap(arr[i + 1], arr[high]);
        
        int pi = i + 1;
        quicksort_serial(arr, low, pi - 1);
        quicksort_serial(arr, pi + 1, high);
    }
}

void quicksort_parallel(std::vector<int>& arr, int low, int high, int depth = 0) {
    if (low < high) {
        if (depth >= 3) { // Limit parallel recursion depth
            quicksort_serial(arr, low, high);
            return;
        }
        
        int pivot = arr[high];
        int i = low - 1;
        
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                std::swap(arr[i], arr[j]);
            }
        }
        std::swap(arr[i + 1], arr[high]);
        
        int pi = i + 1;
        
        std::future<void> left_sort = std::async(std::launch::async,
            [&arr, low, pi, depth]() {
                quicksort_parallel(arr, low, pi - 1, depth + 1);
            });
            
        quicksort_parallel(arr, pi + 1, high, depth + 1);
        left_sort.wait();
    }
}

int main(int argc, char* argv[]) {
    // Set thread count from command line argument if provided
    if (argc > 1) {
        set_thread_count(std::stoi(argv[1]));
    }
    std::cout << "Running with " << g_num_threads << " threads" << std::endl;
    
    const int PRIME_LIMIT = 100000;
    const int SORT_SIZE = 1000000;
    const int FIB_N = 100000;
    
    // Create logs directory if it doesn't exist
    std::filesystem::create_directory("logs");
    
    double serial_time_fib, parallel_time_fib;
    double serial_time_primes, parallel_time_primes;
    double serial_time_sort, parallel_time_sort;
    
    // Fibonacci test
    std::cout << "\nC++ Fibonacci Test" << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    auto fib_serial = fibonacci_dynamic(FIB_N);
    auto end = std::chrono::high_resolution_clock::now();
    serial_time_fib = std::chrono::duration<double>(end - start).count();
    std::cout << "Serial Time (Dynamic): " << serial_time_fib << " seconds" << std::endl;
    
    start = std::chrono::high_resolution_clock::now();
    auto fib_parallel = fibonacci_parallel(FIB_N);
    end = std::chrono::high_resolution_clock::now();
    parallel_time_fib = std::chrono::duration<double>(end - start).count();
    std::cout << "Parallel Time: " << parallel_time_fib << " seconds" << std::endl;
    
    // Prime numbers test
    std::cout << "\nC++ Prime Numbers Test" << std::endl;
    
    start = std::chrono::high_resolution_clock::now();
    auto primes_serial = find_primes_serial(PRIME_LIMIT);
    end = std::chrono::high_resolution_clock::now();
    serial_time_primes = std::chrono::duration<double>(end - start).count();
    std::cout << "Serial Time: " << serial_time_primes << " seconds" << std::endl;
    
    start = std::chrono::high_resolution_clock::now();
    auto primes_parallel = find_primes_parallel(PRIME_LIMIT);
    end = std::chrono::high_resolution_clock::now();
    parallel_time_primes = std::chrono::duration<double>(end - start).count();
    std::cout << "Parallel Time: " << parallel_time_primes << " seconds" << std::endl;
    
    // QuickSort test
    std::cout << "\nC++ QuickSort Test" << std::endl;
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 1000000);
    
    std::vector<int> test_array(SORT_SIZE);
    for (int i = 0; i < SORT_SIZE; i++) {
        test_array[i] = dis(gen);
    }
    auto array_copy = test_array;
    
    start = std::chrono::high_resolution_clock::now();
    quicksort_serial(test_array, 0, test_array.size() - 1);
    end = std::chrono::high_resolution_clock::now();
    serial_time_sort = std::chrono::duration<double>(end - start).count();
    std::cout << "Serial Time: " << serial_time_sort << " seconds" << std::endl;
    
    start = std::chrono::high_resolution_clock::now();
    quicksort_parallel(array_copy, 0, array_copy.size() - 1);
    end = std::chrono::high_resolution_clock::now();
    parallel_time_sort = std::chrono::duration<double>(end - start).count();
    std::cout << "Parallel Time: " << parallel_time_sort << " seconds" << std::endl;
    
    // Write results to JSON file
    std::ofstream log_file("logs/cpp_results.json");
    log_file << "{\n";
    log_file << "  \"language\": \"C++\",\n";
    log_file << "  \"thread_count\": " << g_num_threads << ",\n";
    log_file << "  \"fibonacci_serial\": " << serial_time_fib << ",\n";
    log_file << "  \"fibonacci_parallel\": " << parallel_time_fib << ",\n";
    log_file << "  \"primes_serial\": " << serial_time_primes << ",\n";
    log_file << "  \"primes_parallel\": " << parallel_time_primes << ",\n";
    log_file << "  \"sort_serial\": " << serial_time_sort << ",\n";
    log_file << "  \"sort_parallel\": " << parallel_time_sort << "\n";
    log_file << "}\n";
    log_file.close();
    
    return 0;
}