package main

import (
    "fmt"
    "math"
    "os"
)

// En Go no existen "clases", se usan Structs para definir estructuras de datos
type Persona struct {
    Nombre string
    Edad   int
    Activo bool
}

// Las "funciones miembro" o métodos se adjuntan a los structs usando "receptores"
func (p Persona) Saludar() string {
    return "Hola, me llamo " + p.Nombre
}

func main() {
    // Instanciación tradicional
    var usuario1 Persona
    usuario1.Nombre = "Rogelio"
    usuario1.Edad = 25
    usuario1.Activo = true

    // Instanciación literal
    usuario2 := Persona{
        Nombre: "Ana", 
        Edad: 30, 
        Activo: false,
    }

    // Acceso a métodos y propiedades
    mensaje := usuario1.Saludar()
}
