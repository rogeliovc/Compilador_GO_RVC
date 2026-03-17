import re
from errors import agregar_error_lexico

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
            '×': 'TKN OPMULT',
            '+=': 'TKN ADDEQ', '-=': 'TKN SUBEQ', '*=': 'TKN MULTEQ', '/=': 'TKN DIVEQ', '%=': 'TKN MODEQ',
            '&=': 'TKN ANDEQ', '|=': 'TKN OREQ', '^=': 'TKN XOREQ', '&^=': 'TKN ANDNOTEQ',
            '<<=': 'TKN LSHIFTEQ', '>>=': 'TKN RSHIFTEQ',
            '++': 'TKN INC', '--': 'TKN DEC'
        }
        
        self.patron = r'===|!==|<=|>=|&&|\|\||<<|>>|&\^|<-|\.\.\.|:=|\+\=|-\=|\*\=|/\=|%\=|&\=|\|\=|\^\=|&\^\=|<<=|>>=|\+\+|--|[%&*+\-/<>=!|:.,;{}()\[\]\'"`]|[a-zA-Z_][\w.]*|\d+\.\d+|\d+'

    def es_identificador_valido(self, token):
        if not token: return False
        return token[0].isalpha() or token[0] == '_'

    def procesar(self, entrada, linea=1):
        partes_de_la_expresion = re.findall(self.patron, entrada)
        resultado = []
        
        texto_reconocido = ''.join(partes_de_la_expresion)
        if texto_reconocido != entrada:
            for i, char in enumerate(entrada):
                if char not in texto_reconocido and not char.isspace():
                    agregar_error_lexico(
                        f"Carácter inválido '{char}'",
                        linea,
                        i + 1,
                        entrada.strip()
                    )
        
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
                agregar_error_lexico(
                    f"Token no reconocido '{l}'",
                    linea,
                    entrada.find(l) + 1,
                    entrada.strip()
                )
            
            resultado.append((tipo, l))
        
        return resultado