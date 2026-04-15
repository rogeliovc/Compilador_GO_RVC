from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from utils import TIPOS_BASICOS, PALABRAS_RESERVADAS, es_tipo_dato, es_palabra_reservada
from errors import agregar_error_redefinicion, agregar_error_patron, agregar_error_declaracion, agregar_error_tipo, agregar_error_ambito, agregar_error_uso

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
        self.simbolos: dict[str, list[Simbolo]] = {}
        self.pila_ambitos: list[Ambito] = [Ambito.GLOBAL]
        self.ambito_actual = Ambito.GLOBAL
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
    
    def agregar_simbolo(self, simbolo, es_declaracion_corta: bool = False) -> bool:
        if simbolo.nombre in self.simbolos:
            # Verificar si ya existe en el ámbito actual
            for s in self.simbolos[simbolo.nombre]:
                if s.ambito == simbolo.ambito:
                    # Si es declaración corta (:=), permitir redeclaración en Go
                    if es_declaracion_corta:
                        # En Go, := puede redeclarar si al menos una variable es nueva
                        # Por simplicidad, permitimos la redeclaración
                        pass
                    else:
                        # Error de redefinición para declaraciones normales (var)
                        agregar_error_redefinicion(
                            f"El {simbolo.tipo_simbolo.value} '{simbolo.nombre}' ya existe en el ámbito actual",
                            simbolo.linea,
                            0,
                            f"{simbolo.tipo_simbolo.value} {simbolo.nombre}: {simbolo.tipo_dato}",
                            simbolo.nombre
                        )
                        return False
        self.simbolos.setdefault(simbolo.nombre, []).append(simbolo)
        return True
    
    def buscar_simbolo(self, nombre: str) -> Simbolo | None:
        if nombre in self.simbolos:
            # Buscar en los símbolos del nombre dado, priorizando el ámbito actual
            simbolos_lista = self.simbolos[nombre]
            
            # Buscar en la pila de ámbitos (del más específico al más general)
            for ambito in reversed(self.pila_ambitos):
                for s in reversed(simbolos_lista):
                    if s.ambito == ambito:
                        return s
        return None
    
    def existe_simbolo(self, nombre: str) -> bool:
        return self.buscar_simbolo(nombre) is not None
    
    def agregar_variable(self, nombre: str, tipo_dato: str, linea: int, es_declaracion_corta: bool = False) -> bool:
        # Detectar ambigüedad antes de agregar (solo si no es declaración corta)
        if not es_declaracion_corta and not self._detectar_ambiguedad(nombre, tipo_dato, linea):
            return False
        
        simbolo = Simbolo(nombre, TipoSimbolo.VARIABLE, tipo_dato, linea, self.ambito_actual)
        return self.agregar_simbolo(simbolo, es_declaracion_corta)
    
    def _detectar_ambiguedad(self, nombre: str, tipo: str, linea: int) -> bool:
        """Detecta ambigüedad de variables con mismo nombre y diferente tipo"""
        if nombre not in self.variables_declaradas:
            self.variables_declaradas[nombre] = []
        
        # Verificar ambigüedad (mismo nombre, diferente tipo)
        for tipo_existente, linea_existente in self.variables_declaradas[nombre]:
            if tipo_existente != tipo:
                # Ambigüedad detectada
                agregar_error_redefinicion(
                    f"Ambigüedad: variable '{nombre}' declarada como '{tipo_existente}' en línea {linea_existente} y ahora como '{tipo}'",
                    linea,
                    0,
                    f"{nombre}: {tipo_existente} vs {tipo}",
                    nombre
                )
                return False
        
        # Registrar variable
        self.variables_declaradas[nombre].append((tipo, linea))
        return True
    
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

    def validar_patron_declaracion(self, tokens: list[tuple]) -> tuple[bool, str, Optional[Simbolo]]:
        if len(tokens) < 1:
            return False, "Línea vacía", None
            
        # Estructuras de control y saltos (delegados al Parser)
        if any(t[1].lower() in ['if', 'else', 'for', 'switch', 'case', 'default'] for t in tokens):
            return False, "Estructura de control", None
            
        if len(tokens) >= 1 and tokens[0][1] in ["break", "continue", "fallthrough", "return", "goto"]:
            return False, "Salto de control de flujo", None
        
        if len(tokens) == 1 and tokens[0][0] in ["TKN LLAVE_A", "TKN LLAVE_C", "TKN PAREN_A", "TKN PAREN_C"]:
            return False, "Estructura de control", None

        #const
        if any(t[1] == "const" for t in tokens):
            return True, "Declaración de constante(s) analizada", None

        if (len(tokens) >= 2 and tokens[0][1] == "package" and tokens[1][0] == "TKN ID"):
            
            paquete_nombre = tokens[1][1]
            simbolo_id = f"pkg_{paquete_nombre}"
            simbolo = Simbolo(simbolo_id, TipoSimbolo.PALABRA_RESERVADA, "package", 0, self.ambito_actual)
            if self.agregar_simbolo(simbolo):
                return True, f"Paquete \"{paquete_nombre}\" registrado", simbolo
            else:
                return False, f"ERROR: Paquete \"{paquete_nombre}\" ya existe", None

        if (len(tokens) >= 2 and tokens[0][1] == "import" and tokens[1][0] == "TKN_STRING"):
            paquete = tokens[1][1].strip('"').strip('`')
            simbolo = Simbolo(paquete, TipoSimbolo.PALABRA_RESERVADA, "import", 0, self.ambito_actual)
            if self.agregar_simbolo(simbolo):
                return True, f"Import \"{paquete}\" registrado", simbolo
            else:
                return False, f"ERROR: Import \"{paquete}\" ya existe", None
        
        if (len(tokens) >= 3 and tokens[0][1] == "import" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN_STRING"):
            
            alias = tokens[1][1]
            paquete = tokens[2][1].strip('"').strip('`')
            
            simbolo = Simbolo(alias, TipoSimbolo.PALABRA_RESERVADA, f"import:{paquete}", 0, self.ambito_actual)
            if self.agregar_simbolo(simbolo):
                return True, f"Import {alias} \"{paquete}\" registrado", simbolo
            else:
                return False, f"ERROR: Import {alias} ya existe", None
        
        if (len(tokens) >= 4 and tokens[0][0] == "TKN ID" and tokens[0][1] == "func" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN PAREN_A" and tokens[3][0] == "TKN PAREN_C"):
            
            nombre_func = tokens[1][1]
            
            tiene_llave = any(t[0] == "TKN LLAVE_A" for t in tokens)
            
            simbolo = Simbolo(nombre_func, TipoSimbolo.FUNCION, "void", 0, self.ambito_actual)
            
            if self.agregar_simbolo(simbolo):
                if tiene_llave:
                    return True, f"Función {nombre_func}() registrada", simbolo
                else:
                    return True, f"Función {nombre_func}() registrada (sin cuerpo)", simbolo
            else:
                return False, f"ERROR: Función {nombre_func} ya existe en el ámbito actual", None
        
        if (len(tokens) >= 6 and tokens[0][0] == "TKN ID" and tokens[0][1] == "func" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN PAREN_A"):
            
            nombre_func = tokens[1][1]
            tipo_retorno = "void" 
            
            parametros = []
            i = 3  
            while i < len(tokens) and tokens[i][0] != "TKN PAREN_C":
                if tokens[i][0] == "TKN ID":
                    if i + 1 < len(tokens) and tokens[i + 1][0] == "TKN ID":
                        tipo_param = tokens[i][1]
                        nombre_param = tokens[i + 1][1]
                        parametros.append((nombre_param, tipo_param))
                        i += 2
                    else:
                        parametros.append((f"param{len(parametros)}", tokens[i][1]))
                        i += 1
                elif tokens[i][0] == "TKN COMMA":
                    i += 1  
                else:
                    i += 1
            
            for j in range(i, len(tokens)):
                if tokens[j][0] == "TKN PAREN_C" and j + 1 < len(tokens):
                    if tokens[j + 1][0] == "TKN ID" and es_tipo_dato(tokens[j + 1][1]):
                        tipo_retorno = tokens[j + 1][1]
                    break
            
            simbolo = Simbolo(nombre_func, TipoSimbolo.FUNCION, tipo_retorno, 0, self.ambito_actual)
            simbolo.parametros = parametros
            if self.agregar_simbolo(simbolo):
                params_str = ", ".join([f"{nombre}:{tipo}" for nombre, tipo in parametros])
                if params_str:
                    return True, f"Función {nombre_func}({params_str}): {tipo_retorno} registrada", simbolo
                else:
                    return True, f"Función {nombre_func}(): {tipo_retorno} registrada", simbolo
            else:
                return False, f"ERROR: Función {nombre_func} ya existe en el ámbito actual", None
        
        if (len(tokens) >= 4 and tokens[0][0] == "TKN ID" and tokens[0][1] == "type" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN ID" and tokens[2][1] == "struct" and
            tokens[3][0] == "TKN LLAVE_A"):
            
            nombre_struct = tokens[1][1]
            
            simbolo = Simbolo(nombre_struct, TipoSimbolo.TIPO_DATO, "struct", 0, self.ambito_actual)
            
            if self.agregar_simbolo(simbolo):
                return True, f"Struct {nombre_struct} definido", simbolo
            else:
                return False, f"ERROR: Struct {nombre_struct} ya existe en el ámbito actual", None
        
        if len(tokens) >= 3 and tokens[0][0] == "TKN ID" and tokens[0][1] == "var" and tokens[1][0] == "TKN ID":
            
            nombre_var = tokens[1][1]
            tipo_dato = ""
            i = 2
            
            if i < len(tokens) and tokens[i][0] == "TKN OPMULT" and tokens[i][1] == "*":
                tipo_dato += "*"
                i += 1
                
            if i < len(tokens) and tokens[i][0] == "TKN ID":
                tipo_dato += tokens[i][1]
                i += 1
            
            tipo_base = tipo_dato.replace("*", "")
            if not es_tipo_dato(tipo_base) and not self.existe_simbolo(tipo_base):
                return False, f"ERROR SEMÁNTICO: Tipo de dato no reconocido '{tipo_base}' para la variable '{nombre_var}'", None
            
            tiene_asignacion = any(t[0] == "TKN ASIGN" or t[0] == "TKN WALRUS" for t in tokens)
            
            simbolo = Simbolo(nombre_var, TipoSimbolo.VARIABLE, tipo_dato, 0, self.ambito_actual)
            if tiene_asignacion:
                simbolo.inicializada = True
            
            if self.agregar_simbolo(simbolo):
                return True, f"Variable {nombre_var}: {tipo_dato} registrada", simbolo
            else:
                return False, f"ERROR: Variable {nombre_var} ya existe en el ámbito actual", None
        
        nombre_var = None
        tiene_walrus = False
        
        for i, (tipo, valor) in enumerate(tokens):
            if tipo == "TKN WALRUS":
                tiene_walrus = True
                if i > 0 and tokens[i-1][0] == "TKN ID":
                    nombre_var = tokens[i-1][1]
                break
        
        if nombre_var and tiene_walrus:
            simbolo = Simbolo(nombre_var, TipoSimbolo.VARIABLE, "auto", 0, self.ambito_actual)
            simbolo.inicializada = True
            
            if self.agregar_simbolo(simbolo):
                return True, f"Variable {nombre_var} (inferida) registrada", simbolo
            else:
                return False, f"ERROR: Variable {nombre_var} ya existe en el ámbito actual", None
        
        if any(t[1] == "var" for t in tokens):
            return False, "Error de declaración con keyword 'var' mal formado", None
        
        tipo_dato = None
        nombre_var = None
        tiene_asignacion = False
        
        for i, (tipo, valor) in enumerate(tokens):
            if tipo == "TKN ID" and not tipo_dato and es_tipo_dato(valor):
                tipo_dato = valor
            elif tipo == "TKN ID" and tipo_dato and not nombre_var:
                nombre_var = valor
            elif tipo == "TKN ASIGN" and nombre_var:
                tiene_asignacion = True
                break
            elif tipo == "TKN PUNTO_COMA" and nombre_var:
                break
        
        if not all([tipo_dato, nombre_var]):
            if any(t[0] == "TKN ASIGN" for t in tokens):
                return False, "Asignación (no es declaración)", None
            
            # Patrón para cierres de bloque (incluyendo punto y coma)
            if len(tokens) >= 1 and tokens[0][1] in ["}", ")", "]"]:
                return False, "Cierre de bloque (no es declaración)", None
            
            # Patrón para operadores de incremento/decremento (++, --)
            if len(tokens) >= 2 and tokens[0][0] == "TKN ID" and tokens[1][0] in ["TKN INC", "TKN DEC"]:
                return True, "Operación de incremento/decremento válida", None
            
            # Patrón para llamadas a función: objeto.metodo() o funcion()
            if len(tokens) >= 3:
                # Buscar patrón: ID . ID ( ... )
                for i in range(len(tokens) - 2):
                    if (tokens[i][0] == "TKN ID" and 
                        tokens[i+1][1] == "." and 
                        tokens[i+2][0] == "TKN ID"):
                        return False, "Llamada a método (no es declaración)", None
                
                # Buscar patrón: ID ( ... )
                for i in range(len(tokens) - 1):
                    if (tokens[i][0] == "TKN ID" and 
                        tokens[i+1][0] == "TKN PAREN_A"):
                        return False, "Llamada a función (no es declaración)", None
            
            return False, "No es una declaración válida", None
        
        simbolo = Simbolo(nombre_var, TipoSimbolo.VARIABLE, tipo_dato, 0, self.ambito_actual)
        
        if tiene_asignacion:
            simbolo.inicializada = True
        
        if self.agregar_simbolo(simbolo):
            return True, f"Variable {nombre_var}: {tipo_dato} registrada", simbolo
        else:
            return False, f"ERROR: Variable {nombre_var} ya existe en el ámbito actual", None

    
    def entrar_ambito_for(self, nombre_for: str = "for"):
        """Entrar a un nuevo ámbito de bucle for"""
        nuevo_ambito = Ambito.LOCAL  # Los bucles for tienen ámbito local
        self.pila_ambitos.append(nuevo_ambito)
        self.ambito_actual = nuevo_ambito
        return nuevo_ambito
    
    def salir_ambito_for(self):
        """Salir del ámbito actual del bucle for"""
        if len(self.pila_ambitos) > 1:  # Mantener siempre el ámbito global
            self.pila_ambitos.pop()
            self.ambito_actual = self.pila_ambitos[-1]
        return self.ambito_actual
    
    def limpiar_ambito_local(self):
        """Limpiar todas las variables del ámbito local actual"""
        ambito_a_limpiar = self.ambito_actual
        if ambito_a_limpiar == Ambito.LOCAL:
            # Eliminar todos los símbolos del ámbito local
            nombres_a_eliminar = []
            for nombre, simbolos in self.simbolos.items():
                # Mantener solo los símbolos que no son del ámbito local actual
                simbolos_filtrados = [s for s in simbolos if s.ambito != ambito_a_limpiar]
                if simbolos_filtrados:
                    self.simbolos[nombre] = simbolos_filtrados
                else:
                    nombres_a_eliminar.append(nombre)
            
            # Eliminar nombres que ya no tienen símbolos
            for nombre in nombres_a_eliminar:
                del self.simbolos[nombre]
    
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
