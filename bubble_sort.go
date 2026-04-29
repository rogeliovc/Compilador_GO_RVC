package main
import "fmt"

func main() {
    var n int = 5
    var lista [5]int
    
    // Inicializar lista desordenada
    lista[0] = 50
    lista[1] = 10
    lista[2] = 40
    lista[3] = 20
    lista[4] = 30
    
    fmt.Println("Ordenando lista por Bubble Sort...")
    
    // Algoritmo Bubble Sort
    for i := 0; i < n-1; i++ {
        for j := 0; j < n-i-1; j++ {
            
            valActual := lista[j]
            valSiguiente := lista[j+1]
            
            if valActual > valSiguiente {
                // Intercambio (Swap)
                lista[j] = valSiguiente
                lista[j+1] = valActual
                fmt.Println("Intercambio realizado")
            }
        }
    }
    
    fmt.Println("Lista ordenada con éxito.")
}