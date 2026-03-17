package main

func main() {
    // Prueba de ambigüedad - Proyecto 2
    var x int = 5;
    var x string = "hola";  // AMBIGÜEDAD: mismo nombre, diferente tipo
    var 2q bool = false;     // ERROR: identificador inválido
    y = 0;                 // WARNING: variable no declarada
    var z int = 4;
    x = x + z;
    print(x)                // WARNING: falta punto y coma
}
