from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo
from utils import es_identificador_valido

class AutomataSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.variables_encontradas = set() 

    def validar_declaracion(self, tokens):
        return self.tabla_simbolos.validar_patron_declaracion(tokens)
    
    def imprimir_tabla_completa(self):
        self.tabla_simbolos.imprimir_tabla()
    
    def validar_declaracion_variable(self, tokens, linea):
        if not tokens:
            return []
        
        errores = []
        
        if tokens[0][1] == 'var':
            if len(tokens) < 3:
                errores.append(f"Línea {linea}: Declaración var incompleta")
                return errores
            
            if len(tokens) >= 4:
                nombre = tokens[1][1]
                tipo = tokens[2][1] if len(tokens) > 2 else ""
                
                if not es_identificador_valido(nombre):
                    errores.append(f"Línea {linea}: Identificador inválido '{nombre}'")
                    return errores
                
                if self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    if simbolo_existente.tipo_dato != tipo:
                        errores.append(f"Línea {linea}: AMBIGÜEDAD - Variable '{nombre}' declarada previamente como '{simbolo_existente.tipo_dato}' y ahora como '{tipo}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, tipo, linea)
        
        elif any((t[1] == ':=') for t in tokens):
            pos = next((i for i, t in enumerate(tokens) if (t[1] == ':=')), -1)
            if pos == 0 or pos >= len(tokens) - 1:
                errores.append(f"Línea {linea}: Declaración corta inválida")
            else:
                nombre = tokens[pos-1][1]
                if es_identificador_valido(nombre):
                    if self.tabla_simbolos.existe_simbolo(nombre):
                        errores.append(f"Línea {linea}: VARIABLE DUPLICADA '{nombre}'")
                    else:
                        self.tabla_simbolos.agregar_variable(nombre, "inferido", linea)
        
        return errores
    
    def limpiar_variables(self):
        self.variables_encontradas.clear()
        self.tabla_simbolos = TablaSimbolos()