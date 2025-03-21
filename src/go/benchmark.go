package main

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"sync"
	"time"
	"io/ioutil"
)

// Global variable for process count
var numProcessors = runtime.NumCPU()

func setProcessorCount(count int) {
	if count > 0 {
		numProcessors = min(count, runtime.NumCPU())
	} else {
		numProcessors = runtime.NumCPU()
	}
	runtime.GOMAXPROCS(numProcessors)
}

// Fibonacci implementations
func fibonacciSerial(n int) uint64 {
	if n <= 1 {
		return uint64(n)
	}
	return fibonacciSerial(n-1) + fibonacciSerial(n-2)
}

func fibonacciDynamic(n int) uint64 {
	if n <= 1 {
		return uint64(n)
	}
	fib := make([]uint64, n+1)
	fib[1] = 1
	for i := 2; i <= n; i++ {
		fib[i] = fib[i-1] + fib[i-2]
	}
	return fib[n]
}

func fibonacciChunk(start, end int, result chan<- []uint64) {
	fib := make([]uint64, end+1)
	if start <= 1 && end >= 1 {
		fib[1] = 1
	}
	for i := max(2, start); i <= end; i++ {
		fib[i] = fib[i-1] + fib[i-2]
	}
	result <- fib[start : end+1]
}

func fibonacciParallel(n int) []uint64 {
	chunkSize := max(1, n/numProcessors)
	results := make(chan []uint64, numProcessors)
	var wg sync.WaitGroup

	for i := 0; i < n; i += chunkSize {
		wg.Add(1)
		end := min(i+chunkSize, n)
		go func(start, end int) {
			defer wg.Done()
			fibonacciChunk(start, end, results)
		}(i, end)
	}

	go func() {
		wg.Wait()
		close(results)
	}()

	var finalResult []uint64
	for chunk := range results {
		finalResult = append(finalResult, chunk...)
	}
	return finalResult
}

func isPrime(n int) bool {
	if n < 2 {
		return false
	}
	sqrt := int(math.Sqrt(float64(n)))
	for i := 2; i <= sqrt; i++ {
		if n%i == 0 {
			return false
		}
	}
	return true
}

func findPrimesSerial(limit int) []int {
	var primes []int
	for n := 2; n <= limit; n++ {
		if isPrime(n) {
			primes = append(primes, n)
		}
	}
	return primes
}

func findPrimesParallel(limit int) []int {
	numCPU := runtime.NumCPU()
	chunkSize := limit / numCPU
	var wg sync.WaitGroup
	var mu sync.Mutex
	var allPrimes []int

	for i := 0; i < numCPU; i++ {
		wg.Add(1)
		start := i*chunkSize + 2
		end := (i + 1) * chunkSize
		if i == numCPU-1 {
			end = limit
		}

		go func(start, end int) {
			defer wg.Done()
			localPrimes := make([]int, 0)
			for n := start; n <= end; n++ {
				if isPrime(n) {
					localPrimes = append(localPrimes, n)
				}
			}
			mu.Lock()
			allPrimes = append(allPrimes, localPrimes...)
			mu.Unlock()
		}(start, end)
	}

	wg.Wait()
	return allPrimes
}

func quicksortSerial(arr []int) []int {
	if len(arr) <= 1 {
		return arr
	}

	pivot := arr[len(arr)-1]
	var left, right []int

	for i := 0; i < len(arr)-1; i++ {
		if arr[i] <= pivot {
			left = append(left, arr[i])
		} else {
			right = append(right, arr[i])
		}
	}

	left = quicksortSerial(left)
	right = quicksortSerial(right)

	return append(append(left, pivot), right...)
}

func quicksortParallel(arr []int, depth int) []int {
	if len(arr) <= 1 {
		return arr
	}

	if depth <= 0 {
		return quicksortSerial(arr)
	}

	pivot := arr[len(arr)-1]
	var left, right []int

	for i := 0; i < len(arr)-1; i++ {
		if arr[i] <= pivot {
			left = append(left, arr[i])
		} else {
			right = append(right, arr[i])
		}
	}

	var wg sync.WaitGroup
	wg.Add(2)

	var sortedLeft, sortedRight []int

	go func() {
		defer wg.Done()
		sortedLeft = quicksortParallel(left, depth-1)
	}()

	go func() {
		defer wg.Done()
		sortedRight = quicksortParallel(right, depth-1)
	}()

	wg.Wait()

	return append(append(sortedLeft, pivot), sortedRight...)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

type BenchmarkResults struct {
	Language          string  `json:"language"`
	ProcessCount      int     `json:"process_count"`
	FibonacciSerial  float64 `json:"fibonacci_serial"`
	FibonacciParallel float64 `json:"fibonacci_parallel"`
	PrimesSerial     float64 `json:"primes_serial"`
	PrimesParallel   float64 `json:"primes_parallel"`
	SortSerial       float64 `json:"sort_serial"`
	SortParallel     float64 `json:"sort_parallel"`
}

func main() {
	// Set process count from command line argument if provided
	if len(os.Args) > 1 {
		if count, err := strconv.Atoi(os.Args[1]); err == nil {
			setProcessorCount(count)
		}
	}
	fmt.Printf("Running with %d processors\n", numProcessors)

	const (
		primeLimit = 100000
		sortSize   = 1000000
		fibN       = 100000
	)

	// Create logs directory with absolute path from working directory
	cwd, err := os.Getwd()
	if err != nil {
		fmt.Println("Error getting current directory:", err)
	}
	
	// Use absolute path to logs directory in project root
	var logsPath string
	if filepath.Base(cwd) == "go" {
		// If we're in the go directory
		logsPath = filepath.Join(cwd, "../../logs")
	} else if filepath.Base(cwd) == "bin" {
		// If we're in the bin directory
		logsPath = filepath.Join(cwd, "../logs")
	} else {
		// Assume we're in the project root
		logsPath = filepath.Join(cwd, "logs")
	}
	
	// Make sure the directory exists
	err = os.MkdirAll(logsPath, 0755)
	if err != nil {
		fmt.Println("Error creating logs directory:", err)
	}

	results := BenchmarkResults{
		Language:     "Go",
		ProcessCount: numProcessors,
	}

	// Fibonacci sequence test
	fmt.Println("\nGo Fibonacci Sequence Test")
	start := time.Now()
	fibVal := fibonacciDynamic(fibN)
	results.FibonacciSerial = time.Since(start).Seconds()
	fmt.Printf("Serial Time (Dynamic): %.4f seconds\n", results.FibonacciSerial)
	fmt.Printf("Fibonacci(%d) = %d\n", fibN, fibVal)

	start = time.Now()
	fibSlice := fibonacciParallel(fibN)
	results.FibonacciParallel = time.Since(start).Seconds()
	fmt.Printf("Parallel Time: %.4f seconds\n", results.FibonacciParallel)
	fmt.Printf("Fibonacci sequence length: %d\n", len(fibSlice))

	// Prime numbers test
	fmt.Println("\nGo Prime Numbers Test")

	start = time.Now()
	primes := findPrimesSerial(primeLimit)
	results.PrimesSerial = time.Since(start).Seconds()
	fmt.Printf("Serial Time: %.4f seconds\n", results.PrimesSerial)
	fmt.Printf("Found %d primes up to %d\n", len(primes), primeLimit)

	start = time.Now()
	primesPar := findPrimesParallel(primeLimit)
	results.PrimesParallel = time.Since(start).Seconds()
	fmt.Printf("Parallel Time: %.4f seconds\n", results.PrimesParallel)
	fmt.Printf("Found %d primes (parallel) up to %d\n", len(primesPar), primeLimit)

	// QuickSort test
	fmt.Println("\nGo QuickSort Test")

	testArray := make([]int, sortSize)
	for i := range testArray {
		testArray[i] = rand.Intn(1000000) + 1
	}
	arrayCopy := make([]int, len(testArray))
	copy(arrayCopy, testArray)

	start = time.Now()
	quicksortSerial(testArray)
	results.SortSerial = time.Since(start).Seconds()
	fmt.Printf("Serial Time: %.4f seconds\n", results.SortSerial)

	start = time.Now()
	maxDepth := 3 // Control parallel recursion depth
	quicksortParallel(arrayCopy, maxDepth)
	results.SortParallel = time.Since(start).Seconds()
	fmt.Printf("Parallel Time: %.4f seconds\n", results.SortParallel)

	// Write results to JSON file with absolute path
	resultsJSON, _ := json.MarshalIndent(results, "", "  ")
	err = ioutil.WriteFile(filepath.Join(logsPath, "go_results.json"), resultsJSON, 0644)
	if err != nil {
		fmt.Printf("Error writing results to %s: %v\n", filepath.Join(logsPath, "go_results.json"), err)
		// Fallback to current directory if that fails
		err = ioutil.WriteFile("go_results.json", resultsJSON, 0644)
		if err != nil {
			fmt.Printf("Fallback error writing results to current directory: %v\n", err)
		} else {
			fmt.Println("Results written to current directory as go_results.json")
		}
	} else {
		fmt.Printf("Results written to %s\n", filepath.Join(logsPath, "go_results.json"))
	}
}