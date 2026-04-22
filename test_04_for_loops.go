package main
import "fmt"

func main() {
    fmt.Println("=== PRUEBAS DE CICLO FOR EN GO ===")

    // Variante 1: For clásico completo (init; cond; post)
    fmt.Println("\n1. For clásico:")
    for i := 0; i < 5; i++ {
        fmt.Println("Iteración clásica:", i)
    }

    // Variante 2: For como 'while' (solo condición)
    fmt.Println("\n2. For como while:")
    contador := 0
    for contador < 3 {
        fmt.Println("Iteración while:", contador)
        contador++
    }

    // Variante 3: For con init y cond, pero sin post
    fmt.Println("\n3. For sin post-condición:")
    for j := 0; j < 3; {
        fmt.Println("Iteración sin post:", j)
        j += 1
    }

    // Variante 4: For infinito con break
    fmt.Println("\n4. For infinito con break:")
    inf := 0
    for {
        if inf == 2 {
            fmt.Println("Rompiendo bucle infinito en:", inf)
            break
        }
        inf++
    }

    // Variante 5: For con continue y scope local
    fmt.Println("\n5. For con continue y scope anidado:")
    for k := 0; k < 4; k++ {
        if k == 1 {
            continue
        }
        // Demostrando scope seguro: 'temp' se recrea en cada iteración
        temp := k * 10
        fmt.Println("Iteración con continue, temp =", temp)
    }

    // Variante 6: For anidado (Testing scope robusto)
    fmt.Println("\n6. For anidados:")
    for x := 1; x <= 2; x++ {
        for y := 1; y <= 2; y++ {
            res := x * y
            fmt.Println("x * y =", res)
        }
    }

    /* 
    ========================================================
    CASOS DE ERROR PARA QUE PRUEBES (Descoméntalos uno a uno)
    ========================================================
    
    1. Error: Paréntesis alrededor de la condición (estilo C)
    for (i := 0; i < 10; i++) {
        fmt.Println(i)
    }

    2. Error: Usar : en lugar de := en el init
    for i: 0; i < 5; i++ {
        fmt.Println(i)
    }

    3. Error: Pre-incremento (no permitido en Go)
    for i := 0; i < 5; ++i {
        fmt.Println(i)
    }

    4. Error: Usar basura sintáctica extra en la condición
    for i := 0; i < 5 = 5; i++ {
        fmt.Println(i)
    }

    5. Error: Variable no definida en la condición
    for j := 0; noExisto < 5; j++ {
        fmt.Println(j)
    }
    */
}
