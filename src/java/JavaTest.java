import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;
import java.nio.file.*;
import org.json.*;

public class JavaTest {
    private static int processorCount = Runtime.getRuntime().availableProcessors();
    
    private static void setProcessorCount(int count) {
        if (count > 0) {
            processorCount = Math.min(count, Runtime.getRuntime().availableProcessors());
        } else {
            processorCount = Runtime.getRuntime().availableProcessors();
        }
    }
    
    // Fibonacci implementations
    private static long fibonacciSerial(int n) {
        if (n <= 1) return n;
        return fibonacciSerial(n-1) + fibonacciSerial(n-2);
    }
    
    private static long fibonacciDynamic(int n) {
        if (n <= 1) return n;
        long[] fib = new long[n + 1];
        fib[1] = 1;
        for (int i = 2; i <= n; i++) {
            fib[i] = fib[i-1] + fib[i-2];
        }
        return fib[n];
    }
    
    private static class FibonacciTask extends RecursiveTask<long[]> {
        private final int start;
        private final int end;
        
        FibonacciTask(int start, int end) {
            this.start = start;
            this.end = end;
        }
        
        @Override
        protected long[] compute() {
            long[] fib = new long[end + 1];
            if (start <= 1 && end >= 1) fib[1] = 1;
            for (int i = Math.max(2, start); i <= end; i++) {
                fib[i] = fib[i-1] + fib[i-2];
            }
            return Arrays.copyOfRange(fib, start, end + 1);
        }
    }
    
    private static long[] fibonacciParallel(int n) {
        ForkJoinPool pool = ForkJoinPool.commonPool();
        int chunkSize = Math.max(1, n / processorCount);
        List<FibonacciTask> tasks = new ArrayList<>();
        
        // Create tasks for each chunk of work
        for (int i = 0; i < n; i += chunkSize) {
            int end = Math.min(i + chunkSize - 1, n - 1);
            tasks.add(new FibonacciTask(i, end));
        }
        
        // Process chunks in parallel
        List<long[]> results = tasks.stream()
            .map(pool::invoke)
            .collect(Collectors.toList());
            
        // Combine results into the final array
        long[] finalResult = new long[n];
        int pos = 0;
        for (long[] chunk : results) {
            System.arraycopy(chunk, 0, finalResult, pos, chunk.length);
            pos += chunk.length;
        }
        return finalResult;
    }

    private static boolean isPrime(long n) {
        if (n < 2) return false;
        for (long i = 2; i <= Math.sqrt(n); i++) {
            if (n % i == 0) return false;
        }
        return true;
    }

    private static List<Long> findPrimesSerial(long limit) {
        return LongStream.rangeClosed(2, limit)
                .filter(JavaTest::isPrime)
                .boxed()
                .collect(Collectors.toList());
    }

    private static List<Long> findPrimesParallel(long limit) {
        return LongStream.rangeClosed(2, limit)
                .parallel()
                .filter(JavaTest::isPrime)
                .boxed()
                .collect(Collectors.toList());
    }

    private static void quicksortSerial(int[] arr, int low, int high) {
        if (low < high) {
            int pivot = partition(arr, low, high);
            quicksortSerial(arr, low, pivot - 1);
            quicksortSerial(arr, pivot + 1, high);
        }
    }

    private static class QuicksortTask extends RecursiveAction {
        private final int[] arr;
        private final int low;
        private final int high;
        private final int depth;

        QuicksortTask(int[] arr, int low, int high, int depth) {
            this.arr = arr;
            this.low = low;
            this.high = high;
            this.depth = depth;
        }

        @Override
        protected void compute() {
            if (low < high) {
                if (depth <= 0) {
                    quicksortSerial(arr, low, high);
                    return;
                }

                int pivot = partition(arr, low, high);
                invokeAll(
                    new QuicksortTask(arr, low, pivot - 1, depth - 1),
                    new QuicksortTask(arr, pivot + 1, high, depth - 1)
                );
            }
        }
    }

    private static void quicksortParallel(int[] arr) {
        ForkJoinPool pool = ForkJoinPool.commonPool();
        pool.invoke(new QuicksortTask(arr, 0, arr.length - 1, 3));
    }

    private static int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = low - 1;

        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                swap(arr, i, j);
            }
        }
        swap(arr, i + 1, high);
        return i + 1;
    }

    private static void swap(int[] arr, int i, int j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }

    public static void main(String[] args) {
        // Set processor count from command line argument if provided
        if (args.length > 0) {
            try {
                setProcessorCount(Integer.parseInt(args[0]));
            } catch (NumberFormatException e) {
                System.err.println("Invalid processor count: " + args[0]);
            }
        }
        System.out.println("Running with " + processorCount + " processors");

        final long PRIME_LIMIT = 100_000;
        final int SORT_SIZE = 1_000_000;
        final int FIB_N = 100_000;

        // Create logs directory if it doesn't exist
        try {
            Files.createDirectories(Paths.get("logs"));
        } catch (Exception e) {
            System.err.println("Warning: Could not create logs directory: " + e.getMessage());
        }

        JSONObject results = new JSONObject();
        results.put("language", "Java");
        results.put("processor_count", processorCount);

        // Fibonacci sequence test
        System.out.println("\nJava Fibonacci Sequence Test");

        long start = System.nanoTime();
        long fibSerial = fibonacciDynamic(FIB_N);
        double serialTimeFib = (System.nanoTime() - start) / 1e9;
        System.out.printf("Serial Time (Dynamic): %.4f seconds%n", serialTimeFib);
        results.put("fibonacci_serial", serialTimeFib);

        start = System.nanoTime();
        long[] fibParallel = fibonacciParallel(FIB_N);
        double parallelTimeFib = (System.nanoTime() - start) / 1e9;
        System.out.printf("Parallel Time: %.4f seconds%n", parallelTimeFib);
        results.put("fibonacci_parallel", parallelTimeFib);

        // Prime numbers test
        System.out.println("\nJava Prime Numbers Test");

        start = System.nanoTime();
        List<Long> primesSerial = findPrimesSerial(PRIME_LIMIT);
        double serialTimePrimes = (System.nanoTime() - start) / 1e9;
        System.out.printf("Serial Time: %.4f seconds%n", serialTimePrimes);
        results.put("primes_serial", serialTimePrimes);

        start = System.nanoTime();
        List<Long> primesParallel = findPrimesParallel(PRIME_LIMIT);
        double parallelTimePrimes = (System.nanoTime() - start) / 1e9;
        System.out.printf("Parallel Time: %.4f seconds%n", parallelTimePrimes);
        results.put("primes_parallel", parallelTimePrimes);

        // QuickSort test
        System.out.println("\nJava QuickSort Test");

        Random rand = new Random();
        int[] testArray = rand.ints(SORT_SIZE, 1, 1_000_001).toArray();
        int[] arrayCopy = Arrays.copyOf(testArray, testArray.length);

        start = System.nanoTime();
        quicksortSerial(testArray, 0, testArray.length - 1);
        double serialTimeSort = (System.nanoTime() - start) / 1e9;
        System.out.printf("Serial Time: %.4f seconds%n", serialTimeSort);
        results.put("sort_serial", serialTimeSort);

        start = System.nanoTime();
        quicksortParallel(arrayCopy);
        double parallelTimeSort = (System.nanoTime() - start) / 1e9;
        System.out.printf("Parallel Time: %.4f seconds%n", parallelTimeSort);
        results.put("sort_parallel", parallelTimeSort);

        // Write results to JSON file
        try {
            // Create path to logs directory in project root
            Path currentPath = Paths.get("").toAbsolutePath();
            Path logsPath;
            
            // If we're in the bin directory, go up one level
            if (currentPath.endsWith("bin")) {
                logsPath = currentPath.getParent().resolve("logs");
            } else {
                // Assume we're in the project root
                logsPath = currentPath.resolve("logs");
            }
            
            // Create logs directory if it doesn't exist
            Files.createDirectories(logsPath);
            
            // Write to the logs directory with absolute path
            Files.write(
                logsPath.resolve("java_results.json"),
                results.toString(2).getBytes(),
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING
            );
            System.out.println("Results written to " + logsPath.resolve("java_results.json"));
        } catch (Exception e) {
            System.err.println("Error writing results: " + e.getMessage());
            // Try writing to current directory as fallback
            try {
                Files.write(
                    Paths.get("java_results.json"),
                    results.toString(2).getBytes(),
                    StandardOpenOption.CREATE,
                    StandardOpenOption.TRUNCATE_EXISTING
                );
                System.out.println("Results written to current directory as java_results.json");
            } catch (Exception e2) {
                System.err.println("Error writing to current directory: " + e2.getMessage());
            }
        }
    }
}