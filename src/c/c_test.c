#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <math.h>
#include <string.h>
#include <pthread.h>
#ifdef _WIN32
#include <windows.h>
#include <direct.h>
#else
#include <unistd.h>
#include <sys/stat.h>
#endif

// Global variables for thread management
int g_num_threads = 1;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

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

// Set thread count
void set_thread_count(int count) {
    if (count <= 0) {
        g_num_threads = get_num_processors();
    } else {
        g_num_threads = (count < get_num_processors()) ? count : get_num_processors();
    }
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

// Structure for fibonacci chunk calculation
typedef struct {
    int start;
    int end;
    unsigned long long* result;
    int result_size;
} FibChunkArgs;

void* fibonacci_chunk(void* args) {
    FibChunkArgs* fargs = (FibChunkArgs*)args;
    unsigned long long* fib = (unsigned long long*)calloc(fargs->end + 1, sizeof(unsigned long long));
    
    if (fib == NULL) {
        fprintf(stderr, "Memory allocation failed in fibonacci_chunk\n");
        fargs->result = NULL;
        fargs->result_size = 0;
        return NULL;
    }
    
    if (fargs->start <= 1 && fargs->end >= 1) {
        fib[1] = 1;
    }
    
    for (int i = (fargs->start <= 2 ? 2 : fargs->start); i <= fargs->end; i++) {
        fib[i] = fib[i-1] + fib[i-2];
    }
    
    fargs->result = (unsigned long long*)malloc((fargs->end - fargs->start + 1) * sizeof(unsigned long long));
    if (fargs->result == NULL) {
        fprintf(stderr, "Memory allocation failed for result in fibonacci_chunk\n");
        free(fib);
        fargs->result_size = 0;
        return NULL;
    }
    
    memcpy(fargs->result, &fib[fargs->start], (fargs->end - fargs->start + 1) * sizeof(unsigned long long));
    fargs->result_size = fargs->end - fargs->start + 1;
    
    free(fib);
    return NULL;
}

unsigned long long* fibonacci_parallel(int n, int* result_size) {
    if (n <= 0) {
        *result_size = 0;
        return NULL;
    }
    
    // Use fewer threads for small n to reduce overhead
    int num_threads = (n < g_num_threads) ? n : g_num_threads;
    int chunk_size = (n + num_threads - 1) / num_threads;
    
    pthread_t* threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));
    if (threads == NULL) {
        fprintf(stderr, "Memory allocation failed for threads\n");
        *result_size = 0;
        return NULL;
    }
    
    FibChunkArgs* args = (FibChunkArgs*)malloc(num_threads * sizeof(FibChunkArgs));
    if (args == NULL) {
        fprintf(stderr, "Memory allocation failed for args\n");
        free(threads);
        *result_size = 0;
        return NULL;
    }
    
    unsigned long long* final_result = (unsigned long long*)malloc((n + 1) * sizeof(unsigned long long));
    if (final_result == NULL) {
        fprintf(stderr, "Memory allocation failed for final_result\n");
        free(threads);
        free(args);
        *result_size = 0;
        return NULL;
    }
    
    *result_size = 0;
    
    // Handle fibonacci(0) and fibonacci(1) directly
    if (n >= 0) final_result[0] = 0;
    if (n >= 1) final_result[1] = 1;
    
    for (int i = 0; i < num_threads; i++) {
        args[i].start = i * chunk_size;
        if (args[i].start == 0 && chunk_size > 1) {
            // Skip 0 as we've handled it directly
            args[i].start = 1;
        }
        args[i].end = (i + 1) * chunk_size - 1;
        if (args[i].end >= n) args[i].end = n;
        
        // Skip thread creation if range is invalid
        if (args[i].start > args[i].end) {
            args[i].result = NULL;
            args[i].result_size = 0;
            continue;
        }
        
        if (pthread_create(&threads[i], NULL, fibonacci_chunk, &args[i]) != 0) {
            fprintf(stderr, "Thread creation failed for thread %d\n", i);
            // Clean up already created threads
            for (int j = 0; j < i; j++) {
                pthread_join(threads[j], NULL);
                if (args[j].result != NULL) {
                    free(args[j].result);
                    args[j].result = NULL;
                }
            }
            free(threads);
            free(args);
            free(final_result);
            *result_size = 0;
            return NULL;
        }
    }
    
    // Manually set the first two values
    int pos = 0;
    if (n >= 0) {
        final_result[pos++] = 0;
        *result_size = 1;
    }
    if (n >= 1) {
        final_result[pos++] = 1;
        *result_size = 2;
    }
    
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
        if (args[i].result != NULL && args[i].result_size > 0) {
            int start_idx = args[i].start;
            
            // Copy results, skipping the first two if they were directly set
            for (int j = 0; j < args[i].result_size; j++) {
                int idx = start_idx + j;
                if (idx >= 2) { // Skip 0 and 1 as we've already set them
                    final_result[idx] = args[i].result[j];
                    if (idx >= *result_size) {
                        *result_size = idx + 1;
                    }
                }
            }
            
            free(args[i].result);
        }
    }
    
    free(threads);
    free(args);
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

typedef struct {
    int start;
    int end;
    int* primes;
    int count;
} PrimeArgs;

void* find_primes_thread(void* args) {
    PrimeArgs* pargs = (PrimeArgs*)args;
    int capacity = (pargs->end - pargs->start + 1); // Maximum possible primes
    
    pargs->primes = (int*)malloc(capacity * sizeof(int));
    if (pargs->primes == NULL) {
        fprintf(stderr, "Memory allocation failed in find_primes_thread\n");
        pargs->count = 0;
        return NULL;
    }
    
    pargs->count = 0;
    
    for (int n = pargs->start; n <= pargs->end; n++) {
        if (is_prime(n)) {
            pargs->primes[pargs->count++] = n;
        }
    }
    
    return NULL;
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
    
    // Use fewer threads for small ranges
    int num_threads = (limit < g_num_threads * 1000) ? (limit / 1000 + 1) : g_num_threads;
    num_threads = (num_threads > g_num_threads) ? g_num_threads : num_threads;
    
    pthread_t* threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));
    if (threads == NULL) {
        fprintf(stderr, "Memory allocation failed for threads\n");
        *count = 0;
        return NULL;
    }
    
    PrimeArgs* args = (PrimeArgs*)malloc(num_threads * sizeof(PrimeArgs));
    if (args == NULL) {
        fprintf(stderr, "Memory allocation failed for args\n");
        free(threads);
        *count = 0;
        return NULL;
    }
    
    int chunk_size = (limit - 1) / num_threads;
    *count = 0;
    
    for (int i = 0; i < num_threads; i++) {
        args[i].start = i * chunk_size + 2;
        args[i].end = (i + 1) * chunk_size + 1;
        if (i == num_threads - 1) args[i].end = limit;
        
        if (pthread_create(&threads[i], NULL, find_primes_thread, &args[i]) != 0) {
            fprintf(stderr, "Thread creation failed for thread %d\n", i);
            // Clean up already created threads
            for (int j = 0; j < i; j++) {
                pthread_join(threads[j], NULL);
                if (args[j].primes != NULL) {
                    free(args[j].primes);
                    args[j].primes = NULL;
                }
            }
            free(threads);
            free(args);
            *count = 0;
            return NULL;
        }
    }
    
    // Calculate total count first
    int total_count = 0;
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
        total_count += args[i].count;
    }
    
    if (total_count == 0) {
        for (int i = 0; i < num_threads; i++) {
            if (args[i].primes != NULL) {
                free(args[i].primes);
            }
        }
        free(threads);
        free(args);
        *count = 0;
        return NULL;
    }
    
    int* all_primes = (int*)malloc(total_count * sizeof(int));
    if (all_primes == NULL) {
        fprintf(stderr, "Memory allocation failed for all_primes\n");
        for (int i = 0; i < num_threads; i++) {
            if (args[i].primes != NULL) {
                free(args[i].primes);
            }
        }
        free(threads);
        free(args);
        *count = 0;
        return NULL;
    }
    
    int pos = 0;
    
    for (int i = 0; i < num_threads; i++) {
        if (args[i].primes != NULL && args[i].count > 0) {
            memcpy(&all_primes[pos], args[i].primes, args[i].count * sizeof(int));
            pos += args[i].count;
            free(args[i].primes);
        }
    }
    
    *count = total_count;
    free(threads);
    free(args);
    
    // Use insertion sort for small result sets, bubble sort is too slow for large sets
    for (int i = 1; i < total_count; i++) {
        int key = all_primes[i];
        int j = i - 1;
        
        while (j >= 0 && all_primes[j] > key) {
            all_primes[j + 1] = all_primes[j];
            j--;
        }
        all_primes[j + 1] = key;
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
    int* arr;
    int low;
    int high;
    int depth;
} QuickSortArgs;

void* quicksort_thread(void* args) {
    QuickSortArgs* qargs = (QuickSortArgs*)args;
    
    if (qargs->low >= qargs->high) {
        return NULL;
    }
    
    if (qargs->depth <= 0 || (qargs->high - qargs->low) < 10000) {
        quicksort_serial(qargs->arr, qargs->low, qargs->high);
        return NULL;
    }
    
    int pi = partition(qargs->arr, qargs->low, qargs->high);
    
    // Create thread-specific args on heap to avoid stack issues
    QuickSortArgs* left_args = (QuickSortArgs*)malloc(sizeof(QuickSortArgs));
    if (left_args == NULL) {
        fprintf(stderr, "Memory allocation failed for left_args\n");
        quicksort_serial(qargs->arr, qargs->low, qargs->high);
        return NULL;
    }
    
    left_args->arr = qargs->arr;
    left_args->low = qargs->low;
    left_args->high = pi - 1;
    left_args->depth = qargs->depth - 1;
    
    pthread_t left_thread;
    if (pthread_create(&left_thread, NULL, quicksort_thread, left_args) != 0) {
        fprintf(stderr, "Thread creation failed for left partition\n");
        free(left_args);
        // Fall back to serial sorting
        quicksort_serial(qargs->arr, qargs->low, pi - 1);
        quicksort_serial(qargs->arr, pi + 1, qargs->high);
        return NULL;
    }
    
    // Process right partition in current thread
    quicksort_serial(qargs->arr, pi + 1, qargs->high);
    
    // Wait for left partition to complete
    pthread_join(left_thread, NULL);
    free(left_args);
    
    return NULL;
}

void quicksort_parallel(int* arr, int size) {
    if (arr == NULL || size <= 1) {
        return;
    }
    
    QuickSortArgs args = {arr, 0, size - 1, 2}; // Reduced depth limit to 2
    quicksort_thread(&args);
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
    // Set thread count from command line argument if provided
    if (argc > 1) {
        set_thread_count(atoi(argv[1]));
    } else {
        set_thread_count(0); // Use all available processors
    }
    
    printf("Running with %d threads\n", g_num_threads);
    
    const int PRIME_LIMIT = 100000;
    const int SORT_SIZE = 1000000;
    const int FIB_N = 35;
    
#ifdef _WIN32
    _mkdir("logs");
#else
    mkdir("logs", 0777);
#endif
    
    double serial_time_fib, parallel_time_fib;
    double serial_time_primes, parallel_time_primes;
    double serial_time_sort, parallel_time_sort;
    clock_t start;
    
    // Fibonacci test
    printf("\nC Fibonacci Test\n");
    
    start = clock();
    unsigned long long fib_serial = fibonacci_dynamic(FIB_N);
    serial_time_fib = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Serial Time (Dynamic): %.4f seconds\n", serial_time_fib);
    
    start = clock();
    int fib_size;
    unsigned long long* fib_parallel = fibonacci_parallel(FIB_N, &fib_size);
    parallel_time_fib = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Parallel Time: %.4f seconds\n", parallel_time_fib);
    free(fib_parallel);
    
    // Prime numbers test
    printf("\nC Prime Numbers Test\n");
    
    start = clock();
    int count_serial;
    int* primes_serial = find_primes_serial(PRIME_LIMIT, &count_serial);
    serial_time_primes = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Serial Time: %.4f seconds\n", serial_time_primes);
    free(primes_serial);
    
    start = clock();
    int count_parallel;
    int* primes_parallel = find_primes_parallel(PRIME_LIMIT, &count_parallel);
    parallel_time_primes = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Parallel Time: %.4f seconds\n", parallel_time_primes);
    free(primes_parallel);
    
    // QuickSort test
    printf("\nC QuickSort Test\n");
    
    int* test_array = (int*)malloc(SORT_SIZE * sizeof(int));
    int* array_copy = (int*)malloc(SORT_SIZE * sizeof(int));
    
    srand(time(NULL));
    for (int i = 0; i < SORT_SIZE; i++) {
        test_array[i] = rand() % 1000000 + 1;
    }
    memcpy(array_copy, test_array, SORT_SIZE * sizeof(int));
    
    start = clock();
    quicksort_serial(test_array, 0, SORT_SIZE - 1);
    serial_time_sort = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Serial Time: %.4f seconds\n", serial_time_sort);
    
    start = clock();
    quicksort_parallel(array_copy, SORT_SIZE);
    parallel_time_sort = (double)(clock() - start) / CLOCKS_PER_SEC;
    printf("Parallel Time: %.4f seconds\n", parallel_time_sort);
    
    free(test_array);
    free(array_copy);
    
    // Write results to JSON file
    FILE* log_file = fopen("logs/c_results.json", "w");
    write_json_start(log_file);
    write_json_string(log_file, "language", "C", false);
    write_json_number(log_file, "thread_count", g_num_threads, false);
    write_json_number(log_file, "fibonacci_serial", serial_time_fib, false);
    write_json_number(log_file, "fibonacci_parallel", parallel_time_fib, false);
    write_json_number(log_file, "primes_serial", serial_time_primes, false);
    write_json_number(log_file, "primes_parallel", parallel_time_primes, false);
    write_json_number(log_file, "sort_serial", serial_time_sort, false);
    write_json_number(log_file, "sort_parallel", parallel_time_sort, true);
    write_json_end(log_file);
    fclose(log_file);
    
    return 0;
}