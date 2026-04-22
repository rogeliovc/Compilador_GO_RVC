class NodoAST:
    def __init__(self, tipo, valor=None, linea=0):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.hijos = []
    
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
    def __init__(self, condicion, bloque_true, bloque_false=None, linea=0):
        super().__init__("If", None, linea)
        self.agregar_hijo(condicion)
        self.agregar_hijo(bloque_true)
        if bloque_false:
            self.agregar_hijo(bloque_false)

class For(NodoAST):
    def __init__(self, init, condicion, post, bloque, linea=0):
        super().__init__("For", None, linea)
        self.agregar_hijo(init)
        self.agregar_hijo(condicion)
        self.agregar_hijo(post)
        self.agregar_hijo(bloque)

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

class Import(NodoAST):
    def __init__(self, paquete, linea=0):
        super().__init__("Import", paquete, linea)

class ParserExpresiones:
    def __init__(self, tokens):
        # Ignoramos espacios y saltos de línea al parsear expresiones
        # Note: now tokens are (tipo, valor, linea)
        self.tokens = [t for t in tokens if t[1] not in [' ', '\n', '\t', ';', '{']]
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, tipo_o_valor):
        t = self.peek()
        if t and (t[0] == tipo_o_valor or t[1] == tipo_o_valor):
            self.pos += 1
            return t
        return None

    def parse(self):
        if not self.tokens:
            return None
        nodo = self.parse_expresion()
        if self.pos < len(self.tokens):
            t_sobrante = self.tokens[self.pos][1]
            linea = self.tokens[self.pos][2] if len(self.tokens[self.pos]) > 2 else 0
            raise SyntaxError(f"Token inesperado '{t_sobrante}' al final de la expresión")
        return nodo

    # --- INICIO DE NIVELES DE PRECEDENCIA ---

    def parse_expresion(self):
        return self.parse_or()

    def parse_or(self):
        nodo = self.parse_and()
        while self.peek() and self.peek()[1] == '||':
            op = self.match('||')
            linea = op[2] if len(op) > 2 else 0
            der = self.parse_and()
            nodo = OperacionBinaria(op[1], nodo, der, linea)
        return nodo

    def parse_and(self):
        nodo = self.parse_igualdad()
        while self.peek() and self.peek()[1] == '&&':
            op = self.match('&&')
            linea = op[2] if len(op) > 2 else 0
            der = self.parse_igualdad()
            nodo = OperacionBinaria(op[1], nodo, der, linea)
        return nodo

    def parse_igualdad(self):
        nodo = self.parse_comparacion()
        while self.peek() and self.peek()[1] in ['==', '!=']:
            op = self.peek()
            self.pos += 1
            linea = op[2] if len(op) > 2 else 0
            der = self.parse_comparacion()
            nodo = OperacionBinaria(op[1], nodo, der, linea)
        return nodo

    def parse_comparacion(self):
        nodo = self.parse_termino()
        while self.peek() and self.peek()[1] in ['<', '>', '<=', '>=']:
            op = self.peek()
            self.pos += 1
            linea = op[2] if len(op) > 2 else 0
            der = self.parse_termino()
            nodo = OperacionBinaria(op[1], nodo, der, linea)
        return nodo

    def parse_termino(self):
        nodo = self.parse_factor()
        while self.peek() and self.peek()[1] in ['+', '-']:
            op = self.peek()
            self.pos += 1
            linea = op[2] if len(op) > 2 else 0
            der = self.parse_factor()
            nodo = OperacionBinaria(op[1], nodo, der, linea)
        return nodo

    def parse_factor(self):
        nodo = self.parse_unario()
        while self.peek() and self.peek()[1] in ['*', '/', '%']:
            op = self.peek()
            self.pos += 1
            linea = op[2] if len(op) > 2 else 0
            der = self.parse_unario()
            nodo = OperacionBinaria(op[1], nodo, der, linea)
        return nodo

    def parse_unario(self):
        t = self.peek()
        if t and t[1] in ['-', '!', '++', '--', '*', '&']:
            self.pos += 1
            linea = t[2] if len(t) > 2 else 0
            operando = self.parse_unario()
            return OperacionUnaria(t[1], operando, linea)
        return self.parse_primario()

    def parse_primario(self):
        t = self.peek()
        if not t:
            raise SyntaxError("Se esperaba una expresión o valor")
            
        linea = t[2] if len(t) > 2 else 0
        nodo = None
        
        # Paréntesis
        if t[1] == '(':
            self.pos += 1
            nodo = self.parse_expresion()
            if not self.match(')'):
                raise SyntaxError("Falta paréntesis de cierre ')'")
            
        # Literales Numéricos
        elif t[0] in ['TKN NUM', 'TKN DEC', 'TKN FLO'] or t[1].replace('.', '', 1).isdigit():
            self.pos += 1
            nodo = Numero(t[1], linea)
            
        # Literales String
        elif t[0] in ['TKN STRING', 'TKN COMILLA'] or '"' in t[1] or "'" in t[1] or '`' in t[1]:
            self.pos += 1
            nodo = StringLiteral(t[1], linea)
            
        # Literales Booleanos / Nil
        elif t[1] in ['true', 'false', 'nil']:
            self.pos += 1
            nodo = BooleanLiteral(t[1], linea)
            
        # Identificadores (Variables, Atributos, Llamadas a Funciones)
        elif t[0] == 'TKN ID' or t[1].isidentifier():
            self.pos += 1
            nodo = Variable(t[1], linea)
            
        if not nodo:
            raise SyntaxError(f"Se esperaba una expresión válida pero se encontró '{t[1]}'")
            
        # Procesar sufijos (accesos a atributos y llamadas a función)
        while self.peek():
            sig = self.peek()
            if sig[1] == '.':
                self.pos += 1
                attr = self.peek()
                if attr and (attr[0] == 'TKN ID' or attr[1].isidentifier()):
                    self.pos += 1
                    nodo = AttributeAccess(nodo, attr[1], sig[2] if len(sig)>2 else linea)
                else:
                    raise SyntaxError("Se esperaba un identificador después de '.'")
            elif sig[1] == '(':
                self.pos += 1
                args = []
                while self.peek() and self.peek()[1] != ')':
                    args.append(self.parse_expresion())
                    if not self.match(','):
                        break
                if not self.match(')'):
                    raise SyntaxError("Falta paréntesis de cierre ')' en llamada a función")
                
                nodo = LlamadaFuncion(nodo, args, sig[2] if len(sig)>2 else linea)
            else:
                break
                
        return nodo