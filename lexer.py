# lexer.py
import re

class AnalizadorLexico:
    def __init__(self):
        # Diccionario de lexemas (Tu código original)
        self.tokens_fijos = {
            '+': 'TKN OPADD', '-': 'TKN OPSUB', '*': 'TKN OPMULT', '/': 'TKN OPDIV',
            '(': 'TKN PAREN_A', ')': 'TKN PAREN_C', '[': 'TKN CORAPER', ']': 'TKN CORCIERRE',
            '{': 'TKN LLAVE_A', '}': 'TKN LLAVE_C',
            '=': 'TKN ASIGN', '"': 'TKN COMILLA',
            '×': 'TKN OPMULT' # Añadido de tu bloque main
        }
        # Tipos de datos válidos (Extraído de tu Automata para el Lexer)
        self.tipos_datos = {'int', 'double', 'str', 'bool'}
        
        # Patrón regex para separar la expresion (Tu código original)
        self.patron = r'[a-zA-Z]:|\d+\.\d+|[a-zA-Z_][\w.]*|\d+|[^\w\s]'

    def es_identificador_valido(self, token):
        # Lógica de validación rápida de ID
        if not token: return False
        return token[0].isalpha() or token[0] == '_'

    def procesar(self, entrada):
        partes_de_la_expresion = re.findall(self.patron, entrada)
        resultado = []
        
        for l in partes_de_la_expresion:
            l = l.strip()
            if not l: continue

            # Clasificación segun el TKN
            if l in self.tokens_fijos:
                tipo = self.tokens_fijos[l]
            elif l.lower() in self.tipos_datos:
                tipo = "TKN TIPO_DATO"
            elif l.replace('.', '', 1).isdigit():
                tipo = "TKN NUM"
            elif self.es_identificador_valido(l):
                tipo = "TKN ID"
            else:
                tipo = "TKN ERROR"
            
            resultado.append((tipo, l))
        
        return resultado