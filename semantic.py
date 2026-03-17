from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo

class AutomataSemantico:
    def __init__(self):
        self.estado = 'inicio'
        self.prohibidos = {'$', '#', '(', '@'}
        
        self.tabla_simbolos = TablaSimbolos()
        
        self.variables_encontradas = set() 

    def transicion(self, caracter):
        if self.estado == 'inicio':
            if caracter.isalpha() or caracter == '_':
                self.estado = 'valido'
            else:
                self.estado = 'invalido'
        elif self.estado == 'valido':
            if caracter.isalnum() or caracter in '_.:' and caracter not in self.prohibidos:
                self.estado = 'valido'
            else:
                self.estado = 'invalido'

    def validar_variable(self, nombre):
        self.estado = 'inicio'
        for caracter in nombre:
            self.transicion(caracter)
            if self.estado == 'invalido': return False
        return self.estado == 'valido'
    
    def get_descripcion_tipo(self, tipo):
        descripciones = {
            'int': 'tipo de dato entero corto',
            'double': 'tipo de dato entero largo',
            'str': 'tipo de dato cadena',
            'bool': 'tipo de dato booleano'
        }
        return descripciones.get(tipo.lower(), 'tipo de dato desconocido')
    
    def registrar_y_validar_variable(self, tipo_dato, variable):
        descripcion = self.get_descripcion_tipo(tipo_dato)
        
        if self.tabla_simbolos.existe_simbolo(variable):
            return f"{tipo_dato} {variable} // {descripcion}, ERROR: ambigüedad con variable existente"
        
        if self.tabla_simbolos.agregar_variable(variable, tipo_dato, 0):
            self.variables_encontradas.add(variable)
            return f"{tipo_dato} {variable} // {descripcion}, registrada correctamente"
        else:
            return f"{tipo_dato} {variable} // {descripcion}, ERROR: no se pudo registrar"
    
    def validar_declaracion(self, tokens):
        return self.tabla_simbolos.validar_patron_declaracion(tokens)
    
    def verificar_uso_variable(self, nombre_variable):
        simbolo = self.tabla_simbolos.buscar_simbolo(nombre_variable)
        if simbolo:
            if not simbolo.inicializada:
                return f"ADVERTENCIA: Variable '{nombre_variable}' no inicializada"
            return f"Variable '{nombre_variable}' válida"
        else:
            return f"ERROR: Variable '{nombre_variable}' no declarada"
    
    def obtener_info_variable(self, nombre):
        simbolo = self.tabla_simbolos.buscar_simbolo(nombre)
        if simbolo:
            return str(simbolo)
        return f"Variable '{nombre}' no encontrada"
    
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
                
                if not self._es_identificador_valido(nombre):
                    errores.append(f"Línea {linea}: Identificador inválido '{nombre}'")
                    return errores
                
                if self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    if simbolo_existente.tipo != tipo:
                        errores.append(f"Línea {linea}: AMBIGÜEDAD - Variable '{nombre}' declarada previamente como '{simbolo_existente.tipo}' y ahora como '{tipo}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, tipo, linea)
        
        elif any((t[1] == ':=') for t in tokens):
            pos = next((i for i, t in enumerate(tokens) if (t[1] == ':=')), -1)
            if pos == 0 or pos >= len(tokens) - 1:
                errores.append(f"Línea {linea}: Declaración corta inválida")
            else:
                nombre = tokens[pos-1][1]
                if self._es_identificador_valido(nombre):
                    if self.tabla_simbolos.existe_simbolo(nombre):
                        errores.append(f"Línea {linea}: VARIABLE DUPLICADA '{nombre}'")
                    else:
                        self.tabla_simbolos.agregar_variable(nombre, "inferido", linea)
        
        return errores
    
    def _es_identificador_valido(self, nombre):
        if not nombre:
            return False
        
        if nombre[0].isdigit():
            return False
        
        if not all(c.isalnum() or c == '_' for c in nombre):
            return False
        
        keywords_go = {'package', 'import', 'func', 'var', 'const', 'if', 'else', 'for', 'break', 'continue', 'return', 'struct', 'interface', 'type', 'map', 'range', 'chan', 'select', 'defer', 'go', 'int', 'string', 'float', 'bool', 'true', 'false', 'nil'}
        if nombre in keywords_go:
            return False
        
        return True
    
    def limpiar_variables(self):
        self.variables_encontradas.clear()
        self.tabla_simbolos = TablaSimbolos()