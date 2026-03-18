from enum import Enum
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
        self.simbolos: Dict[str, List[Simbolo]] = {}
        self.pila_ambitos: List[Ambito] = [Ambito.GLOBAL]
        self.ambito_actual = Ambito.GLOBAL
        self.variables_declaradas = {}  # {nombre: [(tipo, linea), ...]} para detectar ambigüedad
        self._registrar_tipos_basicos()
    
    def _registrar_tipos_basicos(self):
        for tipo in TIPOS_BASICOS:
            simbolo = Simbolo(tipo, TipoSimbolo.TIPO_DATO, tipo, 0)
            self.agregar_simbolo(simbolo)
        
        for palabra in PALABRAS_RESERVADAS:
            simbolo = Simbolo(palabra, TipoSimbolo.PALABRA_RESERVADA, palabra, 0)
            self.agregar_simbolo(simbolo)
    
    def agregar_simbolo(self, simbolo) -> bool:
        if simbolo.nombre in self.simbolos:
            # Verificar si ya existe en el ámbito actual
            for s in self.simbolos[simbolo.nombre]:
                if s.ambito == simbolo.ambito:
                    # Error de redefinición
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
    
    def buscar_simbolo(self, nombre: str) -> Optional[Simbolo]:
        for ambito in reversed(self.pila_ambitos):
            clave = f"{nombre}@{ambito.value}"
            if clave in self.simbolos:
                return self.simbolos[clave][-1]
        return None
    
    def existe_simbolo(self, nombre: str) -> bool:
        return self.buscar_simbolo(nombre) is not None
    
    def agregar_variable(self, nombre: str, tipo_dato: str, linea: int) -> bool:
        # Detectar ambigüedad antes de agregar
        if not self._detectar_ambiguedad(nombre, tipo_dato, linea):
            return False
        
        simbolo = Simbolo(nombre, TipoSimbolo.VARIABLE, tipo_dato, linea, self.ambito_actual)
        return self.agregar_simbolo(simbolo)
    
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

    def validar_patron_declaracion(self, tokens: List[tuple]) -> tuple[bool, str, Optional[Simbolo]]:
        if len(tokens) < 1:
            return False, "Línea vacía", None
        
        # Patrón 0: Ignorar líneas que no son declaraciones
        # Llamadas a funciones: nombre.funcion(parametros)
        if (len(tokens) >= 3 and tokens[0][0] == "TKN ID" and tokens[1][0] == "TKN DOT" and
            tokens[2][0] == "TKN ID"):
            return False, "Llamada a función (no es declaración)", None
        
        # Llamadas simples: funcion(parametros)
        if (len(tokens) >= 3 and tokens[0][0] == "TKN ID" and tokens[1][0] == "TKN PAREN_A"):
            return False, "Llamada a función (no es declaración)", None
        
        # Solo llaves o paréntesis
        if len(tokens) == 1 and tokens[0][0] in ["TKN LLAVE_A", "TKN LLAVE_C", "TKN PAREN_A", "TKN PAREN_C"]:
            return False, "Estructura de control (no es declaración)", None
        
        # Patrón 0.5: package nombre
        if (len(tokens) >= 2 and tokens[0][0] == "TKN ID" and tokens[0][1] == "package" and
            tokens[1][0] == "TKN ID"):
            
            paquete_nombre = tokens[1][1]
            simbolo_id = f"pkg_{paquete_nombre}"
            simbolo = Simbolo(simbolo_id, TipoSimbolo.PALABRA_RESERVADA, "package", 0, self.ambito_actual)
            if self.agregar_simbolo(simbolo):
                return True, f"Paquete \"{paquete_nombre}\" registrado", simbolo
            else:
                return False, f"ERROR: Paquete \"{paquete_nombre}\" ya existe", None

        # Patrón 1: import "paquete" (import simple)
        if (len(tokens) >= 3 and tokens[0][0] == "TKN ID" and tokens[0][1] == "import" and
            tokens[1][0] == "TKN COMILLA"):
            
            # Extraer nombre del paquete entre comillas
            paquete = ""
            for i in range(1, len(tokens)):
                if tokens[i][0] == "TKN COMILLA":
                    if i + 1 < len(tokens) and tokens[i + 1][0] == "TKN ID":
                        paquete = tokens[i + 1][1]
                        break
            
            if paquete:
                simbolo = Simbolo(paquete, TipoSimbolo.PALABRA_RESERVADA, "import", 0, self.ambito_actual)
                if self.agregar_simbolo(simbolo):
                    return True, f"Import \"{paquete}\" registrado", simbolo
                else:
                    return False, f"ERROR: Import \"{paquete}\" ya existe", None
            else:
                return False, "ERROR: Formato de import inválido", None
        
        # Patrón 2: import alias "paquete" (import con alias)
        if (len(tokens) >= 4 and tokens[0][0] == "TKN ID" and tokens[0][1] == "import" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN COMILLA"):
            
            alias = tokens[1][1]
            
            # Extraer nombre del paquete entre comillas
            paquete = ""
            for i in range(2, len(tokens)):
                if tokens[i][0] == "TKN COMILLA":
                    if i + 1 < len(tokens) and tokens[i + 1][0] == "TKN ID":
                        paquete = tokens[i + 1][1]
                        break
            
            if paquete and alias:
                simbolo = Simbolo(alias, TipoSimbolo.PALABRA_RESERVADA, f"import:{paquete}", 0, self.ambito_actual)
                if self.agregar_simbolo(simbolo):
                    return True, f"Import {alias} \"{paquete}\" registrado", simbolo
                else:
                    return False, f"ERROR: Import {alias} ya existe", None
            else:
                return False, "ERROR: Formato de import con alias inválido", None
        
        # Patrón 3: func nombre() { (función Go básica)
        if (len(tokens) >= 4 and tokens[0][0] == "TKN ID" and tokens[0][1] == "func" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN PAREN_A" and tokens[3][0] == "TKN PAREN_C"):
            
            nombre_func = tokens[1][1]
            
            # Verificar si tiene llave de apertura
            tiene_llave = any(t[0] == "TKN LLAVE_A" for t in tokens)
            
            simbolo = Simbolo(nombre_func, TipoSimbolo.FUNCION, "void", 0, self.ambito_actual)
            
            if self.agregar_simbolo(simbolo):
                if tiene_llave:
                    return True, f"Función {nombre_func}() registrada", simbolo
                else:
                    return True, f"Función {nombre_func}() registrada (sin cuerpo)", simbolo
            else:
                return False, f"ERROR: Función {nombre_func} ya existe en el ámbito actual", None
        
        # Patrón 4: func nombre(parametros) tipo_retorno { (función con parámetros)
        if (len(tokens) >= 6 and tokens[0][0] == "TKN ID" and tokens[0][1] == "func" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN PAREN_A"):
            
            nombre_func = tokens[1][1]
            tipo_retorno = "void"  # Por defecto
            
            # Extraer parámetros entre paréntesis
            parametros = []
            i = 3  # Después de func nombre(
            while i < len(tokens) and tokens[i][0] != "TKN PAREN_C":
                if tokens[i][0] == "TKN ID":
                    # Puede ser tipo o nombre de parámetro
                    if i + 1 < len(tokens) and tokens[i + 1][0] == "TKN ID":
                        # Es tipo nombre: int edad
                        tipo_param = tokens[i][1]
                        nombre_param = tokens[i + 1][1]
                        parametros.append((nombre_param, tipo_param))
                        i += 2
                    else:
                        # Es solo tipo (sin nombre): int
                        parametros.append((f"param{len(parametros)}", tokens[i][1]))
                        i += 1
                elif tokens[i][0] == "TKN COMMA":
                    i += 1  # Ignorar coma
                else:
                    i += 1
            
            # Buscar tipo de retorno después de paréntesis
            for j in range(i, len(tokens)):
                if tokens[j][0] == "TKN PAREN_C" and j + 1 < len(tokens):
                    if tokens[j + 1][0] == "TKN ID" and es_tipo_dato(tokens[j + 1][1]):
                        tipo_retorno = tokens[j + 1][1]
                    break
            
            simbolo = Simbolo(nombre_func, TipoSimbolo.FUNCION, tipo_retorno, 0, self.ambito_actual)
            simbolo.parametros = parametros  # Guardar parámetros
            
            if self.agregar_simbolo(simbolo):
                params_str = ", ".join([f"{nombre}:{tipo}" for nombre, tipo in parametros])
                if params_str:
                    return True, f"Función {nombre_func}({params_str}): {tipo_retorno} registrada", simbolo
                else:
                    return True, f"Función {nombre_func}(): {tipo_retorno} registrada", simbolo
            else:
                return False, f"ERROR: Función {nombre_func} ya existe en el ámbito actual", None
        
        # Patrón 5: type Nombre struct { (structs - equivalente a clases en Go)
        if (len(tokens) >= 4 and tokens[0][0] == "TKN ID" and tokens[0][1] == "type" and
            tokens[1][0] == "TKN ID" and tokens[2][0] == "TKN ID" and tokens[2][1] == "struct" and
            tokens[3][0] == "TKN LLAVE_A"):
            
            nombre_struct = tokens[1][1]
            
            simbolo = Simbolo(nombre_struct, TipoSimbolo.TIPO_DATO, "struct", 0, self.ambito_actual)
            
            if self.agregar_simbolo(simbolo):
                return True, f"Struct {nombre_struct} definido", simbolo
            else:
                return False, f"ERROR: Struct {nombre_struct} ya existe en el ámbito actual", None
        
        # Patrón 6: var nombre tipo (Go)
        if len(tokens) >= 3 and tokens[0][0] == "TKN ID" and tokens[0][1] == "var" and tokens[1][0] == "TKN ID":
            
            nombre_var = tokens[1][1]
            tipo_dato = ""
            i = 2
            
            # Checar si es puntero
            if i < len(tokens) and tokens[i][0] == "TKN OPMULT" and tokens[i][1] == "*":
                tipo_dato += "*"
                i += 1
                
            if i < len(tokens) and tokens[i][0] == "TKN ID":
                tipo_dato += tokens[i][1]
                i += 1
            
            # Verificar si el tipo base es válido
            tipo_base = tipo_dato.replace("*", "")
            if not es_tipo_dato(tipo_base) and tipo_base != "struct":
                # Si no es tipo de dato básico, asumiremos que puede ser un interface u objeto
                pass
            
            tiene_asignacion = any(t[0] == "TKN ASIGN" or t[0] == "TKN WALRUS" for t in tokens)
            
            simbolo = Simbolo(nombre_var, TipoSimbolo.VARIABLE, tipo_dato, 0, self.ambito_actual)
            if tiene_asignacion:
                simbolo.inicializada = True
            
            if self.agregar_simbolo(simbolo):
                return True, f"Variable {nombre_var}: {tipo_dato} registrada", simbolo
            else:
                return False, f"ERROR: Variable {nombre_var} ya existe en el ámbito actual", None
        
        # Patrón 7: nombre := valor (declaración corta con inferencia de tipo)
        nombre_var = None
        tiene_walrus = False
        
        # Buscar := en los tokens
        for i, (tipo, valor) in enumerate(tokens):
            if tipo == "TKN WALRUS":
                tiene_walrus = True
                # El nombre de la variable está antes de :=
                if i > 0 and tokens[i-1][0] == "TKN ID":
                    nombre_var = tokens[i-1][1]
                break
        
        if nombre_var and tiene_walrus:
            # Para := no necesitamos verificar tipo, se infiere automáticamente
            simbolo = Simbolo(nombre_var, TipoSimbolo.VARIABLE, "auto", 0, self.ambito_actual)
            simbolo.inicializada = True
            
            if self.agregar_simbolo(simbolo):
                return True, f"Variable {nombre_var} (inferida) registrada", simbolo
            else:
                return False, f"ERROR: Variable {nombre_var} ya existe en el ámbito actual", None
        
        # Si el token incluye la palabra "var" y llegó hasta aquí, no es un Patrón 8
        if any(t[1] == "var" for t in tokens):
            return False, "Error de declaración con keyword 'var' mal formado", None
        
        # Patrón 8: tipo nombre = valor (Go)
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
            # Error de patrón inválido
            agregar_error_patron(
                "No es una declaración válida: falta tipo o nombre",
                0,  # línea se debería pasar como parámetro
                0,
                " ".join([token[1] for token in tokens])
            )
            return False, "No es una declaración válida", None
        
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
