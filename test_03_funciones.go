package main

// Prueba de llamadas a funciones y diferentes firmas

// Función sencilla de un retorno
func sumar(a int, b int) int {
    return a + b
}

// Función sin retorno (void)
func imprimir_mensaje(mensaje string) {
    // fmt.Println(mensaje)
}

// Función con múltiples retornos (muy común en Go para manejo de errores)
func dividir(a float64, b float64) (float64, string) {
    if b == 0.0 {
        return 0.0, "Error: División por cero"
    }
    return a / b, "OK"
}

func main() {
    // Invocaciones
    resultado := sumar(5, 10)
    
    imprimir_mensaje("Calculando...")
    
    // Recibir múltiples retornos
    res, status := dividir(10.0, 2.0)
}
