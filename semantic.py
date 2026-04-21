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
        simbolo = Simbolo(f"pkg_{paquete}", TipoSimbolo.PALABRA_RESERVADA, "package", nodo.linea, self.tabla_simbolos.ambito_actual)
        if not self.tabla_simbolos.existe_simbolo(f"pkg_{paquete}"):
            self.tabla_simbolos.agregar_simbolo(simbolo)
        else:
            self.agregar_error(f"Paquete \"{paquete}\" ya existe", nodo.linea)

    def visit_Import(self, nodo):
        paquete = nodo.valor
        simbolo = Simbolo(paquete, TipoSimbolo.PALABRA_RESERVADA, "import", nodo.linea, self.tabla_simbolos.ambito_actual)
        if not self.tabla_simbolos.existe_simbolo(paquete):
            self.tabla_simbolos.agregar_simbolo(simbolo)
        else:
            self.agregar_error(f"Import \"{paquete}\" ya existe", nodo.linea)

    def visit_DeclaracionVariable(self, nodo):
        nombres = getattr(nodo, 'multiples_valores', [nodo.valor])
        tipo = nodo.tipo_dato
        
        if nodo.hijos and nodo.hijos[0]:
            self.visit(nodo.hijos[0]) # Visitar la expresión de valor
            
        es_corta = (tipo == "inferido")
        if tipo is None: tipo = "inferido"
        
        if not es_tipo_dato(tipo) and tipo != "inferido" and not self.tabla_simbolos.existe_simbolo(tipo):
            self.agregar_error(f"Tipo de dato no reconocido '{tipo}' para la variable '{nombres[0]}'", nodo.linea)
            return

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
        derecho = nodo.hijos[1]
        
        for izquierdo in izquierdos:
            if isinstance(izquierdo, Variable):
                if not self.tabla_simbolos.existe_simbolo(izquierdo.valor):
                    self.agregar_error(f"Variable '{izquierdo.valor}' no declarada siendo asignada", nodo.linea)
            self.visit(izquierdo)
            
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

    def visit_LlamadaFuncion(self, nodo):
        objeto_metodo = nodo.valor
        
        if '.' in objeto_metodo:
            objeto, metodo = objeto_metodo.split('.', 1)
            if not self.tabla_simbolos.existe_simbolo(objeto):
                self.agregar_error(f"Paquete '{objeto}' no importado o no existe", nodo.linea)
            
            if objeto == "fmt":
                funciones_fmt_validas = ["Print", "Println", "Printf", "Scan", "Scanln", "Scanf"]
                if metodo == "Printl":
                    self.agregar_error(f"Función 'Printl' no existe - se esperaba 'Println'", nodo.linea)
                elif metodo not in funciones_fmt_validas:
                    self.agregar_error(f"Función 'fmt.{metodo}' no existe", nodo.linea)
        
        self.visit_generic(nodo)

    def visit_For(self, nodo):
        self.en_bloque_for = True
        self.tabla_simbolos.entrar_ambito_for()
        
        # init, cond, post, bloque (hijos 0, 1, 2, 3)
        if len(nodo.hijos) > 0: self.visit(nodo.hijos[0])
        if len(nodo.hijos) > 1: self.visit(nodo.hijos[1])
        if len(nodo.hijos) > 2: self.visit(nodo.hijos[2])
        if len(nodo.hijos) > 3: self.visit(nodo.hijos[3])
        
        self.tabla_simbolos.salir_ambito_for()
        self.en_bloque_for = False

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
        self.visit_generic(nodo)
        
    def visit_Numero(self, nodo):
        pass
        
    def visit_StringLiteral(self, nodo):
        pass
        
    def visit_BooleanLiteral(self, nodo):
        pass
        
    def visit_Return(self, nodo):
        self.visit_generic(nodo)
