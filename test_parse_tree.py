#!/usr/bin/env python3
# test_parse_tree.py

from lexer import AnalizadorLexico
from parser import AnalizadorSintactico

def test_parse_tree():
    # Expresión de ejemplo basada en la imagen
    expresion = "9*4/5-7+1*3+2"
    
    print("=== PRUEBA DE ÁRBOL DE PARSEO ===")
    print(f"Expresión: {expresion}")
    print()
    
    # Inicializar componentes
    lexer = AnalizadorLexico()
    parser = AnalizadorSintactico()
    
    # Procesar con lexer
    tokens = lexer.procesar(expresion)
    print("Tokens generados:")
    for tipo, valor in tokens:
        print(f"  <{tipo}, '{valor}'>")
    print()
    
    # Generar árbol de parseo
    arbol = parser.generar_arbol_parseo(tokens)
    print("Árbol de parseo:")
    print(arbol)
    
    # Probar con paréntesis
    expresion2 = "(9+4)*3-2"
    print(f"\n=== EXPRESIÓN CON PARÉNTESIS ===")
    print(f"Expresión: {expresion2}")
    
    tokens2 = lexer.procesar(expresion2)
    arbol2 = parser.generar_arbol_parseo(tokens2)
    print("Árbol de parseo:")
    print(arbol2)

if __name__ == "__main__":
    test_parse_tree()
