from ast_nodes import Numero, OperacionBinaria, Variable, ExpresionParentesis

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
        solo_simbolos = "".join([valor for tipo, valor in tokens if tipo in 
                                 ['TKN PAREN_A', 'TKN PAREN_C', 'TKN CORAPER', 
                                  'TKN CORCIERRE', 'TKN LLAVE_A', 'TKN LLAVE_C']])
        
        return self.validar_apertura_cierres(solo_simbolos) 
    
    def generar_arbol_parseo(self, tokens):
        """Genera el árbol de parseo a partir de los tokens"""
        try:
            valores = [valor for tipo, valor in tokens]
            valores = self._procesar_parentesis(valores)
            ast = self._parsear_expresion_simple(valores)
            if ast:
                return self._formatear_arbol(ast)
            return "No se pudo generar el árbol de parseo"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _procesar_parentesis(self, valores):
        i = 0
        while i < len(valores):
            if valores[i] == '(':
                nivel = 1
                j = i + 1
                while j < len(valores) and nivel > 0:
                    if valores[j] == '(':
                        nivel += 1
                    elif valores[j] == ')':
                        nivel -= 1
                    j += 1
                
                if nivel == 0:
                    expresion_interna = valores[i+1:j-1]
                    expresion_procesada = self._procesar_parentesis(expresion_interna)
                    ast_interno = self._parsear_expresion_simple(expresion_procesada)
                    
                    valores[i:j] = [ast_interno]
                    i -= 1
            i += 1
        
        return valores
    
    def _parsear_expresion_simple(self, valores):
        if not valores:
            return None
        
        i = 0
        while i < len(valores):
            if valores[i] in ['*', '/', '×']:
                if i > 0 and i < len(valores) - 1:
                    if isinstance(valores[i-1], str):
                        if valores[i-1].replace('.', '', 1).isdigit():
                            izquierdo = Numero(valores[i-1])
                        else:
                            izquierdo = Variable(valores[i-1])
                    else:
                        izquierdo = valores[i-1]
                    
                    if isinstance(valores[i+1], str):
                        if valores[i+1].replace('.', '', 1).isdigit():
                            derecho = Numero(valores[i+1])
                        else:
                            derecho = Variable(valores[i+1])
                    else:
                        derecho = valores[i+1]
                    
                    operacion = OperacionBinaria(valores[i], izquierdo, derecho)
                    
                    valores[i-1:i+2] = [operacion]
                    i -= 1
            i += 1
        
        i = 0
        while i < len(valores):
            if valores[i] in ['+', '-']:
                if i > 0 and i < len(valores) - 1:
                    if isinstance(valores[i-1], str):
                        if valores[i-1].replace('.', '', 1).isdigit():
                            izquierdo = Numero(valores[i-1])
                        else:
                            izquierdo = Variable(valores[i-1])
                    else:
                        izquierdo = valores[i-1]
                    
                    if isinstance(valores[i+1], str):
                        if valores[i+1].replace('.', '', 1).isdigit():
                            derecho = Numero(valores[i+1])
                        else:
                            derecho = Variable(valores[i+1])
                    else:
                        derecho = valores[i+1]
                    
                    operacion = OperacionBinaria(valores[i], izquierdo, derecho)
                    
                    valores[i-1:i+2] = [operacion]
                    i -= 1
            i += 1
        
        return valores[0] if valores else None
    
    def _formatear_arbol(self, nodo, nivel=0, prefijo=""):
        if nodo is None:
            return ""
        
        resultado = ""
        indentacion = "    " * nivel
        
        if nodo.tipo == "Numero":
            resultado += f"{indentacion}{prefijo}Numero: {nodo.valor}\n"
        elif nodo.tipo in ["Suma", "Resta", "Multiplica", "Divide"]:
            resultado += f"{indentacion}{prefijo}{nodo.tipo}\n"
            if len(nodo.hijos) >= 2:
                resultado += self._formatear_arbol(nodo.hijos[0], nivel + 1, "├── ")
                resultado += self._formatear_arbol(nodo.hijos[1], nivel + 1, "└── ")
        elif nodo.tipo == "Variable":
            resultado += f"{indentacion}{prefijo}Variable: {nodo.valor}\n"
        elif nodo.tipo == "Parentesis":
            resultado += f"{indentacion}{prefijo}Parentesis\n"
            if nodo.hijos:
                resultado += self._formatear_arbol(nodo.hijos[0], nivel + 1, "└── ")
        else:
            resultado += f"{indentacion}{prefijo}{nodo.tipo}"
            if nodo.valor:
                resultado += f": {nodo.valor}"
            resultado += "\n"
        
        return resultado