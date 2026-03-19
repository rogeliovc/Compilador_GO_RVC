package main

import "fmt"

func main() {
    // 1. Ciclo For Estándar (Contador)
    fmt.Println("--- For Estándar ---")
    for i := 0; i < 5; i++ {
        fmt.Printf("Iteración: %d\n", i)
    }

    // 2. Ciclo For como While (Condicional)
    fmt.Println("\n--- For tipo While ---")
    contador := 0
    for contador < 3 {
        fmt.Printf("Contador: %d\n", contador)
        contador++
    }

    // 3. Ciclo for range (Para recorrer Slices/Arrays)
    fmt.Println("\n--- For range ---")
    frutas := []string{"Manzana", "Banana", "Uva"}
    for indice, valor := range frutas {
        fmt.Printf("Índice: %d, Fruta: %s\n", indice, valor)
    }

    // 4. Ciclo Infinito con break
    fmt.Println("\n--- For Infinito con Break ---")
    i := 0
    for {
        fmt.Println("Ejecutando...")
        i++
        if i >= 2 {
            break // Detiene el ciclo
        }
    }
}




