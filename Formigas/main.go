package main

import (
	"bufio"
	"flag"
	"fmt"
	"math"
	"math/rand"
	"os"
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

type ACOParams struct {
	numAnts    int
	alpha      float64
	beta       float64
	rho        float64
	q          float64
	iterations int
	eliteAnts  int
}

type PheromoneMatrix [][]float64

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

func initializePheromones(size int, initial float64) PheromoneMatrix {
	pm := make(PheromoneMatrix, size)
	for i := range pm {
		pm[i] = make([]float64, size)
		for j := range pm[i] {
			if i != j {
				pm[i][j] = initial
			}
		}
	}
	return pm
}

func calculateRouteDistance(path []int, dm DistanceMatrix) float64 {
	distance := 0.0
	for i := 0; i < len(path); i++ {
		j := (i + 1) % len(path)
		distance += dm.Distance(path[i], path[j])
	}
	return distance
}

func selectNextCity(current int, visited []bool, dm DistanceMatrix, pm PheromoneMatrix, params ACOParams) int {
	var probabilities []float64
	var cities []int
	total := 0.0

	for city := 0; city < len(dm); city++ {
		if !visited[city] && city != current {
			ph := pm[current][city]
			heuristic := 1.0 / dm.Distance(current, city)
			prob := math.Pow(ph, params.alpha) * math.Pow(heuristic, params.beta)
			probabilities = append(probabilities, prob)
			cities = append(cities, city)
			total += prob
		}
	}

	if total == 0 {
		return cities[rand.Intn(len(cities))]
	}

	r := rand.Float64() * total
	cumulative := 0.0
	for i, p := range probabilities {
		cumulative += p
		if r <= cumulative {
			return cities[i]
		}
	}
	return cities[len(cities)-1]
}

func constructAntRoute(dm DistanceMatrix, pm PheromoneMatrix, params ACOParams) Route {
	size := len(dm)
	path := make([]int, size)
	visited := make([]bool, size)

	start := rand.Intn(size)
	path[0] = start
	visited[start] = true

	for i := 1; i < size; i++ {
		current := path[i-1]
		next := selectNextCity(current, visited, dm, pm, params)
		path[i] = next
		visited[next] = true
	}

	return Route{
		path:     path,
		distance: calculateRouteDistance(path, dm),
	}
}

func sortRoutes(ants []Route) {
    if len(ants) < 2 {
        return
    }

    left, right := 0, len(ants)-1
    pivot := ants[len(ants)/2].distance

    for left <= right {
        for ants[left].distance < pivot {
            left++
        }
        for ants[right].distance > pivot {
            right--
        }
        if left <= right {
            ants[left], ants[right] = ants[right], ants[left]
            left++
            right--
        }
    }

    if right > 0 {
        sortRoutes(ants[:right+1])
    }
    if left < len(ants) {
        sortRoutes(ants[left:])
    }
}

func updatePheromones(pm PheromoneMatrix, ants []Route, params ACOParams) {
    for i := range pm {
        for j := range pm[i] {
            pm[i][j] *= (1.0 - params.rho)
        }
    }

    sortRoutes(ants)

    eliteCount := params.eliteAnts
    if eliteCount > len(ants) {
        eliteCount = len(ants)
    }
    
    for _, ant := range ants[:eliteCount] {
        deposit := params.q / ant.distance
        for i := 0; i < len(ant.path); i++ {
            from := ant.path[i]
            to := ant.path[(i+1)%len(ant.path)]
            pm[from][to] += deposit
            pm[to][from] += deposit
        }
    }
}

func aco(dm DistanceMatrix, params ACOParams) Route {
	pm := initializePheromones(len(dm), 1.0)
	bestRoute := Route{distance: math.MaxFloat64}

	for iter := 0; iter < params.iterations; iter++ {
		var wg sync.WaitGroup
		ants := make([]Route, params.numAnts)

		for i := 0; i < params.numAnts; i++ {
			wg.Add(1)
			go func(idx int) {
				defer wg.Done()
				ants[idx] = constructAntRoute(dm, pm, params)
			}(i)
		}
		wg.Wait()

		for _, ant := range ants {
			if ant.distance < bestRoute.distance {
				bestRoute = ant
			}
		}

		updatePheromones(pm, ants, params)

		if iter%10 == 0 {
			fmt.Printf("Iteration %d: Best = %.2f\n", iter, bestRoute.distance)
		}
	}

	return bestRoute
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
		inputFile   = flag.String("input", "", "TSPLIB file")
		numAnts     = flag.Int("ants", 50, "Number of ants")
		alpha       = flag.Float64("alpha", 1.0, "Pheromone exponent")
		beta        = flag.Float64("beta", 2.0, "Heuristic exponent")
		rho         = flag.Float64("rho", 0.1, "Evaporation rate")
		q           = flag.Float64("q", 100.0, "Pheromone quantity")
		iterations  = flag.Int("iters", 100, "ACO iterations")
		eliteAnts   = flag.Int("elite", 50, "Number of elite ants")
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
		fmt.Println("No input specified")
		return
	}

	dm := createDistanceMatrix(points)
	params := ACOParams{
		numAnts:    *numAnts,
		alpha:      *alpha,
		beta:       *beta,
		rho:        *rho,
		q:          *q,
		iterations: *iterations,
		eliteAnts:  *eliteAnts,
	}

	fmt.Println("Running ACO...")
	best := aco(dm, params)

	fmt.Printf("\nBest route distance: %.2f\n", best.distance)
	fmt.Printf("Execution time: %s\n", time.Since(startTime))
}
