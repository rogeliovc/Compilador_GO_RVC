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
        self.lineas_codigo = []  # Almacenar líneas para verificar bloques vacíos multilínea
        
        self.variables_declaradas = {}
        self.semantic_analyzer = None  # Referencia al analizador semántico para coordinación

    def set_semantic_analyzer(self, semantic_analyzer):
        """Establecer referencia al analizador semántico para coordinación"""
        self.semantic_analyzer = semantic_analyzer
    
    def notificar_bucle_for(self, tokens, linea):
        """Notificar al semantic sobre bucle for detectado para gestión de ámbito"""
        if self.semantic_analyzer:
            self.semantic_analyzer.notificar_bucle_for_detectado(tokens, linea)
    
    def notificar_condicional(self, tokens, linea):
        """Notificar al semantic sobre condicionales detectados para gestión semántica"""
        if self.semantic_analyzer:
            self.semantic_analyzer.notificar_condicional_detectado(tokens, linea)

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
        # Primero procesar aperturas
        for i, (tipo, valor) in enumerate(tokens):
            if valor == '{':
                # Guardar la línea donde se abre la llave y los tokens para verificar después
                self.pila_llaves.append((valor, linea_num, i, tokens))
        
        # Luego procesar cierres
        for i, (tipo, valor) in enumerate(tokens):
            if valor == '}':
                if not self.pila_llaves:
                    self._agregar_error_sin_apertura("Llave", valor, linea_num, i, tokens)
                else:
                    apertura, linea_apertura, pos_apertura, tokens_apertura = self.pila_llaves.pop()
                    if apertura != '{':
                        self._agregar_error_desbalanceado("Llaves", apertura, valor, linea_num, i, tokens)
                    else:
                        # Verificar si es un bloque vacío multilínea
                        if linea_num > linea_apertura:
                            # Verificar si las líneas intermedias están vacías o solo tienen comentarios
                            self._verificar_bloque_vacio_multilinea(linea_apertura, linea_num, tokens_apertura, tokens)
        
        # Continuar con otros símbolos
        for i, (tipo, valor) in enumerate(tokens):
            if valor == '(':
                self.pila_parentesis.append((valor, linea_num, i))
                # No detectar paréntesis vacíos en la misma línea (pueden ser válidos en funciones)
            elif valor == ')':
                if not self.pila_parentesis:
                    self._agregar_error_sin_apertura("Paréntesis", valor, linea_num, i, tokens)
                else:
                    apertura, linea_apertura, pos_apertura = self.pila_parentesis.pop()
                    if apertura != '(':
                        self._agregar_error_desbalanceado("Paréntesis", apertura, valor, linea_num, i, tokens)
            elif valor == '[':
                # Verificar si es parte del patrón []tipo de Go ANTES de agregar a la pila
                es_patron_go = False
                if i + 1 < len(tokens) and tokens[i+1][1] == ']':
                    # Posible patrón []tipo
                    if i + 2 < len(tokens):
                        siguiente_token = tokens[i+2][1]
                        from utils import TIPOS_BASICOS
                        if siguiente_token in TIPOS_BASICOS:
                            es_patron_go = True
                            # No agregar a la pila, es un patrón válido de Go
                            # Marcar que el siguiente corchete de cierre también debe ser ignorado
                            # Usamos una bandera temporal para recordar esto
                            if not hasattr(self, '_ignorar_proximo_corchete_cierre'):
                                self._ignorar_proximo_corchete_cierre = False
                            self._ignorar_proximo_corchete_cierre = True
                            continue
                
                # Si no es patrón []tipo, procesar normalmente
                self.pila_corchetes.append((valor, linea_num, i))
                # Verificar si hay un cierre en la misma línea Y si no hay contenido entre ellos
                for j in range(i+1, len(tokens)):
                    if tokens[j][1] == ']':
                        # Verificar si realmente está vacío (no hay contenido entre [ y ])
                        if self._esta_realmente_vacio(tokens, i, j):
                            # Corchete vacío en la misma línea: []
                            self._agregar_error_bloque_vacio("Corchetes", linea_num, i, tokens)
                        # Remover la apertura de la pila ya que se cerró
                        if self.pila_corchetes:
                            self.pila_corchetes.pop()
                        break
            elif valor == ']':
                # Verificar si debemos ignorar este corchete porque es parte del patrón []tipo
                if hasattr(self, '_ignorar_proximo_corchete_cierre') and self._ignorar_proximo_corchete_cierre:
                    # Es parte del patrón []tipo, ignorar
                    self._ignorar_proximo_corchete_cierre = False
                else:
                    # Procesamiento normal del corchete de cierre
                    if not self.pila_corchetes:
                        self._agregar_error_sin_apertura("Corchete", valor, linea_num, i, tokens)
                    else:
                        apertura, linea_apertura, pos_apertura = self.pila_corchetes.pop()
                        if apertura != '[':
                            self._agregar_error_desbalanceado("Corchetes", apertura, valor, linea_num, i, tokens)
    
    def _agregar_error_bloque_vacio(self, tipo, linea, pos, tokens):
        contexto = " ".join([t[1] for t in tokens])
        from errors import agregar_error_patron
        agregar_error_patron(
            f"Bloque vacío detectado: {tipo.lower()} sin contenido",
            linea,
            pos,
            contexto
        )
        self.errores_archivo.append(f"Línea {linea}: Bloque vacío - {tipo.lower()} sin contenido")
    
    def _verificar_bloque_vacio_multilinea(self, linea_apertura, linea_cierre, tokens_apertura, tokens_cierre):
        """Verifica si un bloque multilínea está vacío"""
        # Verificar si es un bloque significativo
        if not self._es_bloque_significativo(tokens_apertura, 0, len(tokens_apertura)-1):
            return
            
        # Verificar si las líneas intermedias están realmente vacías
        if hasattr(self, 'lineas_codigo') and self.lineas_codigo:
            lineas_intermedias_vacias = True
            # Verificar líneas entre la apertura y el cierre (excluyendo ambas)
            # Las líneas están numeradas desde 1, pero el array desde 0
            for i in range(linea_apertura + 1, linea_cierre):
                if 0 <= i-1 < len(self.lineas_codigo):
                    linea_intermedia = self.lineas_codigo[i-1].strip()
                    # Si la línea no está vacía y no es solo el cierre, el bloque no está vacío
                    if linea_intermedia and linea_intermedia != '}':
                        # Si es un comentario, lo consideramos como contenido válido
                        # (los comentarios son válidos en bloques vacíos)
                        lineas_intermedias_vacias = False
                        break
            
            if lineas_intermedias_vacias:
                contexto = " ".join([t[1] for t in tokens_cierre])
                from errors import agregar_error_patron
                agregar_error_patron(
                    "Bloque vacío detectado: llaves sin contenido en múltiples líneas",
                    linea_cierre,
                    0,
                    contexto
                )
                self.errores_archivo.append(f"Línea {linea_cierre}: Bloque vacío - llaves sin contenido")
    
    def _es_bloque_significativo(self, tokens, pos_apertura, pos_cierre):
        """Determina si un bloque vacío es significativo y no debería estar vacío"""
        # Buscar palabras clave en toda la línea para identificar el tipo de bloque
        for i, token in enumerate(tokens):
            token_valor = token[1].lower()
            if token_valor in ['func', 'for', 'if', 'else', 'switch', 'while', 'struct', 'interface', 'type']:
                return True
        return False
    
    def _esta_realmente_vacio(self, tokens, pos_apertura, pos_cierre):
        """Verifica si realmente no hay contenido entre los símbolos de apertura y cierre"""
        from utils import TIPOS_BASICOS
        
        # EXCEPCIÓN PARA GO: Patrón []tipo (corchetes vacíos seguidos de tipo)
        # Ejemplo: []int, []string, []bool son válidos en Go
        if pos_cierre - pos_apertura == 1:  # Corchetes están juntos: []
            # Verificar si el siguiente token es un tipo válido
            if pos_cierre + 1 < len(tokens):
                siguiente_token = tokens[pos_cierre + 1][1]
                if siguiente_token in TIPOS_BASICOS:
                    return False  # No está vacío, es el patrón []tipo de Go
        
        # Verificar si hay tokens significativos entre apertura y cierre
        for i in range(pos_apertura + 1, pos_cierre):
            if i < len(tokens):
                token = tokens[i][1]
                # Ignorar espacios en blanco, tabulaciones, saltos de línea y comentarios simples
                if token.strip() and token not in [' ', '\t', '\n', '//', '/*', '*/']:
                    # Si hay algo que no sea espacio o comentario, no está vacío
                    # Pero si solo hay espacios, sigue estando vacío
                    if token.strip() not in [' ', '']:
                        # EXCEPCIÓN PARA GO: Si el contenido es un tipo válido, los corchetes vacíos son válidos
                        # Ejemplo: [int] donde int está dentro de los corchetes
                        if token in TIPOS_BASICOS:
                            # Verificar si es el único token entre corchetes
                            if pos_cierre - pos_apertura == 2:  # [ tipo ]
                                return False  # No está vacío, tiene un tipo válido
                            else:
                                # Hay múltiples tokens, verificar si todos son tipos válidos
                                todos_tipos = True
                                for j in range(pos_apertura + 1, pos_cierre):
                                    if j < len(tokens) and tokens[j][1] not in TIPOS_BASICOS:
                                        todos_tipos = False
                                        break
                                if todos_tipos:
                                    return False  # No está vacío, contiene tipos válidos
                        return False
        return True
    
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
        
        self.validar_sintaxis_if(tokens, linea_num)
        
        self.validar_sintaxis_for(tokens, linea_num)
        
        self.validar_operadores(tokens, linea_num)
        
        self.validar_keywords(tokens, linea_num)
        
        self.validar_sintaxis_else(tokens, linea_num)

        self.validar_sintaxis_switch(tokens, linea_num)
        self.validar_sintaxis_case(tokens, linea_num)
        self.validar_sintaxis_default(tokens, linea_num)
        self.validar_sintaxis_return(tokens, linea_num)
        
        return len(self.errores_encontrados) == 0
    
    def validar_punto_coma(self, tokens, linea):
        # Esta validación era heurística y solo hacía "pass" al final.
        # Ahora que el Lexer (ASI) inserta los TKN PUNTO_COMA de manera precisa,
        # dejamos que el AST/Parser estructurado controle dónde era necesario el ';'.
        pass
    
    def validar_estructura_sintactica(self, tokens, linea):
        if not tokens:
            return
        
        if tokens[0][0] == 'TKN VAR':
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
            
            # Verificar si el segundo token no es un ID válido. Permite '(' para var blocks.
            nombre_tkn = tokens[1][0]
            if nombre_tkn != 'TKN ID' and tokens[1][1] != '(':
                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron(
                    "Estructura var incorrecta - se espera: var nombre tipo [= valor];",
                    linea,
                    0,
                    contexto
                )
                self.errores_encontrados.append(f"Línea {linea}: Estructura var incorrecta")
        
        elif any((t[0] == 'TKN WALRUS') for t in tokens):
            pos = next((i for i, t in enumerate(tokens) if (t[0] == 'TKN WALRUS')), -1)
            # ':=' no puede estar al principio (debe haber algo a la izquierda) y debe haber algo a la derecha
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
        if not tokens or tokens[0][0] != 'TKN FUNC':
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

    def validar_sintaxis_else(self, tokens, linea):
        if not tokens: return
        
        # Casos: "else {", "} else {", "} else if ... {" o "else if ... {"
        idx_else = -1
        for i, t in enumerate(tokens):
            if t[1].lower() == 'else':
                idx_else = i
                break
        
        if idx_else == -1: return

        if idx_else > 0 and tokens[idx_else-1][1] != '}':
            pass

        restante = tokens[idx_else+1:]
        if not restante:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron("Estructura else incompleta", linea, idx_else, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Estructura else incompleta")
            return

        # Caso "else {" o "} else {"
        if restante[0][1] == '{':
            if len(restante) > 1 and restante[-1][1] != '{':
                 pass
        # Caso "else if" o "} else if"
        elif restante[0][1] == 'if':
            self.validar_sintaxis_if(restante, linea)
        else:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron("Se esperaba '{' o 'if' después de 'else'", linea, idx_else + 1, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Error después de 'else'")

    def validar_sintaxis_switch(self, tokens, linea):
        from errors import agregar_error_patron  # Importar aquí para evitar problemas de ámbito
        if not tokens or tokens[0][1].lower() != 'switch':
            return
        
        # Notificar al semantic analyzer sobre detección de switch
        self.notificar_condicional(tokens, linea)
        
        if tokens[-1][1] != '{':
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron("Falta llave de apertura '{' al final del switch", linea, len(tokens)-1, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Falta llave en switch")

    def validar_sintaxis_if(self, tokens, linea):
        from errors import agregar_error_patron  # Importar aquí para evitar problemas de ámbito
        if not tokens or tokens[0][1].lower() != 'if':
            return
        
        # Notificar al semantic analyzer sobre detección de if
        self.notificar_condicional(tokens, linea)
        
        if len(tokens) < 2:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron("Estructura if incompleta", linea, 0, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Estructura if incompleta")
            return

        # En Go, los paréntesis son opcionales en el 'if'.
        
        if tokens[-1][1] != '{':
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron("Falta llave de apertura '{' al final del if", linea, len(tokens)-1, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Falta llave de apertura en if")
                
        cond_tokens = tokens[1:-1]
        if any(t[1] == ';' for t in cond_tokens):
            idx = next(i for i, t in enumerate(cond_tokens) if t[1] == ';')
            cond_tokens = cond_tokens[idx+1:]
        
        if cond_tokens:
            try:
                from ast_nodes import ParserExpresiones
                parser_expr = ParserExpresiones(cond_tokens)
                parser_expr.parse()
            except SyntaxError as e:
                msg = f"Error de sintaxis en expresión de 'if' -> {str(e)}"
                from errors import agregar_error_patron
                agregar_error_patron(msg, linea, 0, " ".join([t[1] for t in tokens]))
                self.errores_encontrados.append(f"Línea {linea}: {msg}")
        
        # Se elimina la validación que causaba errores falsos cuando se utilizaba '='
        # en la inicialización de la declaración de bloque if, algo permitido en Go

    def validar_sintaxis_case(self, tokens, linea):
        if not tokens or tokens[0][1].lower() != 'case':
            return
        
        # Notificar al semantic analyzer sobre detección de case
        self.notificar_condicional(tokens, linea)
        
        if tokens[-1][1] != ':':
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron("Faltan dos puntos ':' al final del case", linea, len(tokens)-1, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Falta ':' en case")
        
        if len(tokens) < 3:
            contexto = " ".join([t[1] for t in tokens])
            agregar_error_patron("Estructura case incompleta", linea, 0, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Case incompleto")

    def validar_sintaxis_default(self, tokens, linea):
        if not tokens or tokens[0][1].lower() != 'default':
            return
        
        # Notificar al semantic analyzer sobre detección de default
        self.notificar_condicional(tokens, linea)
        
        if len(tokens) != 2 or tokens[1][1] != ':':
            contexto = " ".join([t[1] for t in tokens])
            from errors import agregar_error_patron  # Importar aquí para evitar problemas de ámbito
            agregar_error_patron("Estructura default incorrecta - se espera: default:", linea, 0, contexto)
            self.errores_encontrados.append(f"Línea {linea}: Estructura default incorrecta")
    
    def validar_sintaxis_return(self, tokens, linea):
        """Valida la sintaxis de la instrucción return"""
        if not tokens:
            return
        
        # Buscar si hay un return en la línea
        for i, (tipo, valor) in enumerate(tokens):
            if valor == 'return':
                # Caso 1: return está al final de la línea sin nada
                if i == len(tokens) - 1:
                    # return está solo al final - esto es un error sintáctico
                    contexto = " ".join([t[1] for t in tokens])
                    from errors import agregar_error_patron
                    agregar_error_patron(f"'return' incompleto, se esperaba una expresión o ';' para función void", linea, i, contexto)
                    self.errores_encontrados.append(f"Línea {linea}: Error sintáctico - 'return' incompleto, se esperaba una expresión o ';' para función void")
                
                # Caso 2: return; (sin valores de retorno)
                elif i == len(tokens) - 2 and tokens[i+1][1] == ';':
                    # return; - válido para funciones void
                    pass
                
                # Caso 3: return <expresion>
                elif i+1 < len(tokens):
                    siguiente_token = tokens[i+1][1]
                    if siguiente_token == ';':
                        # return; - válido pero podría ser un error si la función espera retornar algo
                        pass  # La validación semántica se encargará de verificar si la función debe retornar algo
                    elif siguiente_token in ['}', ')']:
                        # return seguido de cierre de bloque - error
                        contexto = " ".join([t[1] for t in tokens])
                        from errors import agregar_error_patron
                        agregar_error_patron(f"'return' incompleto, se esperaba una expresión antes de '{siguiente_token}'", linea, i, contexto)
                        self.errores_encontrados.append(f"Línea {linea}: Error sintáctico - 'return' incompleto, se esperaba una expresión antes de '{siguiente_token}'")
                    # else: return <expresion> - válido sintácticamente
                
                break
    
    def validar_sintaxis_for(self, tokens, linea):
        from errors import agregar_error_patron  # Importar aquí para evitar problemas de ámbito
        if not tokens: return
        
        if tokens[0][1].lower() == 'for':
            if len(tokens) < 2:
                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron("Estructura for incompleta", linea, 0, contexto)
                self.errores_encontrados.append(f"Línea {linea}: Estructura for incompleta")
                return

            # ERROR: Paréntesis no permitidos alrededor de la condición en Go
            if len(tokens) > 1 and tokens[1][1] == '(':
                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron("Paréntesis no permitidos en bucle for - Go no usa paréntesis alrededor de las condiciones", linea, 1, contexto)
                self.errores_encontrados.append(f"Línea {linea}: ERROR - Paréntesis no permitidos en for")

            # ERROR: Pre-incremento ++i no permitido en Go
            for i, token in enumerate(tokens):
                if token[1] == '++':
                    # Verificar si es pre-incremento (++variable)
                    if i < len(tokens) - 1 and tokens[i+1][0] == 'TKN ID':
                        # Esto es ++variable (pre-incremento)
                        # Verificar que no sea parte de una expresión válida como variable++
                        if i == 0 or tokens[i-1][1] not in ['TKN ID', ')', ']']:
                            contexto = " ".join([t[1] for t in tokens])
                            agregar_error_patron("Pre-incremento no permitido en Go - use post-incremento (variable++)", linea, i, contexto)
                            self.errores_encontrados.append(f"Línea {linea}: ERROR - Pre-incremento ++{tokens[i+1][1]} no permitido")

            if tokens[-1][1] != '{':
                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron("Falta llave de apertura '{' al final del for", linea, len(tokens)-1, contexto)
                self.errores_encontrados.append(f"Línea {linea}: Falta llave de apertura en for")
            
            num_espacios = sum(1 for t in tokens if t[1] == ';')
            if num_espacios not in [0, 2]:
                # Verificar si es el caso específico de falta ; entre inicialización y condición
                if num_espacios == 1:
                    # Buscar patrón: for nombre := valor variable (falta ;)
                    tiene_walrus = any(t[1] == ':=' for t in tokens)
                    if tiene_walrus and len(tokens) >= 6:
                        # Buscar si hay un ID después del valor (sin ; separando)
                        for i in range(2, len(tokens)-2):  # Después de 'for' y antes del final
                            if tokens[i][0] == 'TKN NUM' and i+1 < len(tokens)-2:
                                if tokens[i+1][0] == 'TKN ID':
                                    contexto = " ".join([t[1] for t in tokens])
                                    agregar_error_patron("Estructura for inválida: falta ';' entre inicialización y condición", linea, 0, contexto)
                                    self.errores_encontrados.append(f"Línea {linea}: Falta ';' en 'for' - se requiere separar inicialización y condición")
                                    return

                contexto = " ".join([t[1] for t in tokens])
                agregar_error_patron("Estructura for inválida: se esperan 0 o 2 puntos y comas ';'", linea, 0, contexto)
                self.errores_encontrados.append(f"Línea {linea}: Estructura for inválida (cantidad de ';')")
            else:
                # Construccion y validación del AST
                try:
                    from ast_nodes import ParserExpresiones
                    if num_espacios == 2:
                        partes = []
                        actual = []
                        for t in tokens[1:-1]:
                            if t[1] == ';':
                                partes.append(actual)
                                actual = []
                            else:
                                actual.append(t)
                        partes.append(actual)
                        
                        # Validar que la primera parte del for sea una declaración válida
                        primera_parte = partes[0]
                        if primera_parte:
                            # En Go, la primera parte debe ser una declaración o estar vacía
                            # No puede contener ':' solo (debe ser ':=' para declaración corta)
                            if any(t[0] == 'TKN COLON' for t in primera_parte):
                                contexto = " ".join([t[1] for t in tokens])
                                from errors import agregar_error_patron
                                agregar_error_patron("Sintaxis inválida en 'for': se espera ':=' para declaración corta, no ':'", linea, 0, contexto)
                                self.errores_encontrados.append(f"Línea {linea}: Sintaxis inválida en 'for' - ':' no es válido, use ':='")
                                return
                        
                        cond_tokens = partes[1]
                        
                        # Validar patrón =! en la condición (error sintáctico)
                        for i, token in enumerate(cond_tokens):
                            if token[1] == '=' and i + 1 < len(cond_tokens) and cond_tokens[i+1][1] == '!':
                                contexto = " ".join([t[1] for t in tokens])
                                from errors import agregar_error_patron
                                agregar_error_patron("Operador inválido '=!' detectado - se esperaba '!=' para desigualdad", linea, 0, contexto)
                                self.errores_encontrados.append(f"Línea {linea}: ERROR - Operador '=!' inválido, use '!=' para desigualdad")
                                return
                        
                        tercera_parte = partes[2]
                        # Verificar operadores sueltos sin asignación o sin ser incremento/decremento real
                        operador_simple = next((t for t in tercera_parte if t[1] in ['+', '-', '*', '/']), None)
                        tiene_asig = any(t[1] == '=' or t[1] == ':=' for t in tercera_parte)
                        es_inc_dec = any(t[1] in ['++', '--'] for t in tercera_parte)
                        
                        if operador_simple and not tiene_asig and not es_inc_dec:
                            op = operador_simple[1]
                            contexto = " ".join([t[1] for t in tokens])
                            from errors import agregar_error_patron
                            agregar_error_patron(f"Operador '{op}' incompleto sin operando de cierre en el 'for'", linea, 0, contexto)
                            self.errores_encontrados.append(f"Línea {linea}: Operador '{op}' incompleto (se esperaba i++, i+=1, etc.)")
                            return
                    else:
                        # For como while (condición única) o for-range
                        contenido_for = tokens[1:-1]  # Ignorar 'for' y '{'
                        if contenido_for:
                            # Detectar for-range
                            if any(t[1] == 'range' for t in contenido_for):
                                # Validar estructura for-range
                                range_pos = next(i for i, t in enumerate(contenido_for) if t[1] == 'range')
                                if range_pos == 0:
                                    contexto = " ".join([t[1] for t in tokens])
                                    from errors import agregar_error_patron
                                    agregar_error_patron("Estructura for-range inválida - se requiere: for indice, valor := range coleccion", linea, 0, contexto)
                                    self.errores_encontrados.append(f"Línea {linea}: Estructura for-range inválida")
                                    return
                                elif range_pos > 0:
                                    # Verificar que antes de range haya una declaración válida
                                    pre_range = contenido_for[:range_pos]
                                    if not any(t[1] == ':=' for t in pre_range):
                                        # for range coleccion (sin variables)
                                        pass  # Válido
                                    else:
                                        # for indice, valor := range coleccion
                                        pass  # Válido
                            else:
                                # For como while (condición única)
                                # La condición debe ser una expresión válida
                                parser_expr = ParserExpresiones(contenido_for)
                                parser_expr.parse()
                        else:
                            # For infinito (sin componentes) - válido
                            pass
                        return
                        
                    if cond_tokens:
                        if not any(t[1] == 'range' for t in cond_tokens):
                            parser_expr = ParserExpresiones(cond_tokens)
                            parser_expr.parse()
                    else:
                        # For infinito (sin condición) - válido
                        pass
                        
                except SyntaxError as e:
                    msg = f"Error de sintaxis en expresión de 'for' -> {str(e)}"
                    from errors import agregar_error_patron
                    agregar_error_patron(msg, linea, 0, " ".join([t[1] for t in tokens]))
                    self.errores_encontrados.append(f"Línea {linea}: {msg}")
    
    def validar_operadores(self, tokens, linea):
        for i, token in enumerate(tokens):
            valor = token[1]
            
            if valor in ['+', '-', '*', '/', '+=', '-=', '*=', '/=', '==', '!=', '<', '>', '<=', '>=']:
                sin_operando = False
                
                if i == 0 or i == len(tokens) - 1:
                    sin_operando = True
                elif i + 1 < len(tokens):
                    siguiente = tokens[i+1][1]
                    if siguiente in [';', '{', '}', ')', ']']:
                        sin_operando = True
                        
                if sin_operando:
                    contexto = " ".join([t[1] for t in tokens])
                    agregar_error_patron(
                        f"Operador '{valor}' sin operando",
                        linea,
                        i,
                        contexto
                    )
                    self.errores_encontrados.append(f"Línea {linea}: Operador '{valor}' sin operando")
            
            elif valor in ['++', '--']:
                pass
    
    def validar_keywords(self, tokens, linea):
        from utils import es_palabra_reservada
        for i, token in enumerate(tokens):
            valor = token[1]
            
            if es_palabra_reservada(valor) and i > 0:
                anterior = tokens[i-1][1]
                if anterior in ['var', 'func', 'type', 'struct', '=', ':=', ',', '(', '{', '}', 'else']:
                    continue
                elif anterior == '.':
                    continue
                elif valor in ['range', 'true', 'false', 'nil', 'iota']:
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
    
    def obtener_errores_semanticos(self):
        """Obtiene los errores semánticos detectados durante validar_archivo_completo"""
        return getattr(self, 'errores_semanticos', [])
    
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
        
        # Almacenar las líneas del código para verificar bloques vacíos multilínea
        self.lineas_codigo = codigo_completo.split('\n')
        
        from lexer import AnalizadorLexico
        from semantic import AutomataSemantico
        lexer = AnalizadorLexico()
        analizador_semantico = AutomataSemantico()
        
        lineas = self.lineas_codigo
        errores_totales = []
        
        errores_sintacticos = []
        errores_semanticos_totales = []
        
        for i, linea in enumerate(lineas, 1):
            if linea.strip():
                tokens_raw = lexer.procesar(linea.strip(), i)
                tokens = self.limpiar_tokens(tokens_raw)
                
                if not tokens:
                    continue
                
                # Capturar errores sintácticos por separado
                errores_anteriores = len(self.errores_encontrados)
                self.validar_sintaxis_go(tokens, i, omitir_balance_simbolos=True)
                errores_sintacticos_linea = self.errores_encontrados[errores_anteriores:]
                errores_sintacticos.extend(errores_sintacticos_linea)
                
                # Capturar errores semánticos por separado
                errores_semanticos_linea = analizador_semantico.validar_declaracion_variable(tokens, i)
                errores_semanticos_totales.extend(errores_semanticos_linea)
                
                # Validar y registrar importaciones directamente
                if (len(tokens) >= 2 and tokens[0][1] == "import" and tokens[1][0] == "TKN STRING"):
                    paquete = tokens[1][1].strip('"').strip('`')
                    from symbol_table import Simbolo, TipoSimbolo
                    simbolo = Simbolo(paquete, TipoSimbolo.PALABRA_RESERVADA, "import", 0, analizador_semantico.tabla_simbolos.ambito_actual)
                    if not analizador_semantico.tabla_simbolos.existe_simbolo(paquete):
                        analizador_semantico.tabla_simbolos.agregar_simbolo(simbolo)
                
                # Validar llamadas a función (errores semánticos)
                errores_funcion_linea = analizador_semantico.validar_llamada_funcion(tokens, i)
                errores_semanticos_totales.extend(errores_funcion_linea)
                
                self.procesar_linea_archivo(tokens, i)
        
        # Solo guardar errores sintácticos en self.errores_encontrados
        self.errores_encontrados = errores_sintacticos
        
        # Guardar errores semánticos en un atributo separado para uso posterior
        self.errores_semanticos = errores_semanticos_totales
        
        self.finalizar_archivo()
        
        self.errores_encontrados.extend(self.errores_archivo)
        
        total_errores = len(self.errores_encontrados)
        
        return total_errores == 0