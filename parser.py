# parser.py

class AnalizadorSintactico:
    def __init__(self):
        pass

    # Validación para (), [], {} (Tu código original exacto)
    def validar_apertura_cierres(self, entrada):
        pila = []
        pares = {')': '(', ']': '[', '}': '{'}
        
        for caracter in entrada:
            if caracter in pares.values():
                pila.append(caracter)
            elif caracter in pares.keys():
                if not pila or pila.pop() != pares[caracter]:
                    return False
        return len(pila) == 0
        
    def procesar_tokens(self, tokens):
        # Aquí reconstruimos los símbolos agrupados para pasarlos a tu validador
        solo_simbolos = "".join([valor for tipo, valor in tokens if tipo in 
                                 ['TKN PAREN_A', 'TKN PAREN_C', 'TKN CORAPER', 
                                  'TKN CORCIERRE', 'TKN LLAVE_A', 'TKN LLAVE_C']])
        
        return self.validar_apertura_cierres(solo_simbolos) 