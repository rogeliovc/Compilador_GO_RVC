from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo
from utils import es_identificador_valido, es_tipo_dato

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
        
        if any(t[1].lower() == 'if' for t in tokens):
            idx_if = next(i for i, t in enumerate(tokens) if t[1].lower() == 'if')
            
            if idx_if == 0 or (idx_if > 0 and tokens[idx_if-1][1].lower() == 'else'):
                primer_token_expr = idx_if + 1
                if len(tokens) > primer_token_expr and tokens[primer_token_expr][0] == 'TKN PAREN_A':
                    primer_token_expr += 1
                
                if len(tokens) > primer_token_expr and tokens[primer_token_expr][0] in ['TKN EQ', 'TKN NEQ', 'TKN LT', 'TKN GT', 'TKN LTE', 'TKN GTE']:
                    errores.append(f"Línea {linea}: SEMÁNTICA - Orden incorrecto, operador antes de variable en 'if'")
            else:
                tiene_comillas = any('COMILLA' in t[0] for t in tokens)
                if not tiene_comillas:
                    errores.append(f"Línea {linea}: SEMÁNTICA - El bloque 'if' presenta un orden incorrecto")
        
        if any(t[1].lower() == 'for' for t in tokens):
            if tokens[0][1].lower() == 'for':
                semicolons = sum(1 for t in tokens if t[1] == ';')
                if semicolons not in [0, 2]:
                    errores.append(f"Línea {linea}: SEMÁNTICA - Bucle 'for' con formato incorrecto (solo 0 o 2 puntos y comas permitidos)")
            else:
                tiene_comillas = any('COMILLA' in t[0] for t in tokens)
                if not tiene_comillas:
                    errores.append(f"Línea {linea}: SEMÁNTICA - El bloque 'for' presenta un orden incorrecto")
        
        if tokens[0][1] == 'var':
            if len(tokens) < 3:
                errores.append(f"Línea {linea}: Declaración var incompleta")
                return errores
            
            if len(tokens) >= 4:
                nombre = tokens[1][1]
                tipo = tokens[2][1] if len(tokens) > 2 else ""
                
                if self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    if simbolo_existente.tipo_dato != tipo:
                        errores.append(f"Línea {linea}: AMBIGÜEDAD - Variable '{nombre}' declarada previamente como '{simbolo_existente.tipo_dato}' and ahora como '{tipo}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, tipo, linea)

                for j in range(3, len(tokens)):
                    if tokens[j][0] == 'TKN ASIGN' or tokens[j][0] == 'TKN WALRUS':
                        rhs_tokens = tokens[j+1:]
                        for tk in rhs_tokens:
                            if tk[0] == 'TKN ID':
                                val = tk[1]
                                if '.' in val:
                                    base = val.split('.')[0]
                                    if not self.tabla_simbolos.existe_simbolo(base):
                                        errores.append(f"Línea {linea}: SEMÁNTICA - Base indefinida '{base}' al intentar acceder a atributo en '{val}'")
                                elif not self.tabla_simbolos.existe_simbolo(val) and not es_tipo_dato(val):
                                    pass
        
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