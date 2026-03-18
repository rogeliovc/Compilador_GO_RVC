package main

import "fmt"

func main() {
    var miVariable int = 10
    var miPuntero *int = &miVariable

    fmt.Println("Valor de miVariable:", miVariable)
    fmt.Println("Valor de miPuntero (dirección de memoria):", miPuntero)
    fmt.Println("Valor apuntado por miPuntero:", *miPuntero)
}
