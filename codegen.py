from ast_nodes import *

class InstruccionTAC:
    def __init__(self, op, arg1=None, arg2=None, res=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.res = res

    def __str__(self):
        if self.op in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||']:
            return f"  {self.res} = {self.arg1} {self.op} {self.arg2}"
        if self.op == '=':
            return f"  {self.res} = {self.arg1}"
        if self.op == 'LABEL':
            return f"\n{self.res}:"
        if self.op == 'GOTO':
            return f"  goto {self.res}"
        if self.op == 'IF':
            return f"  if {self.arg1} goto {self.res}"
        if self.op == 'IFNOT':
            return f"  ifnot {self.arg1} goto {self.res}"
        if self.op == 'PARAM':
            return f"  param {self.arg1}"
        if self.op == 'RECEIVE_PARAM':
            return f"  receive_param {self.arg1}"
        if self.op == 'CALL':
            return f"  {self.res} = call {self.arg1}, {self.arg2}"
        if self.op == 'RETURN':
            return f"  return {self.arg1 if self.arg1 else ''}"
        if self.op == 'UNARY':
            return f"  {self.res} = {self.arg1}{self.arg2}"
        if self.op == '[]=':
            return f"  {self.arg1}[{self.arg2}] = {self.res}"
        if self.op == '=[]':
            return f"  {self.res} = {self.arg1}[{self.arg2}]"
        return f"  {self.res} = {self.op} {self.arg1} {self.arg2}"

class GeneradorIntermedio:
    def __init__(self):
        self.instrucciones = []
        self.temp_count = 0
        self.label_count = 0
        self.pila_etiquetas_for = [] # [(etiqueta_inicio, etiqueta_fin), ...]

    def nuevo_temporal(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def nueva_etiqueta(self):
        l = f"L{self.label_count}"
        self.label_count += 1
        return l

    def emitir(self, op, arg1=None, arg2=None, res=None):
        ins = InstruccionTAC(op, arg1, arg2, res)
        self.instrucciones.append(ins)
        return ins

    def generar(self, nodo_raiz):
        self.instrucciones = []
        self.temp_count = 0
        self.label_count = 0
        self.pila_etiquetas_for = []
        self.visit(nodo_raiz)
        return self.instrucciones

    def visit(self, nodo):
        if nodo is None: return None
        metodo = f"visit_{nodo.__class__.__name__}"
        visitante = getattr(self, metodo, self.visit_generic)
        return visitante(nodo)

    def visit_generic(self, nodo):
        for hijo in nodo.hijos:
            self.visit(hijo)
        return None

    # --- EXPRESIONES ---
    
    def visit_Numero(self, nodo): return str(nodo.valor)
    def visit_StringLiteral(self, nodo): return nodo.valor
    def visit_BooleanLiteral(self, nodo): return "1" if nodo.valor == "true" else "0"
    def visit_Variable(self, nodo): return nodo.valor

    def visit_OperacionBinaria(self, nodo):
        izq = self.visit(nodo.hijos[0])
        der = self.visit(nodo.hijos[1])
        res = self.nuevo_temporal()
        self.emitir(nodo.valor, izq, der, res)
        return res

    def visit_OperacionUnaria(self, nodo):
        operando = self.visit(nodo.hijos[0])
        res = self.nuevo_temporal()
        self.emitir('UNARY', nodo.valor, operando, res)
        return res

    # --- SENTENCIAS ---

    def visit_Programa(self, nodo):
        for hijo in nodo.hijos: self.visit(hijo)

    def visit_Bloque(self, nodo):
        for hijo in nodo.hijos: self.visit(hijo)

    def visit_DeclaracionVariable(self, nodo):
        nombres = getattr(nodo, 'multiples_valores', [nodo.valor])
        derechos = getattr(nodo, 'multiples_derechos', [nodo.hijos[0]] if nodo.hijos else [])
        
        for i, nombre in enumerate(nombres):
            if i < len(derechos):
                valor = self.visit(derechos[i])
                self.emitir('=', valor, None, nombre)
        return None

    def visit_Asignacion(self, nodo):
        izquierdos = getattr(nodo, 'multiples_izquierdos', [nodo.hijos[0]])
        derechos = getattr(nodo, 'multiples_derechos', [nodo.hijos[1]])
        
        for i in range(min(len(izquierdos), len(derechos))):
            valor_der = self.visit(derechos[i])
            izq_nodo = izquierdos[i]
            
            if isinstance(izq_nodo, Variable):
                self.emitir('=', valor_der, None, izq_nodo.valor)
            elif isinstance(izq_nodo, ArrayAccess):
                base = self.visit(izq_nodo.hijos[0])
                idx = self.visit(izq_nodo.hijos[1])
                self.emitir('[]=', base, idx, valor_der)
        return None

    # --- CONTROL DE FLUJO ---

    def visit_If(self, nodo):
        if nodo.init_stmt:
            self.visit(nodo.init_stmt)
            
        l_else = self.nueva_etiqueta()
        l_end = self.nueva_etiqueta()
        
        cond, b_true, b_false = nodo.hijos
        temp_cond = self.visit(cond)
        
        self.emitir('IFNOT', temp_cond, None, l_else)
        self.visit(b_true)
        self.emitir('GOTO', None, None, l_end)
        
        self.emitir('LABEL', None, None, l_else)
        if b_false:
            self.visit(b_false)
            
        self.emitir('LABEL', None, None, l_end)

    def visit_For(self, nodo):
        init, cond, post, bloque = nodo.hijos
        l_start = self.nueva_etiqueta()
        l_post = self.nueva_etiqueta()
        l_end = self.nueva_etiqueta()
        
        self.pila_etiquetas_for.append((l_post, l_end))
        
        if init: self.visit(init)
        self.emitir('LABEL', None, None, l_start)
        
        if cond:
            temp_cond = self.visit(cond)
            self.emitir('IFNOT', temp_cond, None, l_end)
            
        if bloque: self.visit(bloque)
        
        self.emitir('LABEL', None, None, l_post)
        if post: self.visit(post)
        
        self.emitir('GOTO', None, None, l_start)
        self.emitir('LABEL', None, None, l_end)
        self.pila_etiquetas_for.pop()

    def visit_Break(self, nodo):
        if self.pila_etiquetas_for:
            _, l_end = self.pila_etiquetas_for[-1]
            self.emitir('GOTO', None, None, l_end)

    def visit_Continue(self, nodo):
        if self.pila_etiquetas_for:
            l_post, _ = self.pila_etiquetas_for[-1]
            self.emitir('GOTO', None, None, l_post)

    def visit_Return(self, nodo):
        valor = None
        if nodo.hijos:
            valor = self.visit(nodo.hijos[0])
        self.emitir('RETURN', valor)

    def visit_LlamadaFuncion(self, nodo):
        # 1. Generar código para los argumentos
        args_temporales = []
        # En LlamadaFuncion: hijo 0 es la expr_func, hijos 1+ son los argumentos
        for arg in nodo.hijos[1:]:
            args_temporales.append(self.visit(arg))
            
        # 2. Emitir PARAM para cada argumento (estándar TAC)
        for temp in args_temporales:
            self.emitir('PARAM', temp)
            
        # 3. Obtener el nombre de la función
        func_expr = nodo.hijos[0]
        nombre_func = "unknown"
        if isinstance(func_expr, Variable):
            nombre_func = func_expr.valor
        elif isinstance(func_expr, AttributeAccess):
            nombre_func = f"{self.visit(func_expr.hijos[0])}.{func_expr.valor}"
        else:
            nombre_func = self.visit(func_expr)
             
        # 4. Emitir CALL (res = call func, num_params)
        res = self.nuevo_temporal()
        self.emitir('CALL', nombre_func, len(args_temporales), res)
        return res

    def visit_AttributeAccess(self, nodo):
        # Simplificación para TAC: devolver nombre compuesto (ej: fmt.Println)
        base = self.visit(nodo.hijos[0])
        return f"{base}.{nodo.valor}"

    def visit_ArrayAccess(self, nodo):
        # Lectura de arreglo: res = arr[i]
        base = self.visit(nodo.hijos[0])
        idx = self.visit(nodo.hijos[1])
        res = self.nuevo_temporal()
        self.emitir('=[]', base, idx, res)
        return res

    def visit_Funcion(self, nodo):
        nombre = nodo.valor
        self.emitir('LABEL', None, None, f"FUNC_START_{nombre}")
        
        # Procesar parámetros (solo como referencia en el TAC)
        for p_nombre, p_tipo in (nodo.parametros or []):
            self.emitir('RECEIVE_PARAM', p_nombre)
            
        # Visitar el cuerpo (bloque)
        if nodo.hijos:
            self.visit(nodo.hijos[0])
            
        self.emitir('LABEL', None, None, f"FUNC_END_{nombre}")
        return None

    def visit_Switch(self, nodo):
        l_end = self.nueva_etiqueta()
        val_sw = self.visit(nodo.hijos[0]) if nodo.hijos[0] else None
        
        # Guardamos la etiqueta de salida en una propiedad temporal para los 'Case'
        old_switch_end = getattr(self, '_current_switch_end', None)
        self._current_switch_end = l_end
        
        # Procesamos los casos (están en hijos[1:])
        for caso in nodo.hijos[1:]:
            # Pasamos el valor del switch al caso para que genere la comparación
            caso._switch_val = val_sw
            self.visit(caso)
            
        self.emitir('LABEL', None, None, l_end)
        self._current_switch_end = old_switch_end

    def visit_Case(self, nodo):
        l_next = self.nueva_etiqueta()
        
        if not nodo.es_default:
            # En Go un case puede tener múltiples expresiones: case 1, 2, 3:
            # nodo.hijos[:-1] son las expresiones, nodo.hijos[-1] es el bloque
            for expr_nodo in nodo.hijos[:-1]:
                val_case = self.visit(expr_nodo)
                t_cmp = self.nuevo_temporal()
                # Si el switch tiene valor, comparamos. Si no (switch {}), el case debe ser bool.
                if hasattr(nodo, '_switch_val') and nodo._switch_val:
                    self.emitir('==', nodo._switch_val, val_case, t_cmp)
                    self.emitir('IF', t_cmp, None, l_next) # Si coincide, vamos al bloque (simulado)
                else:
                    self.emitir('IFNOT', val_case, None, l_next)
            
            # Nota: Esta es una implementación simplificada de switch.
            # Para mayor fidelidad, se usaría una estructura de saltos más compleja.
            self.visit(nodo.hijos[-1]) # Bloque del case
            self.emitir('GOTO', None, None, self._current_switch_end)
            self.emitir('LABEL', None, None, l_next)
        else:
            # Default case
            self.visit(nodo.hijos[-1])

    def obtener_codigo(self):
        return "\n".join(str(ins) for ins in self.instrucciones)
