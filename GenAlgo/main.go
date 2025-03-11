package main

import (
	"bufio"
	"container/list"
	"flag"
	"fmt"
	"math"
	"math/rand"
	"os"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

type Point struct {
	x, y float64
}

type Route struct {
	path     []int
	distance float64
}

type DistanceMatrix [][]float64

func (dm DistanceMatrix) Distance(i, j int) float64 {
	return dm[i][j]
}

type LRUCache struct {
	capacity int
	cache    map[string]*list.Element
	list     *list.List
	mutex    sync.Mutex
}

type cacheEntry struct {
	key   string
	value float64
}

func NewLRUCache(capacity int) *LRUCache {
	return &LRUCache{
		capacity: capacity,
		cache:    make(map[string]*list.Element),
		list:     list.New(),
	}
}

func (lc *LRUCache) Get(key string) (float64, bool) {
	lc.mutex.Lock()
	defer lc.mutex.Unlock()

	if elem, exists := lc.cache[key]; exists {
		lc.list.MoveToFront(elem)
		return elem.Value.(*cacheEntry).value, true
	}
	return 0, false
}

func (lc *LRUCache) Put(key string, value float64) {
	lc.mutex.Lock()
	defer lc.mutex.Unlock()

	if elem, exists := lc.cache[key]; exists {
		lc.list.MoveToFront(elem)
		elem.Value.(*cacheEntry).value = value
		return
	}

	if lc.list.Len() >= lc.capacity {
		oldest := lc.list.Back()
		delete(lc.cache, oldest.Value.(*cacheEntry).key)
		lc.list.Remove(oldest)
	}

	elem := lc.list.PushFront(&cacheEntry{key, value})
	lc.cache[key] = elem
}

func createDistanceMatrix(points []Point) DistanceMatrix {
	n := len(points)
	matrix := make(DistanceMatrix, n)
	for i := range matrix {
		matrix[i] = make([]float64, n)
		for j := range matrix[i] {
			matrix[i][j] = math.Hypot(points[i].x-points[j].x, points[i].y-points[j].y)
		}
	}
	return matrix
}

func normalizePath(path []int) []int {
	if len(path) == 0 {
		return path
	}
	minIdx := 0
	minVal := path[0]
	for i, v := range path {
		if v < minVal {
			minVal = v
			minIdx = i
		}
	}
	return append(path[minIdx:], path[:minIdx]...)
}

func getKey(path []int) string {
	normalized := normalizePath(path)
	var builder strings.Builder
	for i, city := range normalized {
		if i > 0 {
			builder.WriteByte(',')
		}
		builder.WriteString(strconv.Itoa(city))
	}
	return builder.String()
}

func cachedCrossover(parent1, parent2 Route, cache *LRUCache) (Route, Route) {
	maxAttempts := 15
	for attempt := 0; attempt < maxAttempts; attempt++ {
		child1, child2 := crossover(parent1, parent2)
		key1 := getKey(child1.path)
		key2 := getKey(child2.path)

		if _, exists1 := cache.Get(key1); !exists1 {
			if _, exists2 := cache.Get(key2); !exists2 {
				return child1, child2
			}
		}
	}
	return crossover(parent1, parent2)
}

func cachedMutate(route Route, mutationRate float64, cache *LRUCache) Route {
	maxAttempts := 8
	originalRate := mutationRate
	for attempt := 0; attempt < maxAttempts; attempt++ {
		mutated := mutate(route, mutationRate)
		if _, exists := cache.Get(getKey(mutated.path)); !exists {
			return mutated
		}
		mutationRate *= 1.5
	}
	return mutate(route, originalRate)
}

func evaluatePopulation(population []Route, dm DistanceMatrix, cache *LRUCache) {
	var wg sync.WaitGroup
	workers := runtime.NumCPU()
	jobs := make(chan int, len(population))

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range jobs {
				key := getKey(population[i].path)
				if dist, found := cache.Get(key); found {
					population[i].distance = dist
				} else {
					population[i].distance = calculateDistance(population[i], dm)
					cache.Put(key, population[i].distance)
				}
			}
		}()
	}

	for i := range population {
		jobs <- i
	}
	close(jobs)
	wg.Wait()
}

func calculateDistance(route Route, dm DistanceMatrix) float64 {
	total := 0.0
	prev := 0
	for _, city := range route.path {
		total += dm.Distance(prev, city)
		prev = city
	}
	return total + dm.Distance(prev, 0)
}

func randomRoute(numCities int) Route {
	path := make([]int, numCities-1)
	for i := 1; i < numCities; i++ {
		path[i-1] = i
	}
	rand.Shuffle(len(path), func(i, j int) {
		path[i], path[j] = path[j], path[i]
	})
	return Route{path: path}
}

func initializePopulation(popSize, numCities int) []Route {
	population := make([]Route, popSize)
	for i := 0; i < popSize; i++ {
		population[i] = randomRoute(numCities)
	}
	return population
}

func tournamentSelection(population []Route, tournamentSize int) Route {
	best := population[rand.Intn(len(population))]
	for i := 1; i < tournamentSize; i++ {
		competitor := population[rand.Intn(len(population))]
		if competitor.distance < best.distance {
			best = competitor
		}
	}
	return best
}

func crossover(parent1, parent2 Route) (Route, Route) {
	size := len(parent1.path)
	a, b := rand.Intn(size), rand.Intn(size)
	if a > b {
		a, b = b, a
	}

	child1Path := make([]int, size)
	child2Path := make([]int, size)
	used1, used2 := make(map[int]bool), make(map[int]bool)

	for i := a; i <= b; i++ {
		child1Path[i] = parent1.path[i]
		used1[parent1.path[i]] = true
		child2Path[i] = parent2.path[i]
		used2[parent2.path[i]] = true
	}

	fillChild := func(child []int, parent Route, used map[int]bool) {
		pos := (b + 1) % size
		for _, city := range parent.path {
			if !used[city] {
				child[pos] = city
				pos = (pos + 1) % size
			}
		}
	}

	fillChild(child1Path, parent2, used1)
	fillChild(child2Path, parent1, used2)

	return Route{path: child1Path}, Route{path: child2Path}
}

func mutate(route Route, mutationRate float64) Route {
	if rand.Float64() >= mutationRate {
		return route
	}
	size := len(route.path)
	swaps := rand.Intn(3) + 1
	for i := 0; i < swaps; i++ {
		a, b := rand.Intn(size), rand.Intn(size)
		route.path[a], route.path[b] = route.path[b], route.path[a]
	}
	return route
}

func readPointsFromFile(filename string) ([]Point, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var dimension int
	var points []Point
	inCoordSection := false

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		if strings.HasPrefix(line, "DIMENSION") {
			parts := strings.Split(line, ":")
			if len(parts) < 2 {
				parts = strings.Split(line, " ")
			}
			dimStr := strings.TrimSpace(parts[1])
			dimension, _ = strconv.Atoi(dimStr)
			points = make([]Point, dimension)
		}

		if strings.HasPrefix(line, "NODE_COORD_SECTION") {
			inCoordSection = true
			continue
		}

		if inCoordSection && strings.HasPrefix(line, "EOF") {
			break
		}

		if inCoordSection {
			parts := strings.Fields(line)
			if len(parts) < 3 {
				continue
			}
			idx, _ := strconv.Atoi(parts[0])
			x, _ := strconv.ParseFloat(parts[1], 64)
			y, _ := strconv.ParseFloat(parts[2], 64)
			if idx >= 1 && idx <= dimension {
				points[idx-1] = Point{x, y}
			}
		}
	}

	return points, nil
}

func main() {
	startTime := time.Now()
	rand.Seed(time.Now().UnixNano())

	var (
		inputFile     = flag.String("input", "", "Input file with city coordinates")
		popSize       = flag.Int("pop", 1000, "Population size")
		generations   = flag.Int("gens", 2000, "Number of generations")
		tournament    = flag.Int("tournament", 10, "Tournament size")
		mutationRate  = flag.Float64("mut", 0.1, "Mutation rate")
		eliteSize     = flag.Int("elite", 10, "Elite population size")
		cacheSize     = flag.Int("cache", 10000, "LRU cache size")
	)
	flag.Parse()

	var points []Point
	var err error

	switch {
	case *inputFile != "":
		points, err = readPointsFromFile(*inputFile)
		if err != nil {
			fmt.Println("Error reading file:", err)
			return
		}
	default:
		fmt.Println("No cities specified. Use -input or -random")
		return
	}

	numCities := len(points)
	dm := createDistanceMatrix(points)
	cache := NewLRUCache(*cacheSize)
	population := initializePopulation(*popSize, numCities)
	evaluatePopulation(population, dm, cache)

	best := population[0]
	updateBest := func(r Route) {
		if r.distance < best.distance {
			best = r
		}
	}

	for gen := 0; gen < *generations; gen++ {
		sort.Slice(population, func(i, j int) bool {
			return population[i].distance < population[j].distance
		})
		updateBest(population[0])

		newPopulation := make([]Route, 0, *popSize)
		if *eliteSize > 0 {
			newPopulation = append(newPopulation, population[:*eliteSize]...)
		}

		for len(newPopulation) < *popSize {
			parent1 := tournamentSelection(population, *tournament)
			parent2 := tournamentSelection(population, *tournament)
			child1, child2 := cachedCrossover(parent1, parent2, cache)
			child1 = cachedMutate(child1, *mutationRate, cache)
			child2 = cachedMutate(child2, *mutationRate, cache)
			newPopulation = append(newPopulation, child1, child2)
		}

		newPopulation = newPopulation[:*popSize]
		evaluatePopulation(newPopulation, dm, cache)
		population = newPopulation

		if gen%50 == 0 || gen == *generations-1 {
			fmt.Printf("Gen %d: Best = %.2f\n", gen, best.distance)
		}
	}

	fmt.Printf("\nBest route distance: %.2f\n", best.distance)
	fmt.Printf("Execution time: %s\n", time.Since(startTime))
}