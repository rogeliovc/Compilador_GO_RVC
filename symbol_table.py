from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from utils import TIPOS_BASICOS, PALABRAS_RESERVADAS, es_tipo_dato, es_palabra_reservada
from utils import TIPOS_BASICOS, PALABRAS_RESERVADAS, es_tipo_dato, es_palabra_reservada

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
                 tipo_dato: str, linea: int, ambito: Ambito = Ambito.GLOBAL, scope_id: int = 0):
        self.nombre = nombre
        self.tipo_simbolo = tipo_simbolo
        self.tipo_dato = tipo_dato
        self.linea = linea
        self.ambito = ambito
        self.scope_id = scope_id
        self.inicializada = False
        self.parametros = []
        self.valor = None
    
    def __str__(self):
        inicializada_str = " (inicializada)" if self.inicializada else ""
        return f"{self.tipo_simbolo.value.capitalize()} {self.nombre}: {self.tipo_dato}{inicializada_str} [{self.ambito.value}_{self.scope_id}]"

class TablaSimbolos:
    def __init__(self):
        self.simbolos: dict[str, list[Simbolo]] = {}
        self.pila_ambitos: list[Ambito] = [Ambito.GLOBAL]
        self.pila_scope_ids: list[int] = [0]
        self.scope_counter = 0
        self.ambito_actual = Ambito.GLOBAL
        self.scope_id_actual = 0
        self.variables_declaradas = {}  # {nombre: [(tipo, linea), ...]} para detectar ambigüedad
        self._registrar_tipos_basicos()
        self.en_bloque_import = False  # Estado para bloques multi-línea
    
    def _registrar_tipos_basicos(self):
        for tipo in TIPOS_BASICOS:
            simbolo = Simbolo(tipo, TipoSimbolo.TIPO_DATO, tipo, 0)
            self.agregar_simbolo(simbolo)
        
        for palabra in PALABRAS_RESERVADAS:
            simbolo = Simbolo(palabra, TipoSimbolo.PALABRA_RESERVADA, palabra, 0)
            self.agregar_simbolo(simbolo)
    
    def agregar_simbolo(self, simbolo) -> bool:
        self.simbolos.setdefault(simbolo.nombre, []).append(simbolo)
        return True
    
    def buscar_simbolo(self, nombre: str) -> Simbolo | None:
        if nombre in self.simbolos:
            simbolos_lista = self.simbolos[nombre]
            for ambito, scope_id in zip(reversed(self.pila_ambitos), reversed(self.pila_scope_ids)):
                for s in reversed(simbolos_lista):
                    if s.ambito == ambito and s.scope_id == scope_id:
                        return s
        return None
    
    def existe_simbolo(self, nombre: str) -> bool:
        return self.buscar_simbolo(nombre) is not None
    
    def existe_en_ambito_actual(self, nombre: str) -> bool:
        if nombre in self.simbolos:
            for s in self.simbolos[nombre]:
                if s.ambito == self.ambito_actual and s.scope_id == self.scope_id_actual:
                    return True
        return False
        
    def agregar_variable(self, nombre: str, tipo_dato: str, linea: int) -> bool:
        simbolo = Simbolo(nombre, TipoSimbolo.VARIABLE, tipo_dato, linea, self.ambito_actual, self.scope_id_actual)
        return self.agregar_simbolo(simbolo)
    
    def agregar_funcion(self, nombre: str, tipo_retorno: str, parametros: List, linea: int) -> bool:
        simbolo = Simbolo(nombre, TipoSimbolo.FUNCION, tipo_retorno, linea, self.ambito_actual, self.scope_id_actual)
        simbolo.parametros = parametros
        return self.agregar_simbolo(simbolo)
    
    def agregar_parametro(self, nombre: str, tipo_dato: str, linea: int) -> bool:
        simbolo = Simbolo(nombre, TipoSimbolo.PARAMETRO, tipo_dato, linea, self.ambito_actual, self.scope_id_actual)
        return self.agregar_simbolo(simbolo)
    
    def entrar_ambito(self, ambito: Ambito):
        self.pila_ambitos.append(ambito)
        self.ambito_actual = ambito
        self.scope_counter += 1
        self.pila_scope_ids.append(self.scope_counter)
        self.scope_id_actual = self.scope_counter
    
    def salir_ambito(self):
        if len(self.pila_ambitos) > 1:
            self.pila_ambitos.pop()
            self.ambito_actual = self.pila_ambitos[-1]
            self.pila_scope_ids.pop()
            self.scope_id_actual = self.pila_scope_ids[-1]

    def entrar_ambito_for(self, nombre_for: str = "for"):
        """Entrar a un nuevo ámbito de bucle for"""
        nuevo_ambito = Ambito.LOCAL  # Los bucles for tienen ámbito local
        self.pila_ambitos.append(nuevo_ambito)
        self.ambito_actual = nuevo_ambito
        self.scope_counter += 1
        self.pila_scope_ids.append(self.scope_counter)
        self.scope_id_actual = self.scope_counter
        return nuevo_ambito
    
    def salir_ambito_for(self):
        """Salir del ámbito actual del bucle for"""
        if len(self.pila_ambitos) > 1:  # Mantener siempre el ámbito global
            self.pila_ambitos.pop()
            self.ambito_actual = self.pila_ambitos[-1]
            self.pila_scope_ids.pop()
            self.scope_id_actual = self.pila_scope_ids[-1]
        return self.ambito_actual
    

    
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
