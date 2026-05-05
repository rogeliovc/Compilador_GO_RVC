from ast_nodes import (
    Programa, Bloque, DeclaracionVariable, Asignacion, If, For, 
    Switch, Case, Funcion, Return, Import, Numero, OperacionBinaria, Variable,
    LlamadaFuncion, Break, Continue, ArrayAccess, StringLiteral, BooleanLiteral,
    AttributeAccess, OperacionUnaria, NodoAST
)
from errors import agregar_error_patron
from utils import es_identificador_valido, KEYWORDS_GO

class Package(NodoAST):
    def __init__(self, nombre, linea=0):
        super().__init__("Package", nombre, linea)

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

    def consumir(self, valor_esperado, mensaje_error=None):
        t = self.match_valor(valor_esperado)
        if t: return t
        
        t_actual = self.peek()
        # Intentar obtener línea del token actual o del anterior si estamos al final
        linea = t_actual[2] if t_actual else (self.tokens[-1][2] if self.tokens else 0)
        msg = mensaje_error or f"Se esperaba '{valor_esperado}'"
        raise SyntaxError(msg)

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
                    
                    t_sig = self.peek()
                    # Si el siguiente token está en la misma línea y no es un separador válido, es error
                    if t_sig and t_sig[1] not in [';', '}', 'case', 'default']:
                        if t_sig[2] == sentencia.linea:
                             self.agregar_error(f"Se esperaba ';' o fin de línea después de la sentencia, pero se encontró '{t_sig[1]}'", t_sig[2])
                             # Consumir hasta el siguiente punto de sincronización para evitar cascada
                             while self.peek() and self.peek()[1] not in [';', '}', '{'] and self.peek()[2] == t_sig[2]:
                                 self.avanzar()
                            
            except SyntaxError as e:
                t = self.peek()
                linea = t[2] if t else 0
                self.agregar_error(str(e), linea)
                self.avanzar()
                while self.peek() and self.peek()[1] not in [';', '}', '{']:
                    self.avanzar()

        return programa

    # --- LÓGICA DE EXPRESIONES (UNIFICADA) ---

    def parsear_expresion(self):
        return self.parsear_or()

    def parsear_or(self):
        nodo = self.parsear_and()
        while self.peek() and self.peek()[1] == '||':
            op = self.avanzar()
            der = self.parsear_and()
            nodo = OperacionBinaria(op[1], nodo, der, op[2])
        return nodo

    def parsear_and(self):
        nodo = self.parsear_igualdad()
        while self.peek() and self.peek()[1] == '&&':
            op = self.avanzar()
            der = self.parsear_igualdad()
            nodo = OperacionBinaria(op[1], nodo, der, op[2])
        return nodo

    def parsear_igualdad(self):
        nodo = self.parsear_comparacion()
        while self.peek() and self.peek()[1] in ['==', '!=']:
            op = self.avanzar()
            der = self.parsear_comparacion()
            nodo = OperacionBinaria(op[1], nodo, der, op[2])
        return nodo

    def parsear_comparacion(self):
        nodo = self.parsear_termino()
        while self.peek() and self.peek()[1] in ['<', '>', '<=', '>=']:
            op = self.avanzar()
            der = self.parsear_termino()
            nodo = OperacionBinaria(op[1], nodo, der, op[2])
        return nodo

    def parsear_termino(self):
        nodo = self.parsear_factor()
        while self.peek() and self.peek()[1] in ['+', '-']:
            op = self.avanzar()
            der = self.parsear_factor()
            nodo = OperacionBinaria(op[1], nodo, der, op[2])
        return nodo

    def parsear_factor(self):
        nodo = self.parsear_unario()
        while self.peek() and self.peek()[1] in ['*', '/', '%']:
            op = self.avanzar()
            der = self.parsear_unario()
            nodo = OperacionBinaria(op[1], nodo, der, op[2])
        return nodo

    def parsear_unario(self):
        t = self.peek()
        if t and t[1] in ['-', '!', '*', '&']:
            self.avanzar()
            operando = self.parsear_unario()
            return OperacionUnaria(t[1], operando, t[2])
        return self.parsear_primario()

    def parsear_primario(self):
        t = self.peek()
        if not t:
            raise SyntaxError("Se esperaba una expresión o valor")
            
        linea = t[2]
        nodo = None
        
        if t[1] == '(':
            self.avanzar()
            nodo = self.parsear_expresion()
            self.consumir(')', "Falta paréntesis de cierre ')'")
        elif t[0] in ['TKN NUM', 'TKN DEC', 'TKN FLO'] or t[1].replace('.', '', 1).isdigit():
            self.avanzar()
            nodo = Numero(t[1], linea)
        elif t[0] in ['TKN STRING', 'TKN COMILLA'] or '"' in t[1] or "'" in t[1] or '`' in t[1]:
            self.avanzar()
            nodo = StringLiteral(t[1], linea)
        elif t[1] in ['true', 'false', 'nil']:
            self.avanzar()
            nodo = BooleanLiteral(t[1], linea)
        elif t[0] == 'TKN ID' or t[1].isidentifier():
            self.avanzar()
            nodo = Variable(t[1], linea)
            
        if not nodo:
            raise SyntaxError(f"Se esperaba una expresión válida pero se encontró '{t[1]}'")
            
        # Sufijos (Llamadas, Accesos, Índices)
        while self.peek():
            sig = self.peek()
            if sig[1] == '.':
                self.avanzar()
                attr = self.match_tipo('TKN ID')
                if attr:
                    nodo = AttributeAccess(nodo, attr[1], sig[2])
                else:
                    raise SyntaxError("Se esperaba un identificador después de '.'")
            elif sig[1] == '(':
                self.avanzar()
                args = []
                while self.peek() and self.peek()[1] != ')':
                    args.append(self.parsear_expresion())
                    if not self.match_valor(','): break
                self.consumir(')', "Falta ')' en llamada a función")
                nodo = LlamadaFuncion(nodo, args, sig[2])
            elif sig[1] == '[':
                self.avanzar()
                indice = self.parsear_expresion()
                self.consumir(']', "Falta ']' en acceso a arreglo")
                nodo = ArrayAccess(nodo, indice, sig[2])
            else:
                break
        return nodo

    # --- LÓGICA DE SENTENCIAS ---

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
        elif valor == 'break':
            return self.parsear_break()
        elif valor == 'continue':
            return self.parsear_continue()
        elif valor == '{':
            return self.parsear_bloque()
        else:
            return self.parsear_asignacion_o_expresion()

    def parsear_import(self):
        t_import = self.match_valor('import')
        t_str = self.match_tipo('TKN STRING')
        if not t_str:
            self.agregar_error("Importación inválida", t_import[2])
            return None
        return Import(t_str[1].strip('"').strip('`'), t_import[2])

    def parsear_package(self):
        t_pkg = self.match_valor('package')
        t_id = self.match_tipo('TKN ID')
        if not t_id:
            self.agregar_error("Se espera un identificador después de 'package'", t_pkg[2])
            return None
        return Package(t_id[1], t_pkg[2])

    def parsear_declaracion_var(self):
        t_var = self.match_valor('var')
        
        nombres = []
        id_token = self.match_tipo('TKN ID')
        if not id_token:
            self.agregar_error("Se esperaba un identificador después de 'var'", t_var[2])
            return None
        nombres.append(id_token[1])
        
        while self.match_valor(','):
            id_token = self.match_tipo('TKN ID')
            if not id_token:
                self.agregar_error("Se esperaba un identificador después de ','", t_var[2])
                break
            nombres.append(id_token[1])

        tipo_dato = self.parsear_tipo_dato()
        expresiones = []
        
        if self.match_valor('='):
            expresiones.append(self.parsear_expresion())
            while self.match_valor(','):
                expresiones.append(self.parsear_expresion())

        if not tipo_dato and not expresiones:
            self.agregar_error(f"Declaración de '{nombres[0]}' incompleta", t_var[2])

        # Creamos el nodo con el primer nombre para compatibilidad, pero guardamos la lista completa
        decl = DeclaracionVariable(nombres[0], tipo_dato, expresiones[0] if expresiones else None, t_var[2])
        decl.nombres = nombres
        decl.expresiones = expresiones
        # Agregar hijos para el resto de expresiones
        if len(expresiones) > 1:
            for exp in expresiones[1:]:
                decl.agregar_hijo(exp)
                
        return decl

    def parsear_tipo_dato(self):
        tipo = ""
        while self.peek() and self.peek()[1] == '*':
            tipo += "*"
            self.avanzar()
        while self.peek() and self.peek()[1] == '[':
            self.avanzar()
            t_len = self.peek()
            if t_len and t_len[0] in ['TKN NUM', 'TKN ID']:
                tipo += f"[{t_len[1]}]"
                self.avanzar()
            else: tipo += "[]"
            self.consumir(']', "Se esperaba ']' para cerrar el tipo de dato")
        t = self.peek()
        if t and (t[0] == 'TKN ID' or t[1] in KEYWORDS_GO or t[1] in ['int', 'float64', 'string', 'bool']):
            tipo += t[1]
            self.avanzar()
            return tipo
        return None

    def parsear_asignacion_o_expresion(self):
        linea = self.peek()[2] if self.peek() else 0
        izquierdos = [self.parsear_primario()]
        
        while self.match_valor(','):
            izquierdos.append(self.parsear_primario())
            
        if self.match_valor('='):
            derechos = [self.parsear_expresion()]
            while self.match_valor(','):
                derechos.append(self.parsear_expresion())
            
            asig = Asignacion(izquierdos[0], derechos[0], linea)
            asig.izquierdos = izquierdos
            asig.derechos = derechos
            
            # Agregar hijos restantes
            if len(izquierdos) > 1:
                for izq in izquierdos[1:]: asig.agregar_hijo(izq)
            if len(derechos) > 1:
                for der in derechos[1:]: asig.agregar_hijo(der)
                
            return asig
                
        elif self.match_valor(':='):
            derechos = [self.parsear_expresion()]
            while self.match_valor(','):
                derechos.append(self.parsear_expresion())
            
            # Walrus es una declaración
            decl = DeclaracionVariable(izquierdos[0].valor if hasattr(izquierdos[0], 'valor') else str(izquierdos[0]), "inferido", derechos[0], linea)
            decl.nombres = [izq.valor if hasattr(izq, 'valor') else str(izq) for izq in izquierdos]
            decl.expresiones = derechos
            
            # Agregar hijos restantes
            if len(derechos) > 1:
                for der in derechos[1:]: decl.agregar_hijo(der)
                
            return decl
            
        elif t_op := (self.match_valor('++') or self.match_valor('--')):
            op = '+' if t_op[1] == '++' else '-'
            return Asignacion(izquierdos[0], OperacionBinaria(op, izquierdos[0], Numero("1", linea), linea), linea)
        
        elif t_compound := (self.match_tipo('TKN ADDEQ') or self.match_tipo('TKN SUBEQ') or self.match_tipo('TKN MULTEQ') or self.match_tipo('TKN DIVEQ')):
            der = self.parsear_expresion()
            op = t_compound[1][0]
            return Asignacion(izquierdos[0], OperacionBinaria(op, izquierdos[0], der, linea), linea)

        return izquierdos[0]

    def parsear_bloque(self):
        t_llave = self.consumir('{', "Se esperaba '{' para iniciar el bloque")
        bloque = Bloque(t_llave[2])
        while self.peek() and self.peek()[1] != '}':
            if self.peek()[1] == ';':
                self.avanzar()
                continue
            s = self.parsear_sentencia()
            if s:
                bloque.agregar_hijo(s)
                # Check termination inside block
                t_sig = self.peek()
                if t_sig and t_sig[1] not in [';', '}', 'case', 'default']:
                    if t_sig[2] == s.linea:
                         self.agregar_error(f"Se esperaba ';' o fin de línea después de la sentencia, pero se encontró '{t_sig[1]}'", t_sig[2])
                         while self.peek() and self.peek()[1] not in [';', '}', '{'] and self.peek()[2] == t_sig[2]:
                             self.avanzar()
            else:
                # Si parsear_sentencia falló y no avanzó, evitamos bucle infinito
                if self.peek() and self.peek()[1] != '}':
                    self.avanzar()
        
        self.consumir('}', "Se esperaba '}' para cerrar el bloque")
        return bloque

    def parsear_if(self):
        t_if = self.match_valor('if')
        # Soporte para if con init: if x := 10; x > 5 { ... }
        # Leemos tokens hasta el { o ;
        temp_pos = self.pos
        has_semicolon = False
        while self.pos < len(self.tokens) and self.tokens[self.pos][1] != '{':
            if self.tokens[self.pos][1] == ';':
                has_semicolon = True
                break
            self.pos += 1
        self.pos = temp_pos

        init_stmt = None
        if has_semicolon:
            init_stmt = self.parsear_asignacion_o_expresion()
            self.match_valor(';')
        
        condicion = self.parsear_expresion()
        bloque_true = self.parsear_bloque()
        bloque_false = None
        if self.match_valor('else'):
            if self.peek() and self.peek()[1] == 'if':
                bloque_false = self.parsear_if()
            else:
                bloque_false = self.parsear_bloque()
        return If(condicion, bloque_true, bloque_false, t_if[2], init_stmt)

    def parsear_for(self):
        t_for = self.match_valor('for')
        # Simplificamos: leemos tokens para ver si hay ;
        temp_pos = self.pos
        semicolons = 0
        while self.pos < len(self.tokens) and self.tokens[self.pos][1] != '{':
            if self.tokens[self.pos][1] == ';': semicolons += 1
            self.pos += 1
        self.pos = temp_pos

        init, cond, post = None, None, None
        if semicolons == 2:
            if self.peek() and self.peek()[1] != ';': init = self.parsear_asignacion_o_expresion()
            self.match_valor(';')
            if self.peek() and self.peek()[1] != ';': cond = self.parsear_expresion()
            self.match_valor(';')
            if self.peek() and self.peek()[1] != '{': post = self.parsear_asignacion_o_expresion()
        elif self.peek() and self.peek()[1] != '{':
            cond = self.parsear_expresion()
            
        return For(init, cond, post, self.parsear_bloque(), t_for[2])

    def parsear_return(self):
        t_ret = self.match_valor('return')
        ret_nodo = Return(None, t_ret[2])
        if self.peek() and self.peek()[1] not in [';', '}']:
            ret_nodo.agregar_hijo(self.parsear_expresion())
            while self.match_valor(','):
                ret_nodo.agregar_hijo(self.parsear_expresion())
        return ret_nodo

    def parsear_funcion(self):
        t_func = self.match_valor('func')
        t_id = self.match_tipo('TKN ID')
        if not t_id:
            self.agregar_error("Se esperaba un identificador después de 'func'", t_func[2])
            nombre = "error_func"
        else:
            nombre = t_id[1]
            
        self.consumir('(', "Se esperaba '(' después del nombre de la función")
        parametros = []
        while self.peek() and self.peek()[1] != ')':
            p_id = self.match_tipo('TKN ID')
            if not p_id:
                self.agregar_error("Se esperaba un identificador de parámetro", self.peek()[2] if self.peek() else t_func[2])
                break
            p_tipo = self.parsear_tipo_dato()
            parametros.append((p_id[1], p_tipo))
            if not self.match_valor(','): break
        self.consumir(')', "Se esperaba ')' después de los parámetros")
        
        tipo_retorno = None
        if self.peek() and self.peek()[1] != '{':
            tipo_retorno = self.parsear_tipo_dato()
            
        return Funcion(nombre, parametros, tipo_retorno, self.parsear_bloque(), t_func[2])

    def parsear_break(self):
        return Break(self.avanzar()[2])

    def parsear_continue(self):
        return Continue(self.avanzar()[2])

    def parsear_switch(self):
        t_sw = self.match_valor('switch')
        exp = None
        if self.peek() and self.peek()[1] != '{':
            exp = self.parsear_expresion()
        self.consumir('{', "Se esperaba '{' para iniciar el switch")
        casos = []
        while self.peek() and self.peek()[1] != '}':
            casos.append(self.parsear_case())
        self.consumir('}', "Se esperaba '}' para cerrar el switch")
        return Switch(exp, casos, t_sw[2])

    def parsear_case(self):
        t = self.avanzar()
        es_default = (t[1] == 'default')
        exprs = []
        if not es_default:
            exprs.append(self.parsear_expresion())
            while self.match_valor(','):
                exprs.append(self.parsear_expresion())
        self.match_valor(':')
        bloque = Bloque(t[2])
        while self.peek() and self.peek()[1] not in ['case', 'default', '}']:
            s = self.parsear_sentencia()
            if s: bloque.agregar_hijo(s)
            else: self.avanzar()
        return Case(exprs, bloque, es_default, t[2])
