1. Casos de Éxito (Deben compilar sin errores)
Estas son las formas idiomáticas y legales de escribir un ciclo for en Go. Tu compilador debe aceptarlas todas y generar el árbol correctamente.

For clásico de 3 componentes (Cláusula For):
En Go no se usan paréntesis alrededor de las condiciones, pero las llaves {} son obligatorias.

Go
for i := 0; i < 10; i++ {
    suma += i
}
For como "while" (Condición única):
Go no tiene la palabra while. Se usa for con una sola condición booleana.

Go
contador := 0
for contador < 5 {
    contador++
}
For infinito:
La forma más pura, sin componentes. Se detiene internamente con break o return.

Go
for {
    fmt.Println("Ejecutando...")
    break
}
For con range (Iterador):
Esta es una estructura nativa de Go para recorrer arreglos, slices o mapas.

Go
numeros := []int{1, 2, 3}
for indice, valor := range numeros {
    fmt.Println(indice, valor)
}
Asignación múltiple en la inicialización y post-ejecución:
Go no usa el operador coma , para expresiones separadas como en C, sino que permite asignación paralela.

Go
for i, j := 0, 10; i < j; i, j = i+1, j-1 {
    // Lógica
}
2. Casos de Falla (Deben lanzar ERROR)
Aquí es donde un buen compilador de Go se defiende. Estos casos son comunes en programadores que vienen de C, Java o C#, pero son errores de sintaxis o semántica en Go.

Uso de paréntesis estilo C (Error de Sintaxis):
Go rechaza explícitamente envolver la declaración en paréntesis.

Go
for (i := 0; i < 10; i++) { // ERROR: Paréntesis no permitidos aquí
    suma++
}
Omisión de las llaves (Error de Sintaxis):
A diferencia de C o Java, en Go siempre debes poner las llaves { }, incluso si el cuerpo del bucle es de una sola línea.

Go
for i := 0; i < 10; i++ // ERROR: Falta abrir la llave '{'
    fmt.Println(i)
Condición no booleana (Error Semántico):
En Go, no existe el concepto de "truthy" o "falsy" como en JavaScript o C (donde 1 es verdadero). La condición central tiene que evaluar a tipo bool.

Go
for i := 0; 5; i++ { // ERROR: '5' no es de tipo booleano
    fmt.Println("hola")
}
Uso de pre-incremento (Error de Sintaxis):
Go no tiene operador de pre-incremento (++i). El operador ++ solo puede usarse como sufijo (post-incremento) y es una declaración, no una expresión.

Go
for i := 0; i < 10; ++i { // ERROR: sintaxis inválida, debe ser i++
    suma++
}
Fuga de alcance o scope (Error Semántico):
Si declaras una variable con := dentro de la inicialización del for, esta muere cuando el bucle termina. Si intentas usarla afuera, tu tabla de símbolos debe reportar que no existe.

Go
for i := 0; i < 5; i++ {
    suma += i
}
fmt.Println(i) // ERROR: 'i' no está definida en este ámbito (undefined)