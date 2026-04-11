from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo
from utils import es_identificador_valido, es_tipo_dato

class AutomataSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.variables_encontradas = set()
        
        # Estado para manejar bloques de constantes
        self.en_bloque_const = False 
        
        # Estado para manejar bloques switch y sus casos
        self.en_bloque_switch = False
        self.casos_switch_actual = set()

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
                
                if not es_tipo_dato(tipo) and not self.tabla_simbolos.existe_simbolo(tipo) and tipo != "":
                    errores.append(f"Línea {linea}: SEMÁNTICA - Tipo de dato no reconocido '{tipo}' para la variable '{nombre}'")
                elif self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    if simbolo_existente.tipo_dato != tipo:
                        errores.append(f"Línea {linea}: AMBIGÜEDAD - Variable '{nombre}' declarada previamente como '{simbolo_existente.tipo_dato}' y ahora como '{tipo}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, tipo, linea, es_declaracion_corta=False)

        # Manejar bloques de constantes: const ( Min = 1; Max = 100 )
        if tokens[0][1] == 'const' and len(tokens) > 1 and tokens[1][0] == 'TKN PAREN_A':
            # Inicio de bloque const
            self.en_bloque_const = True
            return errores  # No hay error en la apertura del bloque
        
        elif tokens[0][1] == 'const':
            if len(tokens) < 3:
                errores.append(f"Línea {linea}: Declaración const incompleta")
                return errores
            
            # const PI = 3.14159
            if len(tokens) >= 4:
                nombre = tokens[1][1]
                # Las constantes en Go pueden inferir el tipo del valor
                # Por ahora, registramos como tipo "constante"
                
                if self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    errores.append(f"Línea {linea}: AMBIGÜEDAD - Constante '{nombre}' ya declarada previamente como '{simbolo_existente.tipo_dato}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, "constante", linea, es_declaracion_corta=False)
        
        # Si estamos dentro de un bloque const y encontramos el cierre
        elif self.en_bloque_const and any(t[0] == 'TKN PAREN_C' for t in tokens):
            self.en_bloque_const = False
            return errores
        
        # Si estamos dentro de un bloque const, manejar declaraciones internas
        elif self.en_bloque_const and len(tokens) >= 2 and any(t[1] == '=' for t in tokens):
            # Min = 1 o Max = 100 dentro de bloque const
            pos_igual = next(i for i, t in enumerate(tokens) if t[1] == '=')
            if pos_igual > 0:
                nombre = tokens[pos_igual - 1][1]
                valor = tokens[pos_igual + 1][1] if pos_igual + 1 < len(tokens) else ""
                
                # Si no hay valor, podría ser una constante con valor implícito (iota)
                if self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    errores.append(f"Línea {linea}: AMBIGÜEDAD - Constante '{nombre}' ya declarada previamente como '{simbolo_existente.tipo_dato}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, "constante", linea, es_declaracion_corta=False)
            else:
                errores.append(f"Línea {linea}: Declaración de constante inválida")

        # Manejar bloques switch para detectar casos duplicados
        if any(t[1].lower() == 'switch' for t in tokens):
            self.en_bloque_switch = True
            self.casos_switch_actual = set()
            
        elif self.en_bloque_switch and any(t[1].lower() == 'case' for t in tokens):
            idx_case = next(i for i, t in enumerate(tokens) if t[1].lower() == 'case')
            valor_case = ""
            for t in tokens[idx_case+1:]:
                if t[1] in [':', '{']:
                    break
                valor_case += t[1] + " "
            
            valor_case = valor_case.strip()
            
            if valor_case in self.casos_switch_actual:
                errores.append(f"Línea {linea}: SEMÁNTICA - Caso duplicado '{valor_case}' en el bloque switch")
            elif valor_case:
                self.casos_switch_actual.add(valor_case)
        
        elif any((t[1] == ':=') for t in tokens):
            pos = next((i for i, t in enumerate(tokens) if (t[1] == ':=')), -1)
            if pos == 0 or pos >= len(tokens) - 1:
                errores.append(f"Línea {linea}: Declaración corta inválida")
            else:
                nombre = tokens[pos-1][1]
                if es_identificador_valido(nombre):
                    # En Go, := crea una nueva variable (declaración corta)
                    # Solo es error si ya existe y estamos en el mismo ámbito
                    if self.tabla_simbolos.existe_simbolo(nombre):
                        # Verificar si es realmente una redeclaración en el mismo ámbito
                        simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                        # En Go, := puede redeclarar variables solo en ámbitos diferentes
                        # Por ahora, permitimos la declaración corta sin marcar como duplicado
                        pass
                    # Registrar nueva variable con tipo inferido (declaración corta)
                    self.tabla_simbolos.agregar_variable(nombre, "inferido", linea, es_declaracion_corta=True)
        
        tiene_asignacion = any(t[0] == 'TKN ASIGN' for t in tokens)
        tiene_var = any(t[1] == 'var' for t in tokens)
        tiene_walrus = any(t[0] == 'TKN WALRUS' for t in tokens)

        if tiene_asignacion or tiene_walrus:
            asign_token = next(t[0] for t in tokens if t[0] in ['TKN ASIGN', 'TKN WALRUS'])
            pos_asign = next(i for i, t in enumerate(tokens) if t[0] == asign_token)
            
            if tiene_asignacion and not tiene_var:
                lhs_tokens = tokens[:pos_asign]
                for t in lhs_tokens:
                    if t[0] == 'TKN ID' and not self.tabla_simbolos.existe_simbolo(t[1]):
                        errores.append(f"Línea {linea}: SEMÁNTICA - Variable '{t[1]}' no declarada siendo asignada")
            
            rhs_tokens = tokens[pos_asign+1:]
            for t in rhs_tokens:
                if t[0] == 'TKN ID':
                    val = t[1]
                    if '.' in val:
                        base = val.split('.')[0]
                        if not self.tabla_simbolos.existe_simbolo(base):
                            errores.append(f"Línea {linea}: SEMÁNTICA - Base indefinida '{base}' al intentar acceder a atributo en '{val}'")
                    elif not self.tabla_simbolos.existe_simbolo(val) and not es_tipo_dato(val) and val not in ['true', 'false']:
                        errores.append(f"Línea {linea}: SEMÁNTICA - Símbolo '{val}' no declarado siendo usado en expresión")

        return errores
    
    def limpiar_variables(self):
        self.variables_encontradas.clear()
        self.tabla_simbolos = TablaSimbolos()