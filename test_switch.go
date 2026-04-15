package main

import "fmt"

func calcular() int {
    return 42
}

func main() {
    switch x := calcular(); x {
    case 42:
        fmt.Println("La respuesta a todo")
    default:
        fmt.Println("Valor incorrecto")
    }
    // fmt.Println(x) // Esto debería dar un ERROR SEMÁNTICO (x no definida)
}

