package main

import "fmt"

// === CASOS DE PRUEBA COMPLETOS PARA SWITCH EN GO ===

func main() {
    // Test 1: Switch simple con strings y múltiples valores por case
    dia := "Martes"
    switch dia {
    case "Lunes", "Martes", "Miércoles", "Jueves", "Viernes":
        fmt.Println("Día laborable")
    case "Sábado", "Domingo":
        fmt.Println("Fin de semana")
    default:
        fmt.Println("Día no reconocido")
    }

    // Test 2: Switch con números enteros
    numero := 42
    switch numero {
    case 1, 2, 3:
        fmt.Println("Pequeño")
    case 42:
        fmt.Println("La respuesta")
    case 100:
        fmt.Println("Grande")
    default:
        fmt.Println("Otro número")
    }

    // Test 3: Switch con expresiones aritméticas
    x := 10
    y := 20
    switch x + y {
    case 30:
        fmt.Println("Suma correcta")
    case 40:
        fmt.Println("Suma incorrecta")
    default:
        fmt.Println("Valor inesperado")
    }

    // Test 4: Switch sin expresión (condicional)
    edad := 25
    switch {
    case edad < 18:
        fmt.Println("Menor de edad")
    case edad >= 18 && edad < 65:
        fmt.Println("Adulto")
    case edad >= 65:
        fmt.Println("Adulto mayor")
    default:
        fmt.Println("Edad no válida")
    }

    // for con && y ||
    posicion := 0
    limite := 5
    hayErrorSintactico := false

    fmt.Println("--- Iniciando ciclo con && ---")
    
    // Iterar mientras no lleguemos al límite Y no haya errores
    for posicion < limite && !hayErrorSintactico {
        fmt.Printf("Procesando elemento en posición: %d\n", posicion)
        
        posicion++

        // Simulamos que encontramos un error a la mitad
        if posicion == 3 {
            fmt.Println("¡Error encontrado! Deteniendo proceso...")
            hayErrorSintactico = true 
        }
    }
    
    fmt.Println("Ciclo && terminado.")
}

