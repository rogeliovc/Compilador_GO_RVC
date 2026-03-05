from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo

class AutomataSemantico:
    def __init__(self):
        self.estado = 'inicio'
        self.prohibidos = {'$', '#', '(', '@'}
        
        # NUEVA TABLA DE SÍMBOLOS (contiene tipos y palabras reservadas)
        self.tabla_simbolos = TablaSimbolos()
        
        # MANTENER COMPATIBILIDAD con código existente
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
    
    def validar_funcion(self, tokens):
        if len(tokens) < 5:
            return False, "Declaración de función incompleta", None
        
        tipo_retorno = None
        nombre_func = None
        tiene_parentesis = False
        tiene_llave = False
        
        i = 0
        while i < len(tokens):
            tipo, valor = tokens[i]
            if tipo == "TKN ID" and not tipo_retorno and self.tabla_simbolos.es_tipo_dato(valor):
                tipo_retorno = valor
            elif tipo == "TKN ID" and valor.lower() in ["function", "func"] and not nombre_func:
                if i + 1 < len(tokens) and tokens[i + 1][0] == "TKN ID":
                    nombre_func = tokens[i + 1][1]
                    i += 1
            elif tipo == "TKN PAREN_A":
                tiene_parentesis = True
            elif tipo == "TKN PAREN_C" and tiene_parentesis:
                tiene_parentesis = True
            elif tipo == "TKN LLAVE_A":
                tiene_llave = True
            i += 1
        
        if all([tipo_retorno, nombre_func, tiene_parentesis, tiene_llave]):
            if self.tabla_simbolos.agregar_funcion(nombre_func, tipo_retorno, [], 0):
                return True, f"Función {nombre_func}: {tipo_retorno} registrada", None
            else:
                return False, f"ERROR: Función {nombre_func} ya existe", None
        
        return False, "Patrón de función no válido", None
    
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
    
    def limpiar_variables(self):
        self.variables_encontradas.clear()
        self.tabla_simbolos = TablaSimbolos()