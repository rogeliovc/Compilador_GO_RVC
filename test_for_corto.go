package main

import "fmt"

func main() {
    //For básico con una sola condición (estilo while)
    i := 0
    for i < 5 {
        fmt.Printf("Bucle básico: i = %d\n", i)
        i++
    }
    
    //For con inicialización, condición y post-incremento
    for j := 0; j < 3; j++ {
        fmt.Printf("For clásico: j = %d\n", j)
    }
    
    
    //For infinito
    count := 0
    for {
        fmt.Printf("For infinito: count = %d\n", count)
        count++
        if count >= 3 {
            break // Salir después de 3 iteraciones
        }
    }
    
    //For con continue
    for k := 0; k < 5; k++ {
        if k == 2 {
            continue // Saltar la iteración 2
        }
        fmt.Printf("For con continue: k = %d\n", k)
    }
    
    //For anidado
    for x := 0; x < 2; x++ {
        fmt.Printf("Nivel externo: x = %d\n", x)
        for y := 0; y < 2; y++ {
            fmt.Printf("  Nivel interno: y = %d\n", y)
        }
    }
    
    //For con declaración de variable sin inicialización
     z := 0
    for z = 0; z < 3; z++ {
        fmt.Printf("For con var externa: z = %d\n", z)
    }
    
    //For con condición compleja
    for w := 0; w < 10 && w % 2 == 0; w += 2 {
        fmt.Printf("For con condición compleja: w = %d\n", w)
    }
    
    //For con decremento
    for v := 10; v > 0; v-- {
        fmt.Printf("For con decremento: v = %d\n", v)
    }
    
    //For con asignación compuesta en post
    for u := 0; u < 3; u = u * 2 {
        fmt.Printf("For con asignación: u = %d\n", u)
    }
    
    fmt.Println("Todos los tests de for cortos completados")
}

