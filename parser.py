from ast_nodes import (
    Programa, Bloque, DeclaracionVariable, Asignacion, If, For, 
    Switch, Case, Funcion, Return, Import, Numero, OperacionBinaria, Variable,
    ParserExpresiones
)
from errors import agregar_error_patron
from utils import es_identificador_valido, KEYWORDS_GO

class AnalizadorSintactico:
    def __init__(self):
        self.errores_encontrados = []
        self.tokens = []
        self.pos = 0

    def set_semantic_analyzer(self, semantic_analyzer):
        pass

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def avanzar(self):
        t = self.peek()
        if t: self.pos += 1
        return t

    def match_valor(self, valor_esperado):
        t = self.peek()
        if t and t[1] == valor_esperado:
            self.pos += 1
            return t
        return None

    def match_tipo(self, tipo_esperado):
        t = self.peek()
        if t and t[0] == tipo_esperado:
            self.pos += 1
            return t
        return None

    def limpiar_tokens(self, tokens):
        tokens_limpios = []
        i = 0
        while i < len(tokens):
            tipo, valor = tokens[i][:2]
            linea = tokens[i][2] if len(tokens[i]) > 2 else 0
            if tipo == 'TKN OPDIV' and i + 1 < len(tokens) and tokens[i + 1][1] == '/':
                i += 2
                while i < len(tokens) and tokens[i][1] not in ['\n', ';']:
                    i += 1
                continue
            if tipo not in ['TKN COMENTARIO']:
                tokens_limpios.append((tipo, valor, linea))
            i += 1
        return tokens_limpios

    def agregar_error(self, mensaje, linea):
        self.errores_encontrados.append(f"Línea {linea}: ERROR SINTÁCTICO - {mensaje}")
        from errors import agregar_error_estructural
        agregar_error_estructural(mensaje, linea)

    def obtener_errores(self):
        return self.errores_encontrados

    def parsear_programa(self, tokens):
        self.tokens = self.limpiar_tokens(tokens)
        self.pos = 0
        self.errores_encontrados = []
        
        # Obtenemos la línea inicial para el programa
        linea_prog = self.tokens[0][2] if self.tokens else 0
        programa = Programa(linea_prog)

        while self.pos < len(self.tokens):
            if self.peek() and self.peek()[1] == ';':
                self.avanzar()
                continue
                
            try:
                sentencia = self.parsear_sentencia()
                if sentencia:
                    programa.agregar_hijo(sentencia)
            except SyntaxError as e:
                t = self.peek()
                linea = t[2] if t else 0
                self.agregar_error(str(e), linea)
                self.avanzar()
                while self.peek() and self.peek()[1] not in [';', '}', '{']:
                    self.avanzar()

        return programa

    def parsear_sentencia(self):
        t = self.peek()
        if not t: return None

        valor = t[1]
        if valor == 'var':
            return self.parsear_declaracion_var()
        elif valor == 'if':
            return self.parsear_if()
        elif valor == 'for':
            return self.parsear_for()
        elif valor == 'switch':
            return self.parsear_switch()
        elif valor == 'func':
            return self.parsear_funcion()
        elif valor == 'return':
            return self.parsear_return()
        elif valor == 'import':
            return self.parsear_import()
        elif valor == 'package':
            return self.parsear_package()
        elif valor == '{':
            return self.parsear_bloque()
        else:
            return self.parsear_asignacion_o_expresion()

    def parsear_import(self):
        t_import = self.match_valor('import')
        linea = t_import[2]
        
        t_str = self.match_tipo('TKN STRING')
        if not t_str:
            self.agregar_error("Importación inválida, se espera: import \"paquete\"", linea)
            return None
        
        paquete = t_str[1].strip('"').strip('`')
        return Import(paquete, linea)

    def parsear_package(self):
        t_pkg = self.match_valor('package')
        linea = t_pkg[2]
        
        t_id = self.match_tipo('TKN ID')
        if not t_id:
            self.agregar_error("Se espera un identificador después de 'package'", linea)
            return None
            
        nombre = t_id[1]
        # Creamos un nodo generico o uno especial. Como no hay Package node en ast_nodes, crearemos Variable temporal o uno nuevo?
        # En ast_nodes no hemos creado Package. Podemos importar un nuevo nodo o reutilizar Import
        from ast_nodes import NodoAST
        class Package(NodoAST):
            def __init__(self, nombre, linea=0):
                super().__init__("Package", nombre, linea)
        return Package(nombre, linea)

    def parsear_declaracion_var(self):
        t_var = self.match_valor('var')
        linea = t_var[2]
        
        id_token = self.match_tipo('TKN ID')
        if not id_token:
            self.agregar_error("Se esperaba un identificador después de 'var'", linea)
            return None

        nombre = id_token[1]
        tipo_dato = None

        t = self.peek()
        if t and (t[0] in ['TKN ID'] or t[1] in ['int', 'float64', 'string', 'bool']):
            tipo_dato = t[1]
            self.avanzar()

        expresion_valor = None
        
        if self.match_valor('='):
            parser_expr = ParserExpresiones(self.tokens[self.pos:])
            try:
                expresion_valor = parser_expr.parse_expresion()
                self.pos += parser_expr.pos 
            except SyntaxError as e:
                self.agregar_error(f"Error en la expresión: {str(e)}", linea)

        if not tipo_dato and not expresion_valor:
            self.agregar_error(f"Declaración de '{nombre}' incompleta: falta tipo o asignación", linea)

        return DeclaracionVariable(nombre, tipo_dato, expresion_valor, linea)

    def parsear_asignacion_o_expresion(self):
        pos_inicial = self.pos
        t_actual = self.peek()
        if not t_actual: return None
        linea = t_actual[2]
        
        izquierdos = []
        parser_expr = ParserExpresiones(self.tokens[self.pos:])
        try:
            izquierdos.append(parser_expr.parse_primario())
            self.pos += parser_expr.pos
            
            while self.match_valor(','):
                parser_expr_der = ParserExpresiones(self.tokens[self.pos:])
                izquierdos.append(parser_expr_der.parse_primario())
                self.pos += parser_expr_der.pos
                
            izquierdo = izquierdos[0]
            
            if self.match_valor('='):
                parser_expr_der = ParserExpresiones(self.tokens[self.pos:])
                derecho = parser_expr_der.parse_expresion()
                self.pos += parser_expr_der.pos
                asig = Asignacion(izquierdo, derecho, linea)
                if len(izquierdos) > 1:
                    asig.multiples_izquierdos = izquierdos
                return asig
                
            elif self.match_valor(':='):
                for izq in izquierdos:
                    if izq.tipo != "Variable":
                        self.agregar_error("A la izquierda de ':=' debe haber un identificador válido", linea)
                        return None
                    
                parser_expr_der = ParserExpresiones(self.tokens[self.pos:])
                derecho = parser_expr_der.parse_expresion()
                self.pos += parser_expr_der.pos
                decl = DeclaracionVariable(izquierdo.valor, "inferido", derecho, linea)
                if len(izquierdos) > 1:
                    decl.multiples_valores = [izq.valor for izq in izquierdos]
                return decl
            
            elif self.match_valor('++') or self.match_valor('--'):
                # t_post could be checked before advancing, but match_valor already advanced. 
                # Let's peek backwards to see what it was:
                op_val = self.tokens[self.pos-1][1]
                op = '+' if op_val == '++' else '-'
                derecho = OperacionBinaria(op, izquierdo, Numero("1", linea), linea)
                return Asignacion(izquierdo, derecho, linea)
            
            elif t_compound := (self.match_tipo('TKN ADDEQ') or self.match_tipo('TKN SUBEQ') or self.match_tipo('TKN MULTEQ') or self.match_tipo('TKN DIVEQ') or self.match_tipo('TKN MODEQ')):
                # +=, -=, *=, /=, %=
                parser_expr_der = ParserExpresiones(self.tokens[self.pos:])
                derecho_expr = parser_expr_der.parse_expresion()
                self.pos += parser_expr_der.pos
                op = t_compound[1][0] # Toma el primer caracter (+, -, *, /, %)
                derecho = OperacionBinaria(op, izquierdo, derecho_expr, linea)
                return Asignacion(izquierdo, derecho, linea)

            return izquierdo
            
        except SyntaxError as e:
            self.pos = pos_inicial
            t_err = self.avanzar()
            self.agregar_error(f"Sintaxis inválida cerca de '{t_err[1]}'", t_err[2])
            return None

    def parsear_bloque(self):
        t_llave = self.match_valor('{')
        if not t_llave: return None
        linea = t_llave[2]
        bloque = Bloque(linea)
        
        while self.peek() and self.peek()[1] != '}':
            if self.peek()[1] == ';':
                self.avanzar()
                continue
            
            sentencia = self.parsear_sentencia()
            if sentencia:
                bloque.agregar_hijo(sentencia)
            else:
                self.avanzar()
                
        t_cierre = self.match_valor('}')
        if not t_cierre:
            self.agregar_error("Falta llave de cierre '}'", linea)
            
        return bloque

    def parsear_if(self):
        t_if = self.match_valor('if')
        linea = t_if[2]
        
        cond_tokens = []
        while self.peek() and self.peek()[1] != '{':
            cond_tokens.append(self.avanzar())
            
        if not cond_tokens:
            self.agregar_error("Estructura if incompleta, falta condición", linea)
            return None
            
        parser_expr = ParserExpresiones(cond_tokens)
        try:
            condicion = parser_expr.parse_expresion()
        except SyntaxError as e:
            self.agregar_error(f"Error en condición if: {str(e)}", linea)
            condicion = None
            
        bloque_true = self.parsear_bloque()
        bloque_false = None
        
        if self.match_valor('else'):
            if self.peek() and self.peek()[1] == 'if':
                bloque_false = self.parsear_if()
            elif self.peek() and self.peek()[1] == '{':
                bloque_false = self.parsear_bloque()
            else:
                self.agregar_error("Se esperaba '{' o 'if' después de 'else'", linea)
                
        return If(condicion, bloque_true, bloque_false, linea)

    def parsear_for(self):
        t_for = self.match_valor('for')
        linea = t_for[2]
        
        for_tokens = []
        while self.peek() and self.peek()[1] != '{':
            for_tokens.append(self.avanzar())
            
        if len(for_tokens) > 0 and for_tokens[0][1] == '(':
            self.agregar_error("Paréntesis no permitidos en bucle for - Go no usa paréntesis alrededor de las condiciones", linea)
            
        for i, token in enumerate(for_tokens):
            if token[1] == '++':
                if i < len(for_tokens) - 1 and for_tokens[i+1][0] == 'TKN ID':
                    if i == 0 or for_tokens[i-1][1] not in ['TKN ID', ')', ']']:
                        self.agregar_error("Pre-incremento no permitido en Go - use post-incremento (variable++)", linea)
        
        num_espacios = sum(1 for t in for_tokens if t[1] == ';')
        
        init = None
        cond = None
        post = None
        
        if num_espacios == 2:
            partes = []
            actual = []
            for t in for_tokens:
                if t[1] == ';':
                    partes.append(actual)
                    actual = []
                else:
                    actual.append(t)
            partes.append(actual)
            
            if partes[0]:
                if any(t[0] == 'TKN COLON' for t in partes[0]):
                    self.agregar_error("Sintaxis inválida en 'for' - ':' no es válido, use ':='", linea)
                else:
                    old_tokens, old_pos = self.tokens, self.pos
                    self.tokens = partes[0]
                    self.pos = 0
                    init = self.parsear_asignacion_o_expresion()
                    self.tokens, self.pos = old_tokens, old_pos

            if partes[1]:
                p_cond = ParserExpresiones(partes[1])
                try:
                    cond = p_cond.parse_expresion()
                except SyntaxError:
                    pass
                    
            if partes[2]:
                old_tokens, old_pos = self.tokens, self.pos
                self.tokens = partes[2]
                self.pos = 0
                post = self.parsear_asignacion_o_expresion()
                self.tokens, self.pos = old_tokens, old_pos

        elif num_espacios == 0 and len(for_tokens) > 0:
            p_cond = ParserExpresiones(for_tokens)
            try:
                cond = p_cond.parse_expresion()
            except SyntaxError:
                pass
        elif num_espacios != 0:
            self.agregar_error("Estructura for inválida: se esperan 0 o 2 puntos y comas ';'", linea)

        bloque = self.parsear_bloque()
        return For(init, cond, post, bloque, linea)

    def parsear_switch(self):
        t_switch = self.match_valor('switch')
        linea = t_switch[2]
        
        switch_tokens = []
        while self.peek() and self.peek()[1] != '{':
            switch_tokens.append(self.avanzar())
            
        expresion = None
        if switch_tokens:
            p_expr = ParserExpresiones(switch_tokens)
            try:
                expresion = p_expr.parse_expresion()
            except SyntaxError as e:
                self.agregar_error(f"Error en expresión switch: {str(e)}", linea)

        t_llave = self.match_valor('{')
        if not t_llave:
            self.agregar_error("Falta llave de apertura '{' al final del switch", linea)
            return None
            
        casos = []
        while self.peek() and self.peek()[1] != '}':
            if self.peek()[1] in ['case', 'default']:
                casos.append(self.parsear_case())
            else:
                t_err = self.avanzar()
                if t_err[1] != ';':
                    self.agregar_error(f"Token inesperado '{t_err[1]}' dentro de switch, se esperaba 'case' o 'default'", t_err[2])
                    
        self.match_valor('}')
        return Switch(expresion, casos, linea)

    def parsear_case(self):
        t = self.avanzar()
        linea = t[2]
        es_default = (t[1] == 'default')
        
        exprs = []
        if not es_default:
            case_tokens = []
            while self.peek() and self.peek()[1] not in [':', '{']:
                case_tokens.append(self.avanzar())
                
            if not case_tokens:
                self.agregar_error("Case sin expresión", linea)
            else:
                for i in range(len(case_tokens) - 1):
                    ta = case_tokens[i]
                    tb = case_tokens[i+1]
                    if ta[0] in ['TKN ID', 'TKN NUM'] and tb[0] in ['TKN ID', 'TKN NUM']:
                        self.agregar_error(f"Case inválido - falta operador entre '{ta[1]}' y '{tb[1]}'", linea)

                p_expr = ParserExpresiones(case_tokens)
                try:
                    exprs.append(p_expr.parse_expresion())
                except SyntaxError:
                    pass

        t_colon = self.match_valor(':')
        if not t_colon:
            self.agregar_error("Faltan dos puntos ':' al final del case/default", linea)
            
        bloque_linea = self.peek()[2] if self.peek() else linea
        bloque = Bloque(bloque_linea)
        
        while self.peek() and self.peek()[1] not in ['case', 'default', '}']:
            if self.peek()[1] == ';':
                self.avanzar()
                continue
            s = self.parsear_sentencia()
            if s:
                bloque.agregar_hijo(s)
                
        return Case(exprs, bloque, es_default, linea)

    def parsear_funcion(self):
        t_func = self.match_valor('func')
        linea = t_func[2]
        
        t_id = self.match_tipo('TKN ID')
        if not t_id:
            self.agregar_error("Falta identificador en declaración de función", linea)
            return None
            
        nombre = t_id[1]
        
        t_paren = self.match_valor('(')
        if not t_paren:
            self.agregar_error("Faltan paréntesis de apertura en declaración de función", linea)
            
        parametros = []
        while self.peek() and self.peek()[1] != ')':
            p_id = self.match_tipo('TKN ID')
            if not p_id:
                t_err = self.avanzar()
                self.agregar_error(f"Se esperaba un identificador para el parámetro, se encontró '{t_err[1]}'", linea)
                break
                
            if self.peek() and self.peek()[1] in [',', ')']:
                self.agregar_error(f"Falta el tipo de dato para el parámetro '{p_id[1]}'", linea)
                p_tipo = (None, "desconocido", linea)
            else:
                p_tipo = self.avanzar()
                
            if p_id and p_tipo:
                parametros.append((p_id[1], p_tipo[1]))
            
            if self.peek() and self.peek()[1] == ',':
                self.avanzar()
                
        t_paren_c = self.match_valor(')')
        if not t_paren_c:
            self.agregar_error("Faltan paréntesis de cierre en declaración de función", linea)
            
        tipo_retorno = None
        if self.peek() and self.peek()[1] != '{':
            if self.peek()[1] == '(':
                tokens_retorno = []
                while self.peek() and self.peek()[1] != '{':
                    tokens_retorno.append(self.avanzar()[1])
                tipo_retorno = "".join(tokens_retorno)
            else:
                tipo_retorno = self.avanzar()[1]
            
        bloque = self.parsear_bloque()
        if not bloque:
            self.agregar_error("Falta llave de apertura en cuerpo de función", linea)
            
        return Funcion(nombre, parametros, tipo_retorno, bloque, linea)

    def parsear_return(self):
        t_ret = self.match_valor('return')
        linea = t_ret[2]
        
        expr = None
        if self.peek() and self.peek()[1] not in [';', '}']:
            expr_tokens = []
            while self.peek() and self.peek()[1] not in [';', '}']:
                expr_tokens.append(self.avanzar())
            if expr_tokens:
                p_expr = ParserExpresiones(expr_tokens)
                try:
                    expr = p_expr.parse_expresion()
                except SyntaxError as e:
                    self.agregar_error(f"Error en return: {str(e)}", linea)
        
        return Return(expr, linea)