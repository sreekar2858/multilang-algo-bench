#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <math.h>
#include <string.h>
#include <mpi.h>
#ifdef _WIN32
#include <windows.h>
#include <direct.h>
#else
#include <unistd.h>
#include <sys/stat.h>
#endif

// Global variables for process management
int g_world_size = 1;
int g_rank = 0;

// Get number of processors
int get_num_processors(void) {
#ifdef _WIN32
    SYSTEM_INFO sysinfo;
    GetSystemInfo(&sysinfo);
    return sysinfo.dwNumberOfProcessors;
#else
    return sysconf(_SC_NPROCESSORS_ONLN);
#endif
}

// Fibonacci implementations
unsigned long long fibonacci_serial(int n) {
    if (n <= 1) return n;
    return fibonacci_serial(n - 1) + fibonacci_serial(n - 2);
}

unsigned long long fibonacci_dynamic(int n) {
    if (n <= 1) return n;
    unsigned long long* fib = (unsigned long long*)calloc(n + 1, sizeof(unsigned long long));
    fib[1] = 1;
    
    for (int i = 2; i <= n; i++) {
        fib[i] = fib[i-1] + fib[i-2];
    }
    
    unsigned long long result = fib[n];
    free(fib);
    return result;
}

// Calculate a chunk of Fibonacci sequence
unsigned long long* fibonacci_chunk(int start, int end) {
    unsigned long long* fib = (unsigned long long*)calloc(end + 1, sizeof(unsigned long long));
    
    if (fib == NULL) {
        fprintf(stderr, "Memory allocation failed in fibonacci_chunk\n");
        return NULL;
    }
    
    if (start <= 1 && end >= 1) {
        fib[1] = 1;
    }
    
    for (int i = (start <= 2 ? 2 : start); i <= end; i++) {
        fib[i] = fib[i-1] + fib[i-2];
    }
    
    unsigned long long* result = (unsigned long long*)malloc((end - start + 1) * sizeof(unsigned long long));
    if (result == NULL) {
        fprintf(stderr, "Memory allocation failed for result in fibonacci_chunk\n");
        free(fib);
        return NULL;
    }
    
    memcpy(result, &fib[start], (end - start + 1) * sizeof(unsigned long long));
    free(fib);
    return result;
}

unsigned long long* fibonacci_parallel(int n, int* result_size) {
    if (n <= 0) {
        *result_size = 0;
        return NULL;
    }
    
    // Manually set the first two values
    unsigned long long* final_result = NULL;
    if (g_rank == 0) {
        final_result = (unsigned long long*)malloc((n + 1) * sizeof(unsigned long long));
        if (final_result == NULL) {
            fprintf(stderr, "Memory allocation failed for final_result\n");
            *result_size = 0;
            return NULL;
        }
        
        *result_size = 0;
        if (n >= 0) {
            final_result[0] = 0;
            *result_size = 1;
        }
        if (n >= 1) {
            final_result[1] = 1;
            *result_size = 2;
        }
    }
    
    // For small n, let rank 0 do all the work
    if (n < 10) {
        if (g_rank == 0) {
            for (int i = 2; i <= n; i++) {
                final_result[i] = final_result[i-1] + final_result[i-2];
                *result_size = i + 1;
            }
        }
        return final_result;
    }
    
    // Distribute the work among processes
    int chunk_size = (n + g_world_size - 1) / g_world_size;
    int start = g_rank * chunk_size;
    int end = (g_rank + 1) * chunk_size - 1;
    if (end >= n) end = n;
    
    // Special case for rank 0 to include the initial values
    if (g_rank == 0 && start < 2) {
        // First two values already set, start from 2
        start = 2;
    }
    
    // If start > end, this rank doesn't need to calculate anything
    int local_size = (start <= end) ? (end - start + 1) : 0;
    unsigned long long* local_result = NULL;
    
    // Calculate local chunk
    if (local_size > 0) {
        // If rank > 0, we need to receive the previous two values
        if (g_rank > 0) {
            unsigned long long prev_values[2];
            MPI_Recv(prev_values, 2, MPI_UNSIGNED_LONG_LONG, g_rank - 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            
            // Calculate local chunk with received values
            unsigned long long* fib = (unsigned long long*)calloc(end + 1, sizeof(unsigned long long));
            fib[start - 2] = prev_values[0];
            fib[start - 1] = prev_values[1];
            
            for (int i = start; i <= end; i++) {
                fib[i] = fib[i-1] + fib[i-2];
            }
            
            local_result = (unsigned long long*)malloc(local_size * sizeof(unsigned long long));
            memcpy(local_result, &fib[start], local_size * sizeof(unsigned long long));
            
            // Send last two values to next rank if needed
            if (g_rank < g_world_size - 1) {
                unsigned long long next_values[2] = {fib[end - 1], fib[end]};
                MPI_Send(next_values, 2, MPI_UNSIGNED_LONG_LONG, g_rank + 1, 0, MPI_COMM_WORLD);
            }
            
            free(fib);
        } else {
            // Rank 0
            for (int i = start; i <= end; i++) {
                final_result[i] = final_result[i-1] + final_result[i-2];
            }
            
            // Send last two values to next rank if needed
            if (g_world_size > 1) {
                unsigned long long next_values[2] = {final_result[end - 1], final_result[end]};
                MPI_Send(next_values, 2, MPI_UNSIGNED_LONG_LONG, 1, 0, MPI_COMM_WORLD);
            }
            
            local_result = (unsigned long long*)malloc(local_size * sizeof(unsigned long long));
            memcpy(local_result, &final_result[start], local_size * sizeof(unsigned long long));
        }
    }
    
    // Gather results to rank 0
    if (g_rank == 0) {
        // Rank 0 already has its portion, receive others
        *result_size = n + 1;  // Full size including 0
        
        for (int i = 1; i < g_world_size; i++) {
            int remote_start = i * chunk_size;
            // Skip ranks that don't have work to do
            if (remote_start >= n) continue;
            
            int remote_end = (i + 1) * chunk_size - 1;
            if (remote_end >= n) remote_end = n;
            
            int remote_size = remote_end - remote_start + 1;
            
            // Receive the chunk from the current rank
            MPI_Recv(&final_result[remote_start], remote_size, MPI_UNSIGNED_LONG_LONG, 
                    i, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    } else if (local_size > 0) {
        // Send local results to rank 0
        MPI_Send(local_result, local_size, MPI_UNSIGNED_LONG_LONG, 0, 1, MPI_COMM_WORLD);
    }
    
    if (local_result != NULL && g_rank != 0) {
        free(local_result);
    }
    
    return final_result;
}

// Prime number implementations
bool is_prime(int n) {
    if (n < 2) return false;
    int sqrt_n = (int)sqrt(n);
    for (int i = 2; i <= sqrt_n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

int* find_primes_range(int start, int end, int* count) {
    int capacity = (end - start + 1); // Maximum possible primes
    
    int* primes = (int*)malloc(capacity * sizeof(int));
    if (primes == NULL) {
        fprintf(stderr, "Memory allocation failed in find_primes_range\n");
        *count = 0;
        return NULL;
    }
    
    *count = 0;
    
    for (int n = start; n <= end; n++) {
        if (is_prime(n)) {
            primes[(*count)++] = n;
        }
    }
    
    return primes;
}

int* find_primes_serial(int limit, int* count) {
    int* primes = (int*)malloc(limit * sizeof(int));
    *count = 0;
    
    for (int n = 2; n <= limit; n++) {
        if (is_prime(n)) {
            primes[(*count)++] = n;
        }
    }
    
    return primes;
}

int* find_primes_parallel(int limit, int* count) {
    if (limit < 2) {
        *count = 0;
        return NULL;
    }
    
    int chunk_size = (limit - 1) / g_world_size;
    int start = g_rank * chunk_size + 2;
    int end = (g_rank + 1) * chunk_size + 1;
    if (g_rank == g_world_size - 1) end = limit;
    
    int local_count = 0;
    int* local_primes = find_primes_range(start, end, &local_count);
    
    // Root process coordinates
    int* all_primes = NULL;
    if (g_rank == 0) {
        // First gather the counts
        int* counts = (int*)malloc(g_world_size * sizeof(int));
        counts[0] = local_count;
        
        for (int i = 1; i < g_world_size; i++) {
            MPI_Recv(&counts[i], 1, MPI_INT, i, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
        
        // Calculate total count and displacements
        int total_count = 0;
        int* displs = (int*)malloc(g_world_size * sizeof(int));
        
        for (int i = 0; i < g_world_size; i++) {
            displs[i] = total_count;
            total_count += counts[i];
        }
        
        // Allocate space for all primes
        all_primes = (int*)malloc(total_count * sizeof(int));
        
        // Copy local primes
        memcpy(all_primes, local_primes, local_count * sizeof(int));
        
        // Receive primes from other processes
        for (int i = 1; i < g_world_size; i++) {
            MPI_Recv(all_primes + displs[i], counts[i], MPI_INT, i, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
        
        // Sort all primes (use insertion sort for small result sets)
        for (int i = 1; i < total_count; i++) {
            int key = all_primes[i];
            int j = i - 1;
            
            while (j >= 0 && all_primes[j] > key) {
                all_primes[j + 1] = all_primes[j];
                j--;
            }
            all_primes[j + 1] = key;
        }
        
        *count = total_count;
        free(counts);
        free(displs);
    } else {
        // Send local count to root
        MPI_Send(&local_count, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
        
        // Send local primes to root
        if (local_count > 0) {
            MPI_Send(local_primes, local_count, MPI_INT, 0, 1, MPI_COMM_WORLD);
        }
    }
    
    // Free local primes
    if (local_primes != NULL) {
        free(local_primes);
    }
    
    return all_primes;
}

// QuickSort implementations
void swap(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int partition(int* arr, int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return i + 1;
}

void quicksort_serial(int* arr, int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quicksort_serial(arr, low, pi - 1);
        quicksort_serial(arr, pi + 1, high);
    }
}

typedef struct {
    int low;
    int high;
} QuickSortRange;

void quicksort_parallel(int* arr, int size) {
    if (arr == NULL || size <= 1) {
        return;
    }
    
    // Split the array across processes
    int local_size = size / g_world_size;
    int local_start = g_rank * local_size;
    int local_end = (g_rank == g_world_size - 1) ? (size - 1) : ((g_rank + 1) * local_size - 1);
    
    // Allocate local array
    int* local_arr = (int*)malloc((local_end - local_start + 1) * sizeof(int));
    
    // Scatter the array to all processes
    MPI_Scatter(arr, local_size, MPI_INT, local_arr, local_size, MPI_INT, 0, MPI_COMM_WORLD);
    
    // Sort local portion
    quicksort_serial(local_arr, 0, local_end - local_start);
    
    // Gather sorted portions back to root
    MPI_Gather(local_arr, local_size, MPI_INT, arr, local_size, MPI_INT, 0, MPI_COMM_WORLD);
    
    // Root process performs the final merge step
    if (g_rank == 0) {
        // Merge step (simple implementation using temporary array)
        int* temp = (int*)malloc(size * sizeof(int));
        for (int i = 0; i < g_world_size - 1; i++) {
            int left = 0;
            int right = 0;
            int left_end = (i + 1) * local_size;
            int right_end = (i + 2) * local_size;
            if (i == g_world_size - 2) right_end = size;
            
            int pos = 0;
            
            while (left < left_end && right < right_end) {
                if (arr[left] <= arr[right]) {
                    temp[pos++] = arr[left++];
                } else {
                    temp[pos++] = arr[right++];
                }
            }
            
            while (left < left_end) {
                temp[pos++] = arr[left++];
            }
            
            while (right < right_end) {
                temp[pos++] = arr[right++];
            }
            
            memcpy(arr, temp, pos * sizeof(int));
        }
        
        free(temp);
    }
    
    free(local_arr);
}

// JSON writing helper functions
void write_json_start(FILE* f) {
    fprintf(f, "{\n");
}

void write_json_string(FILE* f, const char* key, const char* value, bool last) {
    fprintf(f, "  \"%s\": \"%s\"%s\n", key, value, last ? "" : ",");
}

void write_json_number(FILE* f, const char* key, double value, bool last) {
    fprintf(f, "  \"%s\": %f%s\n", key, value, last ? "" : ",");
}

void write_json_end(FILE* f) {
    fprintf(f, "}\n");
}

int main(int argc, char** argv) {
    // Initialize MPI
    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &g_world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &g_rank);
    
    if (g_rank == 0) {
        printf("Running with %d MPI processes\n", g_world_size);
    }
    
    const int PRIME_LIMIT = 100000;
    const int SORT_SIZE = 1000000;
    const int FIB_N = 100000;
    
    if (g_rank == 0) {
#ifdef _WIN32
        _mkdir("logs");
#else
        mkdir("logs", 0777);
#endif
    }
    
    // Ensure all processes start at the same time
    MPI_Barrier(MPI_COMM_WORLD);
    
    double serial_time_fib = 0, parallel_time_fib = 0;
    double serial_time_primes = 0, parallel_time_primes = 0;
    double serial_time_sort = 0, parallel_time_sort = 0;
    double start_time, end_time;
    
    // Fibonacci test
    if (g_rank == 0) {
        printf("\nC MPI Fibonacci Test\n");
        
        // Serial implementation (only rank 0)
        start_time = MPI_Wtime();
        unsigned long long fib_serial = fibonacci_dynamic(FIB_N);
        end_time = MPI_Wtime();
        serial_time_fib = end_time - start_time;
        printf("Serial Time (Dynamic): %.4f seconds\n", serial_time_fib);
    }
    
    // Parallel implementation (all ranks)
    MPI_Barrier(MPI_COMM_WORLD);
    start_time = MPI_Wtime();
    
    int fib_size;
    unsigned long long* fib_parallel = fibonacci_parallel(FIB_N, &fib_size);
    
    end_time = MPI_Wtime();
    if (g_rank == 0) {
        parallel_time_fib = end_time - start_time;
        printf("Parallel Time: %.4f seconds\n", parallel_time_fib);
        free(fib_parallel);
    }
    
    // Prime numbers test
    if (g_rank == 0) {
        printf("\nC MPI Prime Numbers Test\n");
        
        // Serial implementation (only rank 0)
        start_time = MPI_Wtime();
        int count_serial;
        int* primes_serial = find_primes_serial(PRIME_LIMIT, &count_serial);
        end_time = MPI_Wtime();
        serial_time_primes = end_time - start_time;
        printf("Serial Time: %.4f seconds\n", serial_time_primes);
        free(primes_serial);
    }
    
    // Parallel implementation (all ranks)
    MPI_Barrier(MPI_COMM_WORLD);
    start_time = MPI_Wtime();
    
    int count_parallel;
    int* primes_parallel = find_primes_parallel(PRIME_LIMIT, &count_parallel);
    
    end_time = MPI_Wtime();
    if (g_rank == 0) {
        parallel_time_primes = end_time - start_time;
        printf("Parallel Time: %.4f seconds\n", parallel_time_primes);
        free(primes_parallel);
    }
    
    // QuickSort test
    if (g_rank == 0) {
        printf("\nC MPI QuickSort Test\n");
        
        // Create test array
        int* test_array = (int*)malloc(SORT_SIZE * sizeof(int));
        int* array_copy = (int*)malloc(SORT_SIZE * sizeof(int));
        
        srand(time(NULL));
        for (int i = 0; i < SORT_SIZE; i++) {
            test_array[i] = rand() % 1000000 + 1;
        }
        memcpy(array_copy, test_array, SORT_SIZE * sizeof(int));
        
        // Serial implementation (only rank 0)
        start_time = MPI_Wtime();
        quicksort_serial(test_array, 0, SORT_SIZE - 1);
        end_time = MPI_Wtime();
        serial_time_sort = end_time - start_time;
        printf("Serial Time: %.4f seconds\n", serial_time_sort);
        
        // Broadcast the unsorted array to all processes
        MPI_Bcast(array_copy, SORT_SIZE, MPI_INT, 0, MPI_COMM_WORLD);
        
        // Parallel sorting
        start_time = MPI_Wtime();
        quicksort_parallel(array_copy, SORT_SIZE);
        end_time = MPI_Wtime();
        parallel_time_sort = end_time - start_time;
        printf("Parallel Time: %.4f seconds\n", parallel_time_sort);
        
        free(test_array);
        free(array_copy);
        
        // Write results to JSON file
        FILE* log_file = fopen("logs/c_mpi_results.json", "w");
        write_json_start(log_file);
        write_json_string(log_file, "language", "C MPI", false);
        write_json_number(log_file, "process_count", g_world_size, false);
        write_json_number(log_file, "fibonacci_serial", serial_time_fib, false);
        write_json_number(log_file, "fibonacci_parallel", parallel_time_fib, false);
        write_json_number(log_file, "primes_serial", serial_time_primes, false);
        write_json_number(log_file, "primes_parallel", parallel_time_primes, false);
        write_json_number(log_file, "sort_serial", serial_time_sort, false);
        write_json_number(log_file, "sort_parallel", parallel_time_sort, true);
        write_json_end(log_file);
        fclose(log_file);
    } else {
        // Non-root processes participate in the parallel sorting
        int* dummy_array = (int*)malloc(SORT_SIZE * sizeof(int));
        MPI_Bcast(dummy_array, SORT_SIZE, MPI_INT, 0, MPI_COMM_WORLD);
        quicksort_parallel(dummy_array, SORT_SIZE);
        free(dummy_array);
    }
    
    // Finalize MPI
    MPI_Finalize();
    return 0;
} 