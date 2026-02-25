# test_consola.py
from lexer import AnalizadorLexico
from parser import AnalizadorSintactico
from semantic import AutomataSemantico

if __name__ == "__main__":
    lex = AnalizadorLexico()
    sintactico = AnalizadorSintactico()
    semantico = AutomataSemantico()

    # 1. Tu prueba matemática
    expresion_matematica = "{[(4*3+2]/5}"
    print(f"--- PRUEBA 1: {expresion_matematica} ---")
    
    tokens_math = lex.procesar(expresion_matematica)
    print("Tokens:", tokens_math)
    
    if sintactico.procesar_tokens(tokens_math):
        print("Sintaxis: Los paréntesis, corchetes y llaves están balanceados.")
    else:
        print("Sintaxis: ERROR - Hay símbolos sin abrir o cerrar.")

    print("\n")

    # 2. Prueba Semántica (Variables)
    print("--- PRUEBA 2: Variables ---")
    print(semantico.registrar_y_validar_variable("int", "edad"))
    # Intentamos registrar 'edad' otra vez (Tu prueba de ambigüedad)
    print(semantico.registrar_y_validar_variable("double", "edad"))