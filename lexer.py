import re
from errors import agregar_error_lexico
from utils import es_identificador_valido, KEYWORDS_GO, TIPOS_BASICOS

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
            '+=': 'TKN ADDEQ', '-=': 'TKN SUBEQ', '*=': 'TKN MULTEQ', '/=': 'TKN DIVEQ', '%=': 'TKN MODEQ',
            '&=': 'TKN ANDEQ', '|=': 'TKN OREQ', '^=': 'TKN XOREQ', '&^=': 'TKN ANDNOTEQ',
            '<<=': 'TKN LSHIFTEQ', '>>=': 'TKN RSHIFTEQ',
            '\\': 'TKN ESCAPE',
            '++': 'TKN INC', '--': 'TKN DEC'
        }
        # Se agregaron: \n, comentarios /*...*/, runas '...', números hex y flotantes mejorados
        # Se quitaron: ===, !==
        self.patron = r'\n|/\*[\s\S]*?\*/|//.*|==|!=|<=|>=|&&|\|\||<<|>>|&\^|<-|\.\.\.|:=|\+\=|-\=|\*\=|/\=|%\=|&\=|\|\=|\^\=|&\^\=|<<=|>>=|\+\+|--|"(?:\\.|[^"\\])*"|`[^`]*`|\'(?:\\.|[^\'\\])*\'|[a-zA-Z_áéíóúÁÉÍÓÚñÑ][\wáéíóúÁÉÍÓÚñÑ]*|0[xX][0-9a-fA-F]+|\d*\.\d+|\d+\.\d*|\d+|[%&*+\-/<>=!|:.,;{}()\[\]\'"`\\]'

    def procesar(self, entrada, linea=1):
        
        resultado = []
        posicion_actual = 0
        
        for match in re.finditer(self.patron, entrada):
            inicio, fin = match.span()
            
            # Revisar si hay texto suelto entre el token anterior y este token
            if inicio > posicion_actual:
                no_reconocido = entrada[posicion_actual:inicio]
                for i, char in enumerate(no_reconocido):
                    if not char.isspace():
                        agregar_error_lexico(
                            f"Carácter inválido '{char}'",
                            linea,
                            posicion_actual + i + 1,
                            entrada.strip()
                        )
            
            posicion_actual = fin
            l_raw = match.group(0)
            l = l_raw.strip()
            
            if l_raw == '\n':
                if len(resultado) > 0:
                    ultimo_tipo = resultado[-1][0]
                    tokens_asi = {
                        "TKN ID", "TKN NUM", "TKN STRING", "TKN BREAK", 
                        "TKN CONTINUE", "TKN FALLTHROUGH", "TKN RETURN", 
                        "TKN INC", "TKN DEC", "TKN PAREN_C", "TKN CORCIERRE", "TKN LLAVE_C"
                    }
                    if ultimo_tipo in tokens_asi or ultimo_tipo.replace("TKN ", "").lower() in TIPOS_BASICOS:
                        resultado.append(("TKN PUNTO_COMA", ";", linea))
                linea += 1
                continue
            
            if not l or l.startswith('//') or l.startswith('/*'):
                linea += l_raw.count('\n')
                continue

            # Manejar tokens
            if l in self.tokens_fijos:
                tipo = self.tokens_fijos[l]
                valor = l
            elif l.replace('.', '', 1).isdigit() or l.lower().startswith('0x'):
                tipo = "TKN NUM"
                valor = l
            elif (l.startswith('"') and l.endswith('"')) or (l.startswith('`') and l.endswith('`')) or (l.startswith("'") and l.endswith("'")):
                tipo = "TKN STRING"
                valor = l
                linea += l_raw.count('\n')
            elif l in KEYWORDS_GO:
                tipo = f"TKN {l.upper()}"
                valor = l
            elif l in TIPOS_BASICOS:
                tipo = f"TKN {l.upper()}"
                valor = l
            elif es_identificador_valido(l):
                tipo = "TKN ID"
                valor = l
            else:
                tipo = "TKN ERROR"
                valor = l
                agregar_error_lexico(
                    f"Token no reconocido '{l}'",
                    linea,
                    inicio + 1,
                    entrada.strip()
                )
            
            resultado.append((tipo, valor, linea))

        # Revisar si quedó basura al final del string
        if posicion_actual < len(entrada):
            no_reconocido = entrada[posicion_actual:]
            for i, char in enumerate(no_reconocido):
                if not char.isspace():
                    agregar_error_lexico(
                        f"Carácter inválido '{char}'",
                        linea,
                        posicion_actual + i + 1,
                        entrada.strip()
                    )
        
        # ASI al final del archivo/línea procesada
        if len(resultado) > 0:
            ultimo_tipo = resultado[-1][0]
            tokens_asi = {
                "TKN ID", "TKN NUM", "TKN STRING", "TKN BREAK", 
                "TKN CONTINUE", "TKN FALLTHROUGH", "TKN RETURN", 
                "TKN INC", "TKN DEC", "TKN PAREN_C", "TKN CORCIERRE", "TKN LLAVE_C"
            }
            if ultimo_tipo in tokens_asi or ultimo_tipo.replace("TKN ", "").lower() in TIPOS_BASICOS:
                resultado.append(("TKN PUNTO_COMA", ";", linea))
        
        return resultado