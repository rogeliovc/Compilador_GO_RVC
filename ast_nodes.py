class NodoAST:
    def __init__(self, tipo, valor=None, linea=0):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.hijos = []
        self.tipo_resultado = None  # Para decoración semántica
    
    def agregar_hijo(self, hijo):
        if hijo is not None:
            self.hijos.append(hijo)
    
    def __str__(self):
        return f"{self.tipo}: {self.valor}" if self.valor else self.tipo

# --- NODOS DE EXPRESIONES (Devuelven un valor) ---
class Numero(NodoAST):
    def __init__(self, valor, linea=0):
        super().__init__("Numero", valor, linea)

class StringLiteral(NodoAST):
    def __init__(self, valor, linea=0):
        super().__init__("String", valor, linea)

class BooleanLiteral(NodoAST):
    def __init__(self, valor, linea=0):
        super().__init__("Boolean", valor, linea)

class Variable(NodoAST):
    def __init__(self, nombre, linea=0):
        super().__init__("Variable", nombre, linea)

class OperacionBinaria(NodoAST):
    def __init__(self, operador, izquierdo, derecho, linea=0):
        super().__init__(f"OpBinaria({operador})", operador, linea)
        self.agregar_hijo(izquierdo)
        self.agregar_hijo(derecho)

class OperacionUnaria(NodoAST):
    def __init__(self, operador, operando, linea=0):
        super().__init__(f"OpUnaria({operador})", operador, linea)
        self.agregar_hijo(operando)

class LlamadaFuncion(NodoAST):
    def __init__(self, expr_funcion, argumentos, linea=0):
        # Usamos el tipo real del nodo para el valor de depuración
        nombre = expr_funcion.valor if hasattr(expr_funcion, 'valor') else "func_expr"
        super().__init__("LlamadaFuncion", nombre, linea)
        self.expr_funcion = expr_funcion
        self.agregar_hijo(expr_funcion)
        for arg in argumentos:
            self.agregar_hijo(arg)

class AttributeAccess(NodoAST):
    def __init__(self, base, attr, linea=0):
        super().__init__("AttributeAccess", attr, linea)
        self.agregar_hijo(base)

class ArrayAccess(NodoAST):
    def __init__(self, base, indice, linea=0):
        super().__init__("ArrayAccess", None, linea)
        self.agregar_hijo(base)
        self.agregar_hijo(indice)

# --- NODOS DE SENTENCIAS (No devuelven valor, controlan el flujo) ---
class Programa(NodoAST):
    def __init__(self, linea=0):
        super().__init__("Programa", None, linea)

class Bloque(NodoAST):
    def __init__(self, linea=0):
        super().__init__("Bloque", None, linea)

class DeclaracionVariable(NodoAST):
    def __init__(self, nombre, tipo_dato, expresion_valor=None, linea=0):
        super().__init__("DeclaracionVar", nombre, linea)
        self.tipo_dato = tipo_dato
        self.agregar_hijo(expresion_valor)

class Asignacion(NodoAST):
    def __init__(self, identificador, expresion, linea=0):
        super().__init__("Asignacion", "=", linea)
        self.agregar_hijo(identificador)
        self.agregar_hijo(expresion)

class If(NodoAST):
    def __init__(self, condicion, bloque_true, bloque_false=None, linea=0, init_stmt=None):
        super().__init__("If", None, linea)
        self.init_stmt = init_stmt
        # Posiciones fijas: 0:cond, 1:true, 2:false
        self.hijos = [condicion, bloque_true, bloque_false]

class For(NodoAST):
    def __init__(self, init, condicion, post, bloque, linea=0):
        super().__init__("For", None, linea)
        # Posiciones fijas: 0:init, 1:cond, 2:post, 3:bloque
        self.hijos = [init, condicion, post, bloque]

class Switch(NodoAST):
    def __init__(self, expresion, casos, linea=0):
        super().__init__("Switch", None, linea)
        self.agregar_hijo(expresion)
        for caso in casos:
            self.agregar_hijo(caso)

class Case(NodoAST):
    def __init__(self, expresiones, bloque, es_default=False, linea=0):
        super().__init__("Case", "default" if es_default else "case", linea)
        self.es_default = es_default
        for expr in (expresiones or []):
            self.agregar_hijo(expr)
        self.agregar_hijo(bloque)

class Funcion(NodoAST):
    def __init__(self, nombre, parametros, tipo_retorno, bloque, linea=0):
        super().__init__("Funcion", nombre, linea)
        # parametros podría ser una lista de tuplas (nombre, tipo) que guardamos en propiedades
        self.parametros = parametros
        self.tipo_retorno = tipo_retorno
        self.agregar_hijo(bloque)

class Return(NodoAST):
    def __init__(self, expresion=None, linea=0):
        super().__init__("Return", None, linea)
        if expresion:
            self.agregar_hijo(expresion)

class Break(NodoAST):
    def __init__(self, linea=0):
        super().__init__("Break", "break", linea)

class Continue(NodoAST):
    def __init__(self, linea=0):
        super().__init__("Continue", "continue", linea)

class Import(NodoAST):
    def __init__(self, paquete, linea=0):
        super().__init__("Import", paquete, linea)