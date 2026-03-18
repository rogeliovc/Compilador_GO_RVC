from ast_nodes import Numero, OperacionBinaria, Variable
from errors import agregar_error_patron, agregar_error_estructural
from utils import es_identificador_valido, KEYWORDS_GO

class AnalizadorSintactico:
    def __init__(self):
        self.errores_encontrados = []

        self.pila_llaves = []  
        self.pila_parentesis = []
        self.pila_corchetes = []
        self.errores_archivo = []
        
        self.variables_declaradas = {}  

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
    
    def procesar_linea_archivo(self, tokens, linea_num):
        for i, (tipo, valor) in enumerate(tokens):
            if valor == '{':
                self.pila_llaves.append((valor, linea_num, i))
            elif valor == '}':
                if not self.pila_llaves:
                    self._agregar_error_sin_apertura("Llave", valor, linea_num, i, tokens)
                else:
                    apertura, linea_apertura, pos_apertura = self.pila_llaves.pop()
                    if apertura != '{':
                        self._agregar_error_desbalanceado("Llaves", apertura, valor, linea_num, i, tokens)
            elif valor == '(':
                self.pila_parentesis.append((valor, linea_num, i))
            elif valor == ')':
                if not self.pila_parentesis:
                    self._agregar_error_sin_apertura("Paréntesis", valor, linea_num, i, tokens)
                else:
                    apertura, linea_apertura, pos_apertura = self.pila_parentesis.pop()
                    if apertura != '(':
                        self._agregar_error_desbalanceado("Paréntesis", apertura, valor, linea_num, i, tokens)
            elif valor == '[':
                self.pila_corchetes.append((valor, linea_num, i))
            elif valor == ']':
                if not self.pila_corchetes:
                    self._agregar_error_sin_apertura("Corchete", valor, linea_num, i, tokens)
                else:
                    apertura, linea_apertura, pos_apertura = self.pila_corchetes.pop()
                    if apertura != '[':
                        self._agregar_error_desbalanceado("Corchetes", apertura, valor, linea_num, i, tokens)
    
    def finalizar_archivo(self):
        for simbolo, linea, pos in self.pila_llaves:
            self.errores_archivo.append(f"Línea {linea}: Llave '{simbolo}' sin cerrar al final del archivo")
        
        for simbolo, linea, pos in self.pila_parentesis:
            self.errores_archivo.append(f"Línea {linea}: Paréntesis '{simbolo}' sin cerrar al final del archivo")
        
        for simbolo, linea, pos in self.pila_corchetes:
            self.errores_archivo.append(f"Línea {linea}: Corchete '{simbolo}' sin cerrar al final del archivo")
        
        return len(self.errores_archivo) == 0
    
    def limpiar_estado_archivo(self):
        self.pila_llaves.clear()
        self.pila_parentesis.clear()
        self.pila_corchetes.clear()
        self.errores_archivo.clear()
        self.variables_declaradas.clear()  
    
    def _agregar_error_sin_apertura(self, tipo, valor, linea, pos, tokens):
        contexto = " ".join([t[1] for t in tokens])
        agregar_error_estructural(
            f"{tipo} '{valor}' sin apertura",
            linea,
            pos,
            contexto
        )
        self.errores_archivo.append(f"Línea {linea}: {tipo} '{valor}' sin apertura")
    
    def _agregar_error_desbalanceado(self, tipo, apertura, cierre, linea, pos, tokens):
        contexto = " ".join([t[1] for t in tokens])
        agregar_error_estructural(
            f"{tipo} desbalanceados: se abrió '{apertura}' pero se cerró '{cierre}'",
            linea,
            pos,
            contexto
        )
        self.errores_archivo.append(f"Línea {linea}: {tipo} desbalanceados")

    def limpiar_tokens(self, tokens):
        tokens_limpios = []
        i = 0
        while i < len(tokens):
            tipo, valor = tokens[i]
            
            if tipo == 'TKN OPDIV' and i + 1 < len(tokens) and tokens[i + 1][1] == '/':
                i += 2
                while i < len(tokens) and tokens[i][1] not in ['\n', ';']:
                    i += 1
                continue
            
            if tipo not in ['TKN COMENTARIO']:
                tokens_limpios.append((tipo, valor))
            
            i += 1
        
        return tokens_limpios
    
    def validar_sintaxis_go(self, tokens, linea_num=1, omitir_balance_simbolos=False):
        self.errores_encontrados = []
        
        if not tokens:
            return True
        
        tokens = self.limpiar_tokens(tokens)
        
        if not tokens:
            return True
        
        self.validar_punto_coma(tokens, linea_num)
        self.validar_estructura_sintactica(tokens, linea_num)
        
        if not omitir_balance_simbolos:
            self.validar_balance_simbolos(tokens, linea_num)
        
        self.validar_sintaxis_funcion(tokens, linea_num)
        
        self.validar_operadores(tokens, linea_num)
        
        self.validar_keywords(tokens, linea_num)
        
        return len(self.errores_encontrados) == 0
    
    def validar_punto_coma(self, tokens, linea):
        if not tokens:
            return
        
        ultimo_token = tokens[-1]
        
        if ultimo_token[1] == '}':
            return
        
        linea_completa = " ".join([t[1] for t in tokens])
        
        no_necesitan_punto_coma = [
            'package',
            'import',
            'func',
            'if',
            'for',
            'switch',
            'struct',
            'interface',
            'type'
        ]
        
        if any(linea_completa.startswith(palabra) for palabra in no_necesitan_punto_coma):
            return
        
        if 'func' in linea_completa and '(' in linea_completa and '{' in linea_completa:
            return
        
        if ':=' in linea_completa:
            return
        
        if '=' in linea_completa and ':=' not in linea_completa and not linea_completa.startswith('var'):
            return
        
        if any(palabra in linea_completa for palabra in ['print(', 'fmt.Println(']):
            return
        
        if ultimo_token[1] != ';':
            pass
    
    def validar_estructura_sintactica(self, tokens, linea):
        if not tokens:
            return
        
        if tokens[0][1] == 'var':
            if len(tokens) < 3:
                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron(
                    "Declaración var incompleta - estructura: var nombre tipo [= valor];",
                    linea,
                    0,
                    contexto
                )
                self.errores_encontrados.append(f"Línea {linea}: Estructura var incompleta")
                return
            
            if len(tokens) >= 3:
                nombre = tokens[1][1]
                tipo = tokens[2][1]
                
                if nombre == tipo or nombre == '=' or tipo == '=':
                    contexto = " ".join([t[1] for t in tokens])
                    agregar_error_patron(
                        "Estructura var incorrecta - se espera: var nombre tipo [= valor];",
                        linea,
                        0,
                        contexto
                    )
                    self.errores_encontrados.append(f"Línea {linea}: Estructura var incorrecta")
        
        elif any((t[1] == ':=') for t in tokens):
            pos = next((i for i, t in enumerate(tokens) if (t[1] == ':=')), -1)
            if pos == 0 or pos >= len(tokens) - 1:
                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron(
                    "Declaración corta inválida - estructura: nombre := valor;",
                    linea,
                    0,
                    contexto
                )
                self.errores_encontrados.append(f"Línea {linea}: Estructura := incorrecta")
    
    def validar_balance_simbolos(self, tokens, linea):
        simbolos = "".join([valor for tipo, valor in tokens if tipo in 
                         ['TKN PAREN_A', 'TKN PAREN_C', 'TKN CORAPER', 
                          'TKN CORCIERRE', 'TKN LLAVE_A', 'TKN LLAVE_C']])
        
        if not self.validar_apertura_cierres(simbolos):
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_estructural(
                f"Símbolos desbalanceados en la línea",
                linea,
                0,
                contexto
            )
            self.errores_encontrados.append(f"Línea {linea}: Símbolos desbalanceados")
    
    def validar_sintaxis_funcion(self, tokens, linea):
        if not tokens or tokens[0][1] != 'func':
            return
        
        if len(tokens) < 3:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron(
                "Declaración de función incompleta",
                linea,
                0,
                contexto
            )
            self.errores_encontrados.append(f"Línea {linea}: Función incompleta")
            return
        
        nombre = tokens[1][1]
        if not es_identificador_valido(nombre):
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron(
                f"Nombre de función inválido: '{nombre}'",
                linea,
                tokens[1][2] if len(tokens[1]) > 2 else 0,
                contexto
            )
            self.errores_encontrados.append(f"Línea {linea}: Nombre de función inválido")
        
        tiene_parentesis_a = False
        tiene_parentesis_c = False
        tiene_llave_a = False
        
        for tipo, valor in tokens:
            if valor == '(':
                tiene_parentesis_a = True
            elif valor == ')':
                tiene_parentesis_c = True
            elif valor == '{':
                tiene_llave_a = True
        
        if not tiene_parentesis_a:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron(
                "Faltan paréntesis de apertura en declaración de función",
                linea,
                tokens[2][2] if len(tokens[2]) > 2 else 0,
                contexto
            )
            self.errores_encontrados.append(f"Línea {linea}: Faltan paréntesis de apertura")
        
        if not tiene_parentesis_c:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron(
                "Faltan paréntesis de cierre en declaración de función",
                linea,
                0,
                contexto
            )
            self.errores_encontrados.append(f"Línea {linea}: Faltan paréntesis de cierre")
        
        if not tiene_llave_a:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron(
                "Falta llave de apertura en cuerpo de función",
                linea,
                0,
                contexto
            )
            self.errores_encontrados.append(f"Línea {linea}: Falta llave de apertura")
    
    def validar_operadores(self, tokens, linea):
        for i, token in enumerate(tokens):
            valor = token[1]
            
            if valor in ['+', '-', '*', '/', '+=', '-=', '*=', '/=', '==', '!=', '<', '>', '<=', '>=']:
                if i == 0 or i == len(tokens) - 1:
                    contexto = " ".join([t[1] for t in tokens])
                    agregar_error_patron(
                        f"Operador '{valor}' sin operando",
                        linea,
                        i,
                        contexto
                    )
                    self.errores_encontrados.append(f"Línea {linea}: Operador '{valor}' sin operando")
            
            elif valor in ['++', '--']:
                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron(
                    f"Operador '{valor}' no existe en Go",
                    linea,
                    i,
                    contexto
                )
                self.errores_encontrados.append(f"Línea {linea}: Operador '{valor}' no existe en Go")
    
    def validar_keywords(self, tokens, linea):
        from utils import es_palabra_reservada
        for i, token in enumerate(tokens):
            valor = token[1]
            
            if es_palabra_reservada(valor) and i > 0:
                anterior = tokens[i-1][1]
                if anterior in ['var', 'func', 'type', 'struct']:
                    continue
                elif anterior == '.':
                    continue
                else:
                    contexto = " ".join([t[1] for t in tokens])
                    agregar_error_patron(
                        f"Uso inválido de palabra reservada '{valor}' como identificador",
                        linea,
                        i,
                        contexto
                    )
                    self.errores_encontrados.append(f"Línea {linea}: Keyword '{valor}' usado como identificador")
    
    def obtener_errores(self):
        return self.errores_encontrados
    
    def generar_arbol_parseo(self, tokens):
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
            
        for operadores in [['*', '/', '×'], ['+', '-']]:
            i = 0
            while i < len(valores):
                if valores[i] in operadores:
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
        else:
            resultado += f"{indentacion}{prefijo}{nodo.tipo}"
            if nodo.valor:
                resultado += f": {nodo.valor}"
            resultado += "\n"
        
        return resultado
    
    def validar_archivo_completo(self, codigo_completo):
        self.errores_encontrados = []
        self.limpiar_estado_archivo()
        
        from lexer import AnalizadorLexico
        from semantic import AutomataSemantico
        lexer = AnalizadorLexico()
        analizador_semantico = AutomataSemantico()
        
        lineas = codigo_completo.split('\n')
        errores_totales = []
        
        for i, linea in enumerate(lineas, 1):
            if linea.strip():
                tokens = lexer.procesar(linea.strip(), i)
                
                errores_anteriores = len(errores_totales)
                self.validar_sintaxis_go(tokens, i, omitir_balance_simbolos=True)
                
                errores_totales.extend(self.errores_encontrados[errores_anteriores:])
                
                errores_semanticos = analizador_semantico.validar_declaracion_variable(tokens, i)
                errores_totales.extend(errores_semanticos)
                
                self.procesar_linea_archivo(tokens, i)
        
        self.errores_encontrados = errores_totales
        
        self.finalizar_archivo()
        
        self.errores_encontrados.extend(self.errores_archivo)
        
        total_errores = len(self.errores_encontrados)
        
        return total_errores == 0