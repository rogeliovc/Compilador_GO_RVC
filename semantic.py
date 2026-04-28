from ast_nodes import *
from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo
from utils import es_identificador_valido, es_tipo_dato

class ASTVisitor:
    def visit(self, nodo):
        if nodo is None:
            return
        
        nombre_metodo = f'visit_{nodo.__class__.__name__}'
        metodo = getattr(self, nombre_metodo, self.visit_generic)
        return metodo(nodo)
        
    def visit_generic(self, nodo):
        for hijo in nodo.hijos:
            self.visit(hijo)

class AnalizadorSemanticoAST(ASTVisitor):
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.errores = []
        
        self.en_bloque_switch = False
        self.casos_switch_actual = set()
        self.en_bloque_for = False
        self.variables_for_locales = set()
        
    def agregar_error(self, mensaje, linea):
        self.errores.append(f"Línea {linea}: SEMÁNTICA - {mensaje}")
        from errors import agregar_error_uso
        agregar_error_uso(mensaje, linea)

    def obtener_errores(self):
        return self.errores
        
    def procesar(self, raiz):
        self.errores = []
        self.visit(raiz)
        return len(self.errores) == 0

    def visit_Programa(self, nodo):
        self.visit_generic(nodo)

    def visit_Package(self, nodo):
        paquete = nodo.valor
        simbolo = Simbolo(f"pkg_{paquete}", TipoSimbolo.PALABRA_RESERVADA, "package", nodo.linea, self.tabla_simbolos.ambito_actual, self.tabla_simbolos.scope_id_actual)
        if not self.tabla_simbolos.existe_simbolo(f"pkg_{paquete}"):
            self.tabla_simbolos.agregar_simbolo(simbolo)
        else:
            self.agregar_error(f"Paquete \"{paquete}\" ya existe", nodo.linea)

    def visit_Import(self, nodo):
        paquete = nodo.valor
        simbolo = Simbolo(paquete, TipoSimbolo.PALABRA_RESERVADA, "import", nodo.linea, self.tabla_simbolos.ambito_actual, self.tabla_simbolos.scope_id_actual)
        if not self.tabla_simbolos.existe_simbolo(paquete):
            self.tabla_simbolos.agregar_simbolo(simbolo)
        else:
            self.agregar_error(f"Import \"{paquete}\" ya existe", nodo.linea)

    def visit_DeclaracionVariable(self, nodo):
        nombres = getattr(nodo, 'multiples_valores', [nodo.valor])
        tipo = nodo.tipo_dato
        
        if nodo.hijos and nodo.hijos[0]:
            derechos = getattr(nodo, 'multiples_derechos', [nodo.hijos[0]])
            for d in derechos:
                self.visit(d)
            
        es_corta = (tipo == "inferido")
        if tipo is None: tipo = "inferido"
        
        if not es_tipo_dato(tipo) and tipo != "inferido" and not self.tabla_simbolos.existe_simbolo(tipo):
            self.agregar_error(f"Tipo de dato no reconocido '{tipo}' para la variable '{nombres[0]}'", nodo.linea)
            return

        if tipo != "inferido" and nodo.hijos and nodo.hijos[0]:
            derechos = getattr(nodo, 'multiples_derechos', [nodo.hijos[0]])
            for d in derechos:
                es_puntero_izq = tipo.startswith('*')
                es_ref_der = isinstance(d, OperacionUnaria) and d.valor == '&'
                if es_puntero_izq and not es_ref_der and isinstance(d, Variable):
                    self.agregar_error(f"Incompatibilidad de tipos: no se puede asignar un valor directo a una variable puntero '{tipo}' (falta &)", nodo.linea)
                elif not es_puntero_izq and es_ref_der:
                    self.agregar_error(f"Incompatibilidad de tipos: no se puede asignar un puntero (&) a una variable de tipo '{tipo}'", nodo.linea)

        if es_corta:
            al_menos_una_nueva = False
            for nombre in nombres:
                if not self.tabla_simbolos.existe_en_ambito_actual(nombre):
                    al_menos_una_nueva = True
                    break
            if not al_menos_una_nueva:
                vars_str = ", ".join(nombres)
                self.agregar_error(f"No hay variables nuevas a la izquierda de ':=' para [{vars_str}]", nodo.linea)

        for nombre in nombres:
            if self.tabla_simbolos.existe_en_ambito_actual(nombre):
                simbolo_previo = self.tabla_simbolos.buscar_simbolo(nombre)
                if not es_corta:
                    self.agregar_error(f"La variable '{nombre}' ya existe en el ámbito actual", nodo.linea)
                elif simbolo_previo and simbolo_previo.tipo_dato != tipo and tipo != "inferido":
                    self.agregar_error(f"Ambigüedad: Variable '{nombre}' declarada previamente como '{simbolo_previo.tipo_dato}' y ahora intentada declarar como '{tipo}'", nodo.linea)
            else:
                self.tabla_simbolos.agregar_variable(nombre, tipo, nodo.linea)

    def visit_Asignacion(self, nodo):
        izquierdos = getattr(nodo, 'multiples_izquierdos', [nodo.hijos[0]])
        derechos = getattr(nodo, 'multiples_derechos', [nodo.hijos[1]])
        
        for i in range(min(len(izquierdos), len(derechos))):
            izquierdo = izquierdos[i]
            derecho = derechos[i]
            if isinstance(izquierdo, Variable):
                if not self.tabla_simbolos.existe_simbolo(izquierdo.valor):
                    self.agregar_error(f"Variable '{izquierdo.valor}' no declarada siendo asignada", nodo.linea)
                else:
                    simbolo = self.tabla_simbolos.buscar_simbolo(izquierdo.valor)
                    tipo_izq = simbolo.tipo_dato if simbolo else "inferido"
                    if tipo_izq != "inferido":
                        es_puntero_izq = tipo_izq.startswith('*')
                        es_ref_der = isinstance(derecho, OperacionUnaria) and derecho.valor == '&'
                        
                        if es_puntero_izq and not es_ref_der and isinstance(derecho, Variable):
                            self.agregar_error(f"Incompatibilidad de tipos: no se puede asignar un valor directo a la variable puntero '{izquierdo.valor}' (falta &)", nodo.linea)
                        elif not es_puntero_izq and es_ref_der:
                            self.agregar_error(f"Incompatibilidad de tipos: no se puede asignar un puntero (&) a la variable '{izquierdo.valor}' de tipo '{tipo_izq}'", nodo.linea)
            elif isinstance(izquierdo, ArrayAccess):
                var_base = izquierdo.hijos[0]
                while isinstance(var_base, ArrayAccess):
                    var_base = var_base.hijos[0]
                if isinstance(var_base, Variable) and not self.tabla_simbolos.existe_simbolo(var_base.valor):
                    self.agregar_error(f"Variable '{var_base.valor}' no declarada siendo asignada", nodo.linea)
                    
            self.visit(izquierdo)
            
        for derecho in derechos:
            self.visit(derecho)

    def visit_Variable(self, nodo):
        val = nodo.valor
        if not self.tabla_simbolos.existe_simbolo(val) and not es_tipo_dato(val) and val not in ['true', 'false']:
            self.agregar_error(f"Símbolo '{val}' no declarado siendo usado en expresión", nodo.linea)

    def visit_AttributeAccess(self, nodo):
        base = nodo.hijos[0]
        self.visit(base)
        # Check if base exists
        if isinstance(base, Variable):
            if not self.tabla_simbolos.existe_simbolo(base.valor):
                self.agregar_error(f"Base indefinida '{base.valor}' al intentar acceder a atributo en '{base.valor}.{nodo.valor}'", nodo.linea)

    def visit_ArrayAccess(self, nodo):
        base = nodo.hijos[0]
        indice = nodo.hijos[1]
        
        self.visit(base)
        self.visit(indice)
        
        var_base = base
        while isinstance(var_base, ArrayAccess):
            var_base = var_base.hijos[0]
            
        if isinstance(var_base, Variable):
            simbolo = self.tabla_simbolos.buscar_simbolo(var_base.valor)
            if simbolo and not ('[' in simbolo.tipo_dato):
                self.agregar_error(f"El símbolo '{var_base.valor}' de tipo '{simbolo.tipo_dato}' no soporta acceso por índice", nodo.linea)

    def visit_LlamadaFuncion(self, nodo):
        expr_funcion = getattr(nodo, 'expr_funcion', None)
        
        if isinstance(expr_funcion, AttributeAccess):
            base = expr_funcion.hijos[0]
            metodo = expr_funcion.valor
            if isinstance(base, Variable):
                objeto = base.valor
                if not self.tabla_simbolos.existe_simbolo(objeto):
                    self.agregar_error(f"Paquete '{objeto}' no importado o no existe", nodo.linea)
                
                if objeto == "fmt":
                    funciones_fmt_validas = ["Print", "Println", "Printf", "Scan", "Scanln", "Scanf"]
                    if metodo == "Printl":
                        self.agregar_error(f"Función 'Printl' no existe - se esperaba 'Println'", nodo.linea)
                    elif metodo not in funciones_fmt_validas:
                        self.agregar_error(f"Función 'fmt.{metodo}' no existe", nodo.linea)
        elif isinstance(expr_funcion, Variable):
            nombre = expr_funcion.valor
            builtins = {"make", "len", "append", "panic", "print", "println", "recover", "close", "delete", "cap", "complex", "real", "imag", "new"}
            if nombre not in builtins:
                if not self.tabla_simbolos.existe_simbolo(nombre):
                    self.agregar_error(f"Llamada a función no declarada '{nombre}'", nodo.linea)
        
        # Al llamar a visit_generic, se visitará el nodo expr_funcion y luego los argumentos
        self.visit_generic(nodo)

    def visit_If(self, nodo):
        has_init = getattr(nodo, 'init_stmt', None) is not None
        if has_init:
            self.tabla_simbolos.entrar_ambito(Ambito.LOCAL)
            self.visit(nodo.init_stmt)
            
        for hijo in nodo.hijos:
            if hijo != getattr(nodo, 'init_stmt', None):
                self.visit(hijo)
                
        if has_init:
            self.tabla_simbolos.salir_ambito()

    def visit_For(self, nodo):
        old_for = self.en_bloque_for
        self.en_bloque_for = True
        self.tabla_simbolos.entrar_ambito_for()
        
        # init, cond, post, bloque (hijos 0, 1, 2, 3)
        if len(nodo.hijos) > 0: self.visit(nodo.hijos[0])
        if len(nodo.hijos) > 1: self.visit(nodo.hijos[1])
        if len(nodo.hijos) > 2: self.visit(nodo.hijos[2])
        if len(nodo.hijos) > 3: self.visit(nodo.hijos[3])
        
        self.tabla_simbolos.salir_ambito_for()
        self.en_bloque_for = old_for

    def visit_Switch(self, nodo):
        old_switch = self.en_bloque_switch
        old_casos = self.casos_switch_actual
        
        self.en_bloque_switch = True
        self.casos_switch_actual = set()
        
        if nodo.hijos:
            self.visit(nodo.hijos[0]) # expression
            for caso in nodo.hijos[1:]:
                self.visit(caso)
                
        self.en_bloque_switch = old_switch
        self.casos_switch_actual = old_casos

    def visit_Case(self, nodo):
        if not nodo.es_default:
            # Evaluate expressions to check for duplicate
            # In a full AST, we would extract the value statically if it's a literal
            for expr in nodo.hijos[:-1]:
                if hasattr(expr, "valor") and expr.valor:
                    val = str(expr.valor)
                    if val in self.casos_switch_actual:
                        self.agregar_error(f"Caso duplicado '{val}' en el bloque switch", nodo.linea)
                    else:
                        self.casos_switch_actual.add(val)
                self.visit(expr)
                
        self.visit(nodo.hijos[-1]) # block

    def visit_Funcion(self, nodo):
        # Register function
        nombre = nodo.valor
        tipo_retorno = getattr(nodo, 'tipo_retorno', 'void') or 'void'
        parametros = getattr(nodo, 'parametros', [])
        
        if not self.tabla_simbolos.agregar_funcion(nombre, tipo_retorno, parametros, nodo.linea):
            self.agregar_error(f"Función '{nombre}' ya existe en el ámbito actual", nodo.linea)
            
        self.tabla_simbolos.entrar_ambito(Ambito.LOCAL)
        for p_name, p_type in parametros:
            if not es_tipo_dato(p_type) and not self.tabla_simbolos.existe_simbolo(p_type):
                self.agregar_error(f"Tipo de dato no reconocido '{p_type}' para el parámetro '{p_name}'", nodo.linea)
            self.tabla_simbolos.agregar_parametro(p_name, p_type, nodo.linea)
            
        if nodo.hijos:
            self.visit(nodo.hijos[0]) # block
        self.tabla_simbolos.salir_ambito()

    def visit_Bloque(self, nodo):
        self.tabla_simbolos.entrar_ambito(Ambito.LOCAL)
        self.visit_generic(nodo)
        self.tabla_simbolos.salir_ambito()

    def visit_If(self, nodo):
        self.visit_generic(nodo)
        
    def visit_OperacionBinaria(self, nodo):
        self.visit_generic(nodo)

    def visit_OperacionUnaria(self, nodo):
        if nodo.valor == '*':
            if isinstance(nodo.hijos[0], Variable):
                simbolo = self.tabla_simbolos.buscar_simbolo(nodo.hijos[0].valor)
                if simbolo and not simbolo.tipo_dato.startswith('*') and simbolo.tipo_dato != "inferido":
                    self.agregar_error(f"Operación inválida: no se puede desreferenciar '{nodo.hijos[0].valor}' porque no es un puntero", nodo.linea)
        self.visit_generic(nodo)
    def visit_Numero(self, nodo):
        pass
        
    def visit_StringLiteral(self, nodo):
        pass
        
    def visit_BooleanLiteral(self, nodo):
        pass
        
    def visit_Return(self, nodo):
        self.visit_generic(nodo)

    def visit_Break(self, nodo):
        if not self.en_bloque_for and not self.en_bloque_switch:
            self.agregar_error("Sentencia 'break' fuera de un ciclo 'for' o bloque 'switch'", nodo.linea)
            
    def visit_Continue(self, nodo):
        if not self.en_bloque_for:
            self.agregar_error("Sentencia 'continue' fuera de un ciclo 'for'", nodo.linea)
