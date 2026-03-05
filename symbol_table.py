from typing import Dict, List, Optional, Any
from enum import Enum

class TipoSimbolo(Enum):
    VARIABLE = "variable"
    FUNCION = "funcion"
    PARAMETRO = "parametro"
    TIPO_DATO = "tipo_dato"
    PALABRA_RESERVADA = "palabra_reservada"

class Ambito(Enum):
    GLOBAL = "global"
    LOCAL = "local"
    PARAMETRO = "parametro"

class Simbolo:
    def __init__(self, nombre: str, tipo_simbolo: TipoSimbolo, 
                 tipo_dato: str, linea: int, ambito: Ambito = Ambito.GLOBAL):
        self.nombre = nombre
        self.tipo_simbolo = tipo_simbolo
        self.tipo_dato = tipo_dato
        self.linea = linea
        self.ambito = ambito
        self.inicializada = False
        self.parametros = []
        self.valor = None
    
    def __str__(self):
        inicializada_str = " (inicializada)" if self.inicializada else ""
        return f"{self.tipo_simbolo.value.capitalize()} {self.nombre}: {self.tipo_dato}{inicializada_str} [{self.ambito.value}]"

class TablaSimbolos:
    def __init__(self):
        self.simbolos: Dict[str, List[Simbolo]] = {}
        self.pila_ambitos: List[Ambito] = [Ambito.GLOBAL]
        self.ambito_actual = Ambito.GLOBAL
        self._registrar_tipos_basicos()
    
    def _registrar_tipos_basicos(self):
        tipos_basicos = [
            'int', 'int8', 'int16', 'int32', 'int64',
            'uint', 'uint8', 'uint16', 'uint32', 'uint64',
            'float32', 'float64', 'complex64', 'complex128',
            'string', 'bool', 'byte', 'rune', 'void'
        ]
        
        palabras_reservadas = [
            'break', 'case', 'chan', 'const', 'continue', 'default',
            'defer', 'else', 'fallthrough', 'for', 'func', 'go',
            'goto', 'if', 'import', 'interface', 'map', 'package',
            'range', 'return', 'select', 'struct', 'switch', 'type',
            'var', 'true', 'false', 'nil', 'iota'
        ]
        
        for tipo in tipos_basicos:
            simbolo = Simbolo(tipo, TipoSimbolo.TIPO_DATO, tipo, 0)
            self.agregar_simbolo(simbolo)
        
        for palabra in palabras_reservadas:
            simbolo = Simbolo(palabra, TipoSimbolo.PALABRA_RESERVADA, palabra, 0)
            self.agregar_simbolo(simbolo)
    
    def es_tipo_dato(self, token):
        tipos_basicos = [
            'int', 'int8', 'int16', 'int32', 'int64',
            'uint', 'uint8', 'uint16', 'uint32', 'uint64',
            'float32', 'float64', 'complex64', 'complex128',
            'string', 'bool', 'byte', 'rune', 'void'
        ]
        return token in tipos_basicos
    
    def es_palabra_reservada(self, token):
        palabras_reservadas = [
            'break', 'case', 'chan', 'const', 'continue', 'default',
            'defer', 'else', 'fallthrough', 'for', 'func', 'go',
            'goto', 'if', 'import', 'interface', 'map', 'package',
            'range', 'return', 'select', 'struct', 'switch', 'type',
            'var', 'true', 'false', 'nil', 'iota'
        ]
        return token in palabras_reservadas
    
    def agregar_simbolo(self, simbolo: Simbolo) -> bool:
        clave = f"{simbolo.nombre}@{simbolo.ambito.value}"
        
        if clave in self.simbolos:
            for sim_existente in self.simbolos[clave]:
                if sim_existente.ambito == simbolo.ambito:
                    return False
        
        if clave not in self.simbolos:
            self.simbolos[clave] = []
        
        self.simbolos[clave].append(simbolo)
        return True
    
    def buscar_simbolo(self, nombre: str) -> Optional[Simbolo]:
        for ambito in reversed(self.pila_ambitos):
            clave = f"{nombre}@{ambito.value}"
            if clave in self.simbolos:
                return self.simbolos[clave][-1]
        return None
    
    def existe_simbolo(self, nombre: str) -> bool:
        return self.buscar_simbolo(nombre) is not None
    
    def agregar_variable(self, nombre: str, tipo_dato: str, linea: int) -> bool:
        simbolo = Simbolo(nombre, TipoSimbolo.VARIABLE, tipo_dato, linea, self.ambito_actual)
        return self.agregar_simbolo(simbolo)
    
    def agregar_funcion(self, nombre: str, tipo_retorno: str, parametros: List, linea: int) -> bool:
        simbolo = Simbolo(nombre, TipoSimbolo.FUNCION, tipo_retorno, linea, self.ambito_actual)
        simbolo.parametros = parametros
        return self.agregar_simbolo(simbolo)
    
    def agregar_parametro(self, nombre: str, tipo_dato: str, linea: int) -> bool:
        simbolo = Simbolo(nombre, TipoSimbolo.PARAMETRO, tipo_dato, linea, Ambito.PARAMETRO)
        return self.agregar_simbolo(simbolo)
    
    def entrar_ambito(self, ambito: Ambito):
        self.pila_ambitos.append(ambito)
        self.ambito_actual = ambito
    
    def salir_ambito(self):
        if len(self.pila_ambitos) > 1:
            self.pila_ambitos.pop()
            self.ambito_actual = self.pila_ambitos[-1]
    
    def obtener_variables(self) -> List[Simbolo]:
        variables = []
        for simbolos in self.simbolos.values():
            for simbolo in simbolos:
                if simbolo.tipo_simbolo == TipoSimbolo.VARIABLE:
                    variables.append(simbolo)
        return variables
    
    def obtener_funciones(self) -> List[Simbolo]:
        funciones = []
        for simbolos in self.simbolos.values():
            for simbolo in simbolos:
                if simbolo.tipo_simbolo == TipoSimbolo.FUNCION:
                    funciones.append(simbolo)
        return funciones
    
    def validar_patron_declaracion(self, tokens: List[tuple]) -> tuple[bool, str, Optional[Simbolo]]:
        if len(tokens) < 2:
            return False, "Declaración incompleta", None
        
        # Patrón 1: var nombre tipo (Go)
        if (len(tokens) >= 3 and tokens[0][0] == "TKN ID" and tokens[0][1] == "var" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN ID"):
            
            nombre_var = tokens[1][1]
            tipo_dato = tokens[2][1]
            
            if not self.es_tipo_dato(tipo_dato):
                return False, f"Tipo de dato '{tipo_dato}' no válido", None
            
            tiene_asignacion = any(t[0] == "TKN ASIGN" or t[0] == "TKN WALRUS" for t in tokens)
            
            simbolo = Simbolo(nombre_var, TipoSimbolo.VARIABLE, tipo_dato, 0, self.ambito_actual)
            if tiene_asignacion:
                simbolo.inicializada = True
            
            if self.agregar_simbolo(simbolo):
                return True, f"Variable {nombre_var}: {tipo_dato} registrada", simbolo
            else:
                return False, f"ERROR: Variable {nombre_var} ya existe en el ámbito actual", None
        
        # Patrón 2: tipo nombre = valor (Go)
        tipo_dato = None
        nombre_var = None
        tiene_asignacion = False
        
        for i, (tipo, valor) in enumerate(tokens):
            if tipo == "TKN ID" and not tipo_dato and self.es_tipo_dato(valor):
                tipo_dato = valor
            elif tipo == "TKN ID" and tipo_dato and not nombre_var:
                nombre_var = valor
            elif tipo == "TKN ASIGN" and nombre_var:
                tiene_asignacion = True
                break
            elif tipo == "TKN PUNTO_COMA" and nombre_var:
                break
        
        if not all([tipo_dato, nombre_var]):
            return False, "Patrón de declaración no válido: falta tipo o nombre", None
        
        simbolo = Simbolo(nombre_var, TipoSimbolo.VARIABLE, tipo_dato, 0, self.ambito_actual)
        
        if tiene_asignacion:
            simbolo.inicializada = True
        
        if self.agregar_simbolo(simbolo):
            return True, f"Variable {nombre_var}: {tipo_dato} registrada", simbolo
        else:
            return False, f"ERROR: Variable {nombre_var} ya existe en el ámbito actual", None
    
    def imprimir_tabla(self):
        print("=== TABLA DE SÍMBOLOS ===")
        print(f"Ámbito actual: {self.ambito_actual.value}")
        print("-" * 50)
        
        for clave, simbolos in sorted(self.simbolos.items()):
            for simbolo in simbolos:
                print(f"  {simbolo}")
        
        print("-" * 50)
        total = sum(len(simbolos) for simbolos in self.simbolos.values())
        print(f"Total de símbolos: {total}")
