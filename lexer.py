import re

class AnalizadorLexico:
    def __init__(self):
        self.tokens_fijos = {
            '+': 'TKN OPADD', '-': 'TKN OPSUB', '*': 'TKN OPMULT', '/': 'TKN OPDIV', '%': 'TKN OPMOD',
            '==': 'TKN EQ', '!=': 'TKN NEQ', '<': 'TKN LT', '>': 'TKN GT',
            '<=': 'TKN LTE', '>=': 'TKN GTE',
            '&&': 'TKN AND', '||': 'TKN OR', '!': 'TKN NOT',
            '(': 'TKN PAREN_A', ')': 'TKN PAREN_C', 
            '[': 'TKN CORAPER', ']': 'TKN CORCIERRE',
            '{': 'TKN LLAVE_A', '}': 'TKN LLAVE_C',
            '=': 'TKN ASIGN', ':=': 'TKN WALRUS', ':': 'TKN COLON',
            ',': 'TKN COMMA', '.': 'TKN DOT', ';': 'TKN PUNTO_COMA',
            '&': 'TKN AMPERSAND', '|': 'TKN PIPE', '^': 'TKN XOR',
            '<<': 'TKN LSHIFT', '>>': 'TKN RSHIFT', '&^': 'TKN AND_NOT',
            '<-': 'TKN ARROW', '...': 'TKN ELLIPSIS',
            '"': 'TKN COMILLA', "'": 'TKN COMILLA_SIMPLE',
            '`': 'TKN BACKTICK',
            '×': 'TKN OPMULT'
        }
        
        self.patron = r'===|!==|<=|>=|&&|\|\||<<|>>|&\^|<-|\.\.\.|:=|[%&*+\-/<>=!|:.,;{}()\[\]\'"`]|[a-zA-Z_][\w.]*|\d+\.\d+|\d+'

    def es_identificador_valido(self, token):
        if not token: return False
        return token[0].isalpha() or token[0] == '_'

    def procesar(self, entrada):
        partes_de_la_expresion = re.findall(self.patron, entrada)
        resultado = []
        
        for l in partes_de_la_expresion:
            l = l.strip()
            if not l: continue

            if l in self.tokens_fijos:
                tipo = self.tokens_fijos[l]
            elif l.replace('.', '', 1).isdigit():
                tipo = "TKN NUM"
            elif self.es_identificador_valido(l):
                tipo = "TKN ID"
            else:
                tipo = "TKN ERROR"
            
            resultado.append((tipo, l))
        
        return resultado