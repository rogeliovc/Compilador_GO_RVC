class NodoAST:
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

class ParserExpresiones:
    def __init__(self, tokens):
        # Ignorar posibles espacios residuales o tokens no esenciales
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
            raise SyntaxError(f"Token (operador o variable) inesperado '{t_sobrante}' en la expresión")
        return nodo

    def parse_expresion(self):
        nodo = self.parse_primario()
        
        while self.peek():
            op = self.peek()
            # Lista de operadores soportados por nuestro AST binario
            operadores_validos = [
                '+', '-', '*', '/', '%', 
                '<', '>', '<=', '>=', '==', '!=', 
                '&&', '||', '='
            ]
            if op[1] in operadores_validos:
                self.pos += 1
                der = self.parse_primario()
                nodo = OperacionBinaria(op[1], nodo, der)
            else:
                break
        return nodo

    def parse_primario(self):
        t = self.peek()
        if not t:
            raise SyntaxError("Se esperaba una expresión o valor")
            
        if t[1] == '(':
            self.pos += 1
            nodo = self.parse_expresion()
            if not self.match(')'):
                raise SyntaxError("Falta paréntesis de cierre ')' en la expresión")
            return nodo
            
        if t[0] in ['TKN DEC', 'TKN FLO'] or t[1].replace('.', '', 1).isdigit():
            self.pos += 1
            return Numero(t[1])
            
        if t[0] in ['TKN_STRING', 'TKN COMILLA'] or '"' in t[1] or "'" in t[1] or '`' in t[1]:
            self.pos += 1
            return NodoAST('String', t[1])
            
        if t[1] in ['true', 'false', 'nil']:
            self.pos += 1
            return NodoAST('Boolean', t[1])
            
        # Variables or Function Calls
        if t[0] == 'TKN ID' or t[1].isidentifier():
            self.pos += 1
            nodo = Variable(t[1])
            
            # Verificación de llamadas a subfunción / casting
            if self.match('('):
                nodo_llamada = NodoAST('LlamadaFuncion', t[1])
                while self.peek() and self.peek()[1] != ')':
                    arg = self.parse_expresion()
                    nodo_llamada.agregar_hijo(arg)
                    if self.match(','):
                        continue
                    else:
                        break
                if not self.match(')'):
                    raise SyntaxError("Falta paréntesis de cierre ')' en llamada a función")
                return nodo_llamada
                
            return nodo
            
        # Operadores unarios básicos
        if t[1] in ['-', '!', '++', '--']:
            self.pos += 1
            nodo = self.parse_primario()
            return NodoAST('Unario_' + t[1], nodo)
            
        raise SyntaxError(f"Se esperaba una expresión válida pero se encontró '{t[1]}'")
