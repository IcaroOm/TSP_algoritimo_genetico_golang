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

func randomRoute(numCities int) Route {
	path := make([]int, numCities)
	for i := 0; i < numCities; i++ {
		path[i] = i
	}
	rand.Shuffle(len(path), func(i, j int) {
		path[i], path[j] = path[j], path[i]
	})
	return Route{path: path}
}

func calculateDistance(route Route, dm DistanceMatrix) float64 {
	total := 0.0
	for i := 0; i < len(route.path); i++ {
		j := (i + 1) % len(route.path)
		total += dm.Distance(route.path[i], route.path[j])
	}
	return total
}

func generateNeighbor(current Route) Route {
	neighbor := Route{
		path: make([]int, len(current.path)),
	}
	copy(neighbor.path, current.path)

	a := rand.Intn(len(neighbor.path))
	b := rand.Intn(len(neighbor.path))
	if a > b {
		a, b = b, a
	}

	for i := 0; i < (b-a+1)/2; i++ {
		neighbor.path[a+i], neighbor.path[b-i] = neighbor.path[b-i], neighbor.path[a+i]
	}

	return neighbor
}

func simulatedAnnealing(dm DistanceMatrix, initialTemp, coolingRate float64, iterations int) Route {
	current := randomRoute(len(dm))
	current.distance = calculateDistance(current, dm)

	best := current
	temp := initialTemp

	for i := 0; i < iterations; i++ {
		neighbor := generateNeighbor(current)
		neighbor.distance = calculateDistance(neighbor, dm)

		delta := neighbor.distance - current.distance

		if delta < 0 || math.Exp(-delta/temp) > rand.Float64() {
			current = neighbor
			if current.distance < best.distance {
				best = current
			}
		}

		temp *= coolingRate

		if i%1000 == 0 {
			fmt.Printf("Iteration %d: Temp=%.2f Best=%.2f Current=%.2f\n",
				i, temp, best.distance, current.distance)
		}
	}

	return best
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
			if len(parts) < 2 {
				return nil, fmt.Errorf("invalid DIMENSION line")
			}
			dimStr := strings.TrimSpace(parts[1])
			dimension, err = strconv.Atoi(dimStr)
			if err != nil {
				return nil, fmt.Errorf("invalid dimension: %v", err)
			}
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

			idx, err := strconv.Atoi(parts[0])
			if err != nil || idx < 1 || idx > dimension {
				continue
			}

			x, err1 := strconv.ParseFloat(parts[1], 64)
			y, err2 := strconv.ParseFloat(parts[2], 64)
			if err1 == nil && err2 == nil {
				points[idx-1] = Point{x: x, y: y}
			}
		}
	}

	for i, p := range points {
		if p.x == 0 && p.y == 0 {
			return nil, fmt.Errorf("missing coordinates for city %d", i+1)
		}
	}

	return points, nil
}

func main() {
	startTime := time.Now()
	rand.Seed(time.Now().UnixNano())

	var (
		inputFile    = flag.String("input", "", "Input file in TSPLIB format")
		initialTemp  = flag.Float64("temp", 100000.0, "Initial temperature")
		coolingRate  = flag.Float64("cooling", 0.9999, "Cooling rate")
		iterations   = flag.Int("iters", 500000, "Number of iterations")
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
		fmt.Printf("Loaded %d cities from %s\n", len(points), *inputFile)
	default:
		fmt.Println("No cities specified. Use -input or -random")
		return
	}

	dm := createDistanceMatrix(points)
	
	fmt.Println("Running simulated annealing...")
	best := simulatedAnnealing(dm, *initialTemp, *coolingRate, *iterations)

	fmt.Printf("\nBest route distance: %.2f\n", best.distance)
	fmt.Printf("Execution time: %s\n", time.Since(startTime))
}
