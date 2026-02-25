class NodoAST:
    """Clase base para todos los nodos del AST"""
    def __init__(self, tipo, valor=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = []
    
    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)
    
    def __str__(self):
        return f"{self.tipo}: {self.valor}" if self.valor else self.tipo

class Numero(NodoAST):
    def __init__(self, valor):
        super().__init__("Numero", valor)

class OperacionBinaria(NodoAST):
    def __init__(self, operador, izquierdo, derecho):
        super().__init__(self._get_nombre_operacion(operador), operador)
        self.agregar_hijo(izquierdo)
        self.agregar_hijo(derecho)
    
    def _get_nombre_operacion(self, operador):
        nombres = {
            '+': 'Suma',
            '-': 'Resta',
            '*': 'Multiplica',
            '/': 'Divide',
            '×': 'Multiplica'
        }
        return nombres.get(operador, f'Operacion_{operador}')

class Variable(NodoAST):
    def __init__(self, nombre):
        super().__init__("Variable", nombre)

class Asignacion(NodoAST):
    def __init__(self, variable, expresion):
        super().__init__("Asignacion", "=")
        self.agregar_hijo(variable)
        self.agregar_hijo(expresion)

class ExpresionParentesis(NodoAST):
    def __init__(self, expresion):
        super().__init__("Parentesis", "()")
        self.agregar_hijo(expresion)