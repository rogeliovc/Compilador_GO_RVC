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
        self._current_switch_end = None

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
        
        # --- NUEVO: Aplicar optimizaciones ---
        optimizador = OptimizadorTAC(self.instrucciones)
        self.instrucciones = optimizador.optimizar()
        
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
        nombres = getattr(nodo, 'nombres', [nodo.valor])
        expresiones = getattr(nodo, 'expresiones', nodo.hijos if nodo.hijos else [])
        
        for i, nombre in enumerate(nombres):
            if i < len(expresiones):
                valor = self.visit(expresiones[i])
                self.emitir('=', valor, None, nombre)
        return None

    def visit_Asignacion(self, nodo):
        izquierdos = getattr(nodo, 'izquierdos', [nodo.hijos[0]])
        derechos = getattr(nodo, 'derechos', [nodo.hijos[1]])
        
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
        args_temporales = []
        for arg in nodo.hijos[1:]:
            args_temporales.append(self.visit(arg))
        for temp in args_temporales:
            self.emitir('PARAM', temp)
        func_expr = nodo.hijos[0]
        nombre_func = "unknown"
        if isinstance(func_expr, Variable):
            nombre_func = func_expr.valor
        elif isinstance(func_expr, AttributeAccess):
            nombre_func = f"{self.visit(func_expr.hijos[0])}.{func_expr.valor}"
        else:
            nombre_func = self.visit(func_expr)
        res = self.nuevo_temporal()
        self.emitir('CALL', nombre_func, len(args_temporales), res)
        return res

    def visit_AttributeAccess(self, nodo):
        base = self.visit(nodo.hijos[0])
        return f"{base}.{nodo.valor}"

    def visit_ArrayAccess(self, nodo):
        base = self.visit(nodo.hijos[0])
        idx = self.visit(nodo.hijos[1])
        res = self.nuevo_temporal()
        self.emitir('=[]', base, idx, res)
        return res

    def visit_Funcion(self, nodo):
        nombre = nodo.valor
        self.emitir('LABEL', None, None, f"FUNC_START_{nombre}")
        for p_nombre, p_tipo in (nodo.parametros or []):
            self.emitir('RECEIVE_PARAM', p_nombre)
        if nodo.hijos:
            self.visit(nodo.hijos[0])
        self.emitir('LABEL', None, None, f"FUNC_END_{nombre}")
        return None

    def visit_Switch(self, nodo):
        l_end = self.nueva_etiqueta()
        val_sw = self.visit(nodo.hijos[0]) if nodo.hijos[0] else None
        old_switch_end = getattr(self, '_current_switch_end', None)
        self._current_switch_end = l_end
        for caso in nodo.hijos[1:]:
            caso._switch_val = val_sw
            self.visit(caso)
        self.emitir('LABEL', None, None, l_end)
        self._current_switch_end = old_switch_end

    def visit_Case(self, nodo):
        l_next = self.nueva_etiqueta()
        if not nodo.es_default:
            for expr_nodo in nodo.hijos[:-1]:
                val_case = self.visit(expr_nodo)
                t_cmp = self.nuevo_temporal()
                if hasattr(nodo, '_switch_val') and nodo._switch_val:
                    self.emitir('==', nodo._switch_val, val_case, t_cmp)
                    self.emitir('IF', t_cmp, None, l_next)
                else:
                    self.emitir('IFNOT', val_case, None, l_next)
            self.visit(nodo.hijos[-1])
            if self._current_switch_end:
                self.emitir('GOTO', None, None, self._current_switch_end)
            self.emitir('LABEL', None, None, l_next)
        else:
            self.visit(nodo.hijos[-1])

    def obtener_codigo(self):
        return "\n".join(str(ins) for ins in self.instrucciones)

class OptimizadorTAC:
    def __init__(self, instrucciones):
        self.instrucciones = instrucciones

    def optimizar(self):
        # Realizamos varias pasadas hasta que ya no haya cambios (o un número fijo)
        for _ in range(3):
            self.instrucciones = self.plegado_constantes(self.instrucciones)
            self.instrucciones = self.eliminar_saltos_inutiles(self.instrucciones)
            self.instrucciones = self.eliminar_etiquetas_huerfanas(self.instrucciones)
        return self.instrucciones

    def es_numero(self, val):
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False

    def plegado_constantes(self, insts):
        optimizadas = []
        for ins in insts:
            if ins.op in ['+', '-', '*', '/', '%'] and self.es_numero(ins.arg1) and self.es_numero(ins.arg2):
                try:
                    v1, v2 = float(ins.arg1), float(ins.arg2)
                    res_val = 0
                    if ins.op == '+': res_val = v1 + v2
                    elif ins.op == '-': res_val = v1 - v2
                    elif ins.op == '*': res_val = v1 * v2
                    elif ins.op == '/': res_val = v1 / v2 if v2 != 0 else 0
                    elif ins.op == '%': res_val = v1 % v2
                    
                    str_res = str(int(res_val)) if res_val.is_integer() else str(res_val)
                    optimizadas.append(InstruccionTAC('=', str_res, None, ins.res))
                    continue
                except ZeroDivisionError: pass
            optimizadas.append(ins)
        return optimizadas

    def eliminar_saltos_inutiles(self, insts):
        optimizadas = []
        for i in range(len(insts)):
            ins = insts[i]
            if ins.op == 'GOTO' and i + 1 < len(insts):
                sig = insts[i+1]
                if sig.op == 'LABEL' and sig.res == ins.res:
                    continue
            optimizadas.append(ins)
        return optimizadas

    def eliminar_etiquetas_huerfanas(self, insts):
        usadas = set()
        for ins in insts:
            if ins.op in ['GOTO', 'IF', 'IFNOT']: usadas.add(ins.res)
        
        optimizadas = []
        for ins in insts:
            if ins.op == 'LABEL' and ins.res not in usadas:
                if not str(ins.res).startswith("FUNC_"): continue
            optimizadas.append(ins)
        return optimizadas
