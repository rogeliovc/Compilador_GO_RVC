from ast_nodes import *
from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo
from utils import es_identificador_valido, es_tipo_dato

class ASTVisitor:
    def visit(self, nodo):
        if nodo is None: return None
        nombre_metodo = f'visit_{nodo.__class__.__name__}'
        metodo = getattr(self, nombre_metodo, self.visit_generic)
        return metodo(nodo)
        
    def visit_generic(self, nodo):
        for hijo in nodo.hijos:
            self.visit(hijo)
        return None

class AnalizadorSemanticoAST(ASTVisitor):
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.errores = []
        
    def agregar_error(self, mensaje, linea):
        if linea <= 0: return 
        # Evitar duplicados simples
        err = f"Línea {linea}: SEMÁNTICA - {mensaje}"
        if err not in self.errores:
            self.errores.append(err)
            from errors import agregar_error_uso
            agregar_error_uso(mensaje, linea)

    def obtener_errores(self):
        return self.errores
        
    def procesar(self, raiz):
        self.errores = []
        self.visit(raiz)
        self.revisar_variables_no_usadas_global()
        return len(self.errores) == 0

    def revisar_variables_no_usadas_global(self):
        for lista_simbolos in self.tabla_simbolos.simbolos.values():
            for s in lista_simbolos:
                if s.nombre in ["import", "package", "main", "_", "int", "float64", "string", "bool"]: continue
                if s.tipo_dato == "package": continue
                
                if not s.usada:
                    if s.tipo_dato == "import":
                        self.agregar_error(f"Paquete '{s.nombre}' importado pero no usado", s.linea)
                    elif s.tipo_simbolo == TipoSimbolo.VARIABLE:
                        self.agregar_error(f"Variable '{s.nombre}' declarada pero no usada", s.linea)

    def visit_Programa(self, nodo):
        for hijo in nodo.hijos: self.visit(hijo)
        return "void"

    def visit_Package(self, nodo): return "void"

    def visit_Import(self, nodo):
        paquete = nodo.valor
        if paquete == "import": return "void"
        simbolo = Simbolo(paquete, TipoSimbolo.PALABRA_RESERVADA, "import", nodo.linea, self.tabla_simbolos.ambito_actual, self.tabla_simbolos.scope_id_actual)
        if not self.tabla_simbolos.existe_simbolo(paquete):
            self.tabla_simbolos.agregar_simbolo(simbolo)
        return "void"

    def visit_DeclaracionVariable(self, nodo):
        nombres = getattr(nodo, 'multiples_valores', [nodo.valor])
        tipo_declarado = nodo.tipo_dato
        tipo_der = self.visit(nodo.hijos[0]) if nodo.hijos and nodo.hijos[0] else None
        
        for nombre in nombres:
            tipo_final = tipo_declarado if tipo_declarado != "inferido" else (tipo_der or "int")
            if not self.tabla_simbolos.existe_en_ambito_actual(nombre):
                self.tabla_simbolos.agregar_variable(nombre, tipo_final, nodo.linea)
        return "void"

    def visit_Asignacion(self, nodo):
        for h in nodo.hijos: self.visit(h)
        return "void"

    def visit_Variable(self, nodo):
        simbolo = self.tabla_simbolos.buscar_simbolo(nodo.valor)
        if simbolo:
            simbolo.usada = True
            nodo.tipo_resultado = simbolo.tipo_dato
            return simbolo.tipo_dato
        if es_tipo_dato(nodo.valor): return nodo.valor
        self.agregar_error(f"Símbolo '{nodo.valor}' no declarado", nodo.linea)
        return "error"

    def visit_OperacionBinaria(self, nodo):
        tipo_izq = self.visit(nodo.hijos[0])
        tipo_der = self.visit(nodo.hijos[1])
        if nodo.valor in ['/', '%'] and isinstance(nodo.hijos[1], Numero) and str(nodo.hijos[1].valor) in ["0", "0.0"]:
            self.agregar_error("División por cero", nodo.linea)
        res = "bool" if nodo.valor in ['==', '!=', '<', '>', '<=', '>=', '&&', '||'] else (tipo_izq or "int")
        nodo.tipo_resultado = res
        return res

    def visit_AttributeAccess(self, nodo):
        base_nodo = nodo.hijos[0]
        self.visit(base_nodo)
        if isinstance(base_nodo, Variable):
            simb = self.tabla_simbolos.buscar_simbolo(base_nodo.valor)
            if simb: simb.usada = True
        return "function"

    def visit_LlamadaFuncion(self, nodo):
        for h in nodo.hijos: self.visit(h)
        return "void"

    def visit_Numero(self, nodo):
        t = "float64" if "." in str(nodo.valor) else "int"
        nodo.tipo_resultado = t
        return t

    def visit_StringLiteral(self, nodo): return "string"
    def visit_BooleanLiteral(self, nodo): return "bool"

    def visit_Bloque(self, nodo):
        self.tabla_simbolos.entrar_ambito(Ambito.LOCAL)
        for hijo in nodo.hijos:
            self.visit(hijo)
        self.tabla_simbolos.salir_ambito()
        return "void"

    def visit_If(self, nodo):
        if nodo.init_stmt:
            self.tabla_simbolos.entrar_ambito(Ambito.LOCAL)
            self.visit(nodo.init_stmt)
        cond, b_true, b_false = nodo.hijos
        self.visit(cond)
        self.visit(b_true)
        if b_false: self.visit(b_false)
        if nodo.init_stmt: self.tabla_simbolos.salir_ambito()
        return "void"

    def visit_For(self, nodo):
        init, cond, post, bloque = nodo.hijos
        self.tabla_simbolos.entrar_ambito_for()
        if init: self.visit(init)
        if cond: self.visit(cond)
        if post: self.visit(post)
        if bloque: self.visit(bloque)
        self.tabla_simbolos.salir_ambito_for()
        return "void"

    def visit_Funcion(self, nodo):
        self.tabla_simbolos.agregar_funcion(nodo.valor, nodo.tipo_retorno, nodo.parametros, nodo.linea)
        self.tabla_simbolos.entrar_ambito(Ambito.LOCAL)
        for p_n, p_t in (nodo.parametros or []):
            self.tabla_simbolos.agregar_parametro(p_n, p_t, nodo.linea)
        if nodo.hijos: self.visit(nodo.hijos[0])
        self.tabla_simbolos.salir_ambito()
        return "void"

    def visit_Return(self, nodo):
        if nodo.hijos: self.visit(nodo.hijos[0])
        return "void"

    def visit_Break(self, nodo): return "void"
    def visit_Continue(self, nodo): return "void"
    def visit_OperacionUnaria(self, nodo):
        self.visit(nodo.hijos[0])
        return "int"

    def visit_ArrayAccess(self, nodo):
        for h in nodo.hijos: self.visit(h)
        return "int"
