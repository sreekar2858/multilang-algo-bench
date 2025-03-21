#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <algorithm>
#include <fstream>
#include <filesystem>
#include <mpi.h>
#include <cmath>

// Global variables for MPI
int g_world_size = 1;
int g_rank = 0;

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
    std::vector<unsigned long long> result(n);
    
    // For small n, let rank 0 do all the work
    if (n < 10) {
        if (g_rank == 0) {
            result.resize(n);
            if (n > 0) result[0] = 0;
            if (n > 1) result[1] = 1;
            
            for (int i = 2; i < n; i++) {
                result[i] = result[i-1] + result[i-2];
            }
        }
        return result;
    }
    
    // Distribute the work among processes
    int chunk_size = (n + g_world_size - 1) / g_world_size;
    int start = g_rank * chunk_size;
    int end = std::min((g_rank + 1) * chunk_size - 1, n - 1);
    
    // Special case for rank 0 to include the initial values
    if (g_rank == 0 && start < 2) {
        // First two values are special cases
        if (n > 0) result[0] = 0;
        if (n > 1) result[1] = 1;
        start = 2;
    }
    
    // If start > end, this rank doesn't need to calculate anything
    int local_size = (start <= end) ? (end - start + 1) : 0;
    std::vector<unsigned long long> local_result;
    
    if (local_size > 0) {
        // If rank > 0, we need to receive the previous two values
        if (g_rank > 0) {
            std::vector<unsigned long long> prev_values(2);
            MPI_Recv(prev_values.data(), 2, MPI_UNSIGNED_LONG_LONG, g_rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            
            // Calculate local chunk with received values
            std::vector<unsigned long long> fib(end + 1);
            fib[start - 2] = prev_values[0];
            fib[start - 1] = prev_values[1];
            
            for (int i = start; i <= end; i++) {
                fib[i] = fib[i-1] + fib[i-2];
            }
            
            local_result.resize(local_size);
            std::copy(fib.begin() + start, fib.begin() + end + 1, local_result.begin());
            
            // Send last two values to next rank if needed
            if (g_rank < g_world_size - 1) {
                std::vector<unsigned long long> next_values = {fib[end - 1], fib[end]};
                MPI_Send(next_values.data(), 2, MPI_UNSIGNED_LONG_LONG, g_rank + 1, 0, MPI_COMM_WORLD);
            }
        } else {
            // Rank 0
            local_result.resize(local_size);
            for (int i = start; i <= end; i++) {
                result[i] = result[i-1] + result[i-2];
                local_result[i - start] = result[i];
            }
            
            // Send last two values to next rank if needed
            if (g_world_size > 1) {
                std::vector<unsigned long long> next_values = {result[end - 1], result[end]};
                MPI_Send(next_values.data(), 2, MPI_UNSIGNED_LONG_LONG, 1, 0, MPI_COMM_WORLD);
            }
        }
    }
    
    // Gather results from all processes
    if (g_rank == 0) {
        // Rank 0 already has its portion, receive others
        for (int i = 1; i < g_world_size; i++) {
            int remote_start = i * chunk_size;
            // Skip ranks that don't have work to do
            if (remote_start >= n) continue;
            
            int remote_end = std::min((i + 1) * chunk_size - 1, n - 1);
            int remote_size = remote_end - remote_start + 1;
            
            std::vector<unsigned long long> remote_result(remote_size);
            MPI_Recv(remote_result.data(), remote_size, MPI_UNSIGNED_LONG_LONG, 
                   i, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            
            // Copy received chunk to result
            std::copy(remote_result.begin(), remote_result.end(), result.begin() + remote_start);
        }
    } else if (local_size > 0) {
        // Send local results to rank 0
        MPI_Send(local_result.data(), local_size, MPI_UNSIGNED_LONG_LONG, 0, 1, MPI_COMM_WORLD);
    }
    
    // Make sure all processes have the same result
    MPI_Bcast(result.data(), n, MPI_UNSIGNED_LONG_LONG, 0, MPI_COMM_WORLD);
    
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

std::vector<int> find_primes_range(int start, int end) {
    std::vector<int> local_primes;
    for (int n = start; n <= end; n++) {
        if (is_prime(n)) {
            local_primes.push_back(n);
        }
    }
    return local_primes;
}

std::vector<int> find_primes_parallel(int limit) {
    // Distribute work among processes
    int chunk_size = (limit - 1) / g_world_size;
    int start = g_rank * chunk_size + 2;
    int end = (g_rank + 1) * chunk_size + 1;
    if (g_rank == g_world_size - 1) end = limit;
    
    std::vector<int> local_primes = find_primes_range(start, end);
    int local_count = local_primes.size();
    
    // Gather all counts to determine total size and displacements
    std::vector<int> counts(g_world_size);
    MPI_Allgather(&local_count, 1, MPI_INT, counts.data(), 1, MPI_INT, MPI_COMM_WORLD);
    
    // Calculate displacements
    std::vector<int> displs(g_world_size);
    int total_count = 0;
    for (int i = 0; i < g_world_size; i++) {
        displs[i] = total_count;
        total_count += counts[i];
    }
    
    // Allocate space for all primes
    std::vector<int> all_primes(total_count);
    
    // Gather all primes with variable counts
    MPI_Allgatherv(local_primes.data(), local_count, MPI_INT, 
                  all_primes.data(), counts.data(), displs.data(), 
                  MPI_INT, MPI_COMM_WORLD);
    
    // Sort the result (already sorted by process rank, but need to merge)
    std::sort(all_primes.begin(), all_primes.end());
    
    return all_primes;
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

void quicksort_parallel(std::vector<int>& arr) {
    if (arr.size() <= 1) {
        return;
    }
    
    // Distribute the array across processes
    int size = arr.size();
    int local_size = size / g_world_size;
    int remainder = size % g_world_size;
    
    // Calculate local sizes and displacements considering remainder
    std::vector<int> sendcounts(g_world_size);
    std::vector<int> displs(g_world_size);
    
    for (int i = 0; i < g_world_size; i++) {
        sendcounts[i] = local_size;
        if (i < remainder) {
            sendcounts[i]++;
        }
        displs[i] = (i > 0) ? displs[i-1] + sendcounts[i-1] : 0;
    }
    
    // Allocate space for local array
    std::vector<int> local_arr(sendcounts[g_rank]);
    
    // Scatter the array from root to all processes
    MPI_Scatterv(arr.data(), sendcounts.data(), displs.data(), MPI_INT,
                local_arr.data(), sendcounts[g_rank], MPI_INT,
                0, MPI_COMM_WORLD);
    
    // Sort local portion
    quicksort_serial(local_arr, 0, local_arr.size() - 1);
    
    // Gather the sorted local arrays back to root
    MPI_Gatherv(local_arr.data(), sendcounts[g_rank], MPI_INT, 
               arr.data(), sendcounts.data(), displs.data(), MPI_INT,
               0, MPI_COMM_WORLD);
    
    // Root process performs the final merge
    if (g_rank == 0) {
        // Merge step using a temporary array
        std::vector<int> temp(size);
        for (int i = 0; i < g_world_size - 1; i++) {
            int left_start = displs[i];
            int mid = displs[i+1] - 1;
            int right_end = (i + 2 < g_world_size) ? displs[i+2] - 1 : size - 1;
            
            // Create temporary arrays for the two halves
            std::vector<int> left(arr.begin() + left_start, arr.begin() + mid + 1);
            std::vector<int> right(arr.begin() + mid + 1, arr.begin() + right_end + 1);
            
            // Merge the two sorted arrays
            std::merge(left.begin(), left.end(), right.begin(), right.end(), 
                      arr.begin() + left_start);
        }
    }
}

int main(int argc, char* argv[]) {
    // Initialize MPI
    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &g_world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &g_rank);
    
    if (g_rank == 0) {
        std::cout << "Running with " << g_world_size << " MPI processes" << std::endl;
    }
    
    const int PRIME_LIMIT = 100000;
    const int SORT_SIZE = 1000000;
    const int FIB_N = 100000;
    
    if (g_rank == 0) {
        // Create logs directory if it doesn't exist
        std::filesystem::create_directory("logs");
    }
    
    // Ensure all processes start at the same time
    MPI_Barrier(MPI_COMM_WORLD);
    
    double serial_time_fib = 0, parallel_time_fib = 0;
    double serial_time_primes = 0, parallel_time_primes = 0;
    double serial_time_sort = 0, parallel_time_sort = 0;
    
    // Fibonacci test
    if (g_rank == 0) {
        std::cout << "\nC++ MPI Fibonacci Test" << std::endl;
        
        // Serial implementation (only rank 0)
        auto start = std::chrono::high_resolution_clock::now();
        auto fib_serial = fibonacci_dynamic(FIB_N);
        auto end = std::chrono::high_resolution_clock::now();
        serial_time_fib = std::chrono::duration<double>(end - start).count();
        std::cout << "Serial Time (Dynamic): " << serial_time_fib << " seconds" << std::endl;
    }
    
    // Parallel implementation (all ranks)
    MPI_Barrier(MPI_COMM_WORLD);
    double start_time = MPI_Wtime();
    
    auto fib_parallel = fibonacci_parallel(FIB_N);
    
    double end_time = MPI_Wtime();
    if (g_rank == 0) {
        parallel_time_fib = end_time - start_time;
        std::cout << "Parallel Time: " << parallel_time_fib << " seconds" << std::endl;
    }
    
    // Prime numbers test
    if (g_rank == 0) {
        std::cout << "\nC++ MPI Prime Numbers Test" << std::endl;
        
        // Serial implementation (only rank 0)
        auto start = std::chrono::high_resolution_clock::now();
        auto primes_serial = find_primes_serial(PRIME_LIMIT);
        auto end = std::chrono::high_resolution_clock::now();
        serial_time_primes = std::chrono::duration<double>(end - start).count();
        std::cout << "Serial Time: " << serial_time_primes << " seconds" << std::endl;
    }
    
    // Parallel implementation (all ranks)
    MPI_Barrier(MPI_COMM_WORLD);
    start_time = MPI_Wtime();
    
    auto primes_parallel = find_primes_parallel(PRIME_LIMIT);
    
    end_time = MPI_Wtime();
    if (g_rank == 0) {
        parallel_time_primes = end_time - start_time;
        std::cout << "Parallel Time: " << parallel_time_primes << " seconds" << std::endl;
    }
    
    // QuickSort test
    if (g_rank == 0) {
        std::cout << "\nC++ MPI QuickSort Test" << std::endl;
        
        // Create test array
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(1, 1000000);
        
        std::vector<int> test_array(SORT_SIZE);
        for (int i = 0; i < SORT_SIZE; i++) {
            test_array[i] = dis(gen);
        }
        auto array_copy = test_array;
        
        // Serial implementation (only rank 0)
        auto start = std::chrono::high_resolution_clock::now();
        quicksort_serial(test_array, 0, test_array.size() - 1);
        auto end = std::chrono::high_resolution_clock::now();
        serial_time_sort = std::chrono::duration<double>(end - start).count();
        std::cout << "Serial Time: " << serial_time_sort << " seconds" << std::endl;
        
        // Broadcast the unsorted array to all processes
        MPI_Bcast(array_copy.data(), SORT_SIZE, MPI_INT, 0, MPI_COMM_WORLD);
        
        // Parallel sorting
        start_time = MPI_Wtime();
        quicksort_parallel(array_copy);
        end_time = MPI_Wtime();
        parallel_time_sort = end_time - start_time;
        std::cout << "Parallel Time: " << parallel_time_sort << " seconds" << std::endl;
        
        // Write results to JSON file
        std::ofstream log_file("logs/cpp_mpi_results.json");
        log_file << "{\n";
        log_file << "  \"language\": \"C++ MPI\",\n";
        log_file << "  \"process_count\": " << g_world_size << ",\n";
        log_file << "  \"fibonacci_serial\": " << serial_time_fib << ",\n";
        log_file << "  \"fibonacci_parallel\": " << parallel_time_fib << ",\n";
        log_file << "  \"primes_serial\": " << serial_time_primes << ",\n";
        log_file << "  \"primes_parallel\": " << parallel_time_primes << ",\n";
        log_file << "  \"sort_serial\": " << serial_time_sort << ",\n";
        log_file << "  \"sort_parallel\": " << parallel_time_sort << "\n";
        log_file << "}\n";
        log_file.close();
    } else {
        // Non-root processes participate in the quicksort test
        std::vector<int> dummy_array(SORT_SIZE);
        MPI_Bcast(dummy_array.data(), SORT_SIZE, MPI_INT, 0, MPI_COMM_WORLD);
        quicksort_parallel(dummy_array);
    }
    
    // Finalize MPI
    MPI_Finalize();
    return 0;
} 