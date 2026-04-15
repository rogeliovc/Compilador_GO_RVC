package main

import "fmt"

func main() {
    // CASOS DE PRUEBA PARA ESTRUCTURA FOR    
    
    // ===== CASOS VÁLIDOS (deben compilar sin errores) =====
    
    // For clásico de 3 componentes
    for i := 0; i != 10; i++ {
        suma := 0
        suma = i++
    }
    
    // For como while (condición única)
    contador := 0
    for contador < 5 {
        contador++
    }
    
    // For infinito
    for {
        break
    }
    
    // For con range
    indice := 0
    numeros := []int{1, 2, 3}
    for indice, valor := range numeros {
        fmt.Println(indice, valor)
    }
    
    // Asignación múltiple
    for i, j := 0, 10; i < j; i, j = i+1, j-1 {
        // Lógica
    }
    
}




