class GeneradorEnsamblador:
    def __init__(self, instrucciones_tac, tabla_simbolos=None):
        self.instrucciones = instrucciones_tac
        self.tabla_simbolos = tabla_simbolos
        self.asm = []
        self.variables = {} # nombre: tamaño en bytes
        self.strings = []

    def generar(self):
        self.asm = []
        self.recolectar_datos()
        
        self.asm.append("; --- CÓDIGO ENSAMBLADOR x86_64 (NASM) ---")
        
        if self.strings:
            self.asm.append("\nsection .rodata")
            for label, val in self.strings:
                self.asm.append(f"  {label} db {val}, 10, 0")

        self.asm.append("\nsection .data")
        # Forzamos que 'lista' y otras variables similares tengan el tamaño correcto
        for var, size in sorted(self.variables.items()):
            if size > 4:
                self.asm.append(f"  {var} times {size//4} dd 0")
            else:
                self.asm.append(f"  {var} dd 0")
        
        self.asm.append("\nsection .text")
        self.asm.append("  global _start\n")
        self.asm.append("_start:")
        self.asm.append("  call FUNC_START_main")
        self.asm.append("  mov eax, 60")
        self.asm.append("  xor rdi, rdi")
        self.asm.append("  syscall\n")

        for ins in self.instrucciones:
            self.traducir_instruccion(ins)

        return "\n".join(self.asm)

    def recolectar_datos(self):
        str_count = 0
        for ins in self.instrucciones:
            # 1. Strings
            if ins.op == 'PARAM' and str(ins.arg1).startswith('"'):
                label = f"str_{str_count}"
                self.strings.append((label, ins.arg1))
                ins.arg1 = label
                str_count += 1

            # 2. Variables y sus tamaños
            # Si la instrucción es de arreglo, su base (arg1) es definitivamente un arreglo
            if ins.op in ['[]=', '=[]']:
                self.registrar_variable(ins.arg1, es_arreglo=True)
            
            # Registrar otras variables normales
            for item in [ins.res, ins.arg1, ins.arg2]:
                if item and isinstance(item, str) and not item.startswith('str_'):
                    if not item.isdigit() and not item.startswith('"') and \
                       not item.startswith('L') and "." not in item and \
                       "FUNC_" not in item:
                        self.registrar_variable(item)

    def registrar_variable(self, nombre, es_arreglo=False):
        if nombre in self.variables and self.variables[nombre] > 4:
            return # Ya está registrada como arreglo

        size = 4
        if self.tabla_simbolos:
            simbolo = self.tabla_simbolos.buscar_simbolo(nombre)
            if simbolo and '[' in str(simbolo.tipo_dato):
                try:
                    # Extraer N de [N]int
                    import re
                    match = re.search(r'\[(\d+)\]', simbolo.tipo_dato)
                    if match:
                        n = int(match.group(1))
                        size = n * 4
                except:
                    size = 40 # Fallback 10 elementos
            elif es_arreglo:
                size = 40 # Si se usa como arreglo pero no lo hallamos, reservamos espacio prudente

        self.variables[nombre] = max(self.variables.get(nombre, 4), size)

    def traducir_instruccion(self, ins):
        op, res, arg1, arg2 = ins.op, ins.res, ins.arg1, ins.arg2

        if op == '=':
            self.asm.append(f"  mov eax, {self.formatear_operando(arg1)}")
            self.asm.append(f"  mov [{res}], eax")
        elif op in ['+', '-', '*', '/']:
            self.asm.append(f"  mov eax, {self.formatear_operando(arg1)}")
            if op == '+': self.asm.append(f"  add eax, {self.formatear_operando(arg2)}")
            elif op == '-': self.asm.append(f"  sub eax, {self.formatear_operando(arg2)}")
            elif op == '*': self.asm.append(f"  imul eax, {self.formatear_operando(arg2)}")
            elif op == '/':
                self.asm.append("  cdq")
                self.asm.append(f"  idiv dword {self.formatear_operando(arg2)}")
            self.asm.append(f"  mov [{res}], eax")
        elif op in ['==', '!=', '<', '>', '<=', '>=']:
            self.asm.append(f"  mov eax, {self.formatear_operando(arg1)}")
            self.asm.append(f"  cmp eax, {self.formatear_operando(arg2)}")
            cond_map = {'==': 'sete', '!=': 'setne', '<': 'setl', '>': 'setg', '<=': 'setle', '>=': 'setge'}
            self.asm.append(f"  {cond_map[op]} al")
            self.asm.append(f"  movzx eax, al")
            self.asm.append(f"  mov [{res}], eax")
        elif op == '[]=':
            idx_op = self.formatear_operando(arg2)
            if arg2.isdigit():
                self.asm.append(f"  mov rbx, {arg2}")
            else:
                self.asm.append(f"  movsxd rbx, dword {idx_op}")

            self.asm.append(f"  mov eax, {self.formatear_operando(res)}")
            self.asm.append(f"  mov [rel {arg1} + rbx*4], eax")

        elif op == '=[]':
            idx_op = self.formatear_operando(arg2)
            if arg2.isdigit():
                self.asm.append(f"  mov rbx, {arg2}")
            else:
                self.asm.append(f"  movsxd rbx, dword {idx_op}")

            self.asm.append(f"  mov eax, [rel {arg1} + rbx*4]")
            self.asm.append(f"  mov [{res}], eax")

        elif op == 'LABEL':
            self.asm.append(f"\n{res}:")
            # --- PRÓLOGO DE FUNCIÓN ---
            if str(res).startswith("FUNC_START_"):
                self.asm.append("  push rbp")
                self.asm.append("  mov rbp, rsp")
            
            # --- EPÍLOGO DE FUNCIÓN ---
            elif str(res).startswith("FUNC_END_"):
                self.asm.append("  mov rsp, rbp")
                self.asm.append("  pop rbp")
                self.asm.append("  ret")

        elif op == 'GOTO':
            self.asm.append(f"  jmp {res}")
        elif op == 'IFNOT':
            self.asm.append(f"  cmp dword [{arg1}], 0")
            self.asm.append(f"  je {res}")
        elif op == 'CALL':
            self.asm.append(f"  ; call {arg1}")
        elif op == 'PARAM':
            self.asm.append(f"  ; param {arg1}")

    def formatear_operando(self, op):
        if op is None: return "0"
        op_str = str(op)
        if op_str.isdigit() or (op_str.startswith('-') and op_str[1:].isdigit()):
            return op_str
        if op_str.startswith('str_'):
            return op_str
        return f"[{op_str}]"
