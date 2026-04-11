package main

// Prueba de estructuras de control (if, else, switch, for)
func main() {
    x := 10

    // Condicionales simples y compuestos
    if x > 5 {
        x = x - 1
    } else if x == 5 {
        x = 0
    } else {
        x = x + 1
    }

    // Estructura Switch / Case
    switch x {
    case 1:
        x = 10
    case 2:
        x = 20
    default:
        x = 0
    }

    // Ciclo For tradicional (inicialización; condición; post-operación)
    for i := 0; i < 10; i++ {
        x = x + i
    }

    // Ciclo For como "While" (solo condición)
    for x > 0 {
        x--
    }

    // Ciclo infinito (break es necesario internamente)
    for {
        x++
        if x > 100 {
            break
        }
    }
}
