import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import re

from lexer import AnalizadorLexico
from parser import AnalizadorSintactico
from semantic import AutomataSemantico
from symbol_table import TablaSimbolos
from errors import limpiar_errores, imprimir_errores, obtener_resumen_errores
from utils import es_identificador_valido, es_tipo_dato, KEYWORDS_GO, TIPOS_BASICOS

class CodeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador Mini-Go - Sistema de Errores")
        self.root.geometry("1000x700")
        self.current_file = None

        self.lexer = AnalizadorLexico()
        self.parser = AnalizadorSintactico()
        self.semantic = AutomataSemantico()
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')
        
        # Panel superior para el editor
        self.editor_frame = ttk.Frame(self.main_frame)
        self.editor_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Panel inferior para resultados
        self.results_frame = ttk.LabelFrame(self.main_frame, text="Resultados del Análisis", height=200)
        self.results_frame.pack(fill='both', expand=False, padx=5, pady=5)
        self.results_frame.pack_propagate(False)
        
        self.line_numbers = tk.Text(self.editor_frame, width=4, padx=3, pady=5,
                                   background='#e0e0e0', foreground='#666666',
                                   font=('Consolas', 11), state='disabled',
                                   wrap=tk.NONE, cursor='arrow')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.text_area = tk.Text(self.editor_frame, wrap=tk.WORD, font=('Consolas', 11), 
                               background='#f0f0f0', foreground='#000000',
                               insertbackground='black', selectbackground='#a6d2ff',
                               padx=10, pady=10, yscrollcommand=self.on_textscroll)
        self.text_area.pack(side=tk.LEFT, expand=True, fill='both')
        
        self.scrollbar = ttk.Scrollbar(self.editor_frame, orient='vertical',
                                command=self.on_scrollbar)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_area.config(yscrollcommand=self.on_textscroll)
        
        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD, font=('Consolas', 10),
                                   background='#2b2b2b', foreground='#00ff00',
                                   padx=5, pady=5, height=8)
        self.results_scrollbar = ttk.Scrollbar(self.results_frame, orient='vertical',
                                            command=self.results_text.yview)
        self.results_text.config(yscrollcommand=self.results_scrollbar.set)
        
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.pack(side=tk.LEFT, expand=True, fill='both')
        
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Listo", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, padx=2)
        
        self.file_info_label = ttk.Label(self.status_bar, text="", relief=tk.SUNKEN)
        self.file_info_label.pack(side=tk.RIGHT, padx=2)
        
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        self.text_area.bind('<MouseWheel>', self.on_mousewheel)
        self.text_area.bind('<Return>', self.on_enter_key)
        
        self.update_line_numbers()
        self.setup_menu()
        self.setup_syntax_highlighting()
        
    def setup_syntax_highlighting(self):
        """Configura los colores (tags) para el editor de código"""
        self.text_area.tag_configure("Keyword", foreground="#cc7832", font=('Consolas', 11, 'bold'))
        self.text_area.tag_configure("Type", foreground="#9876aa", font=('Consolas', 11, 'italic'))
        self.text_area.tag_configure("String", foreground="#6a8759")
        self.text_area.tag_configure("Comment", foreground="#808080", font=('Consolas', 11, 'italic'))
        self.text_area.tag_configure("Number", foreground="#6897bb")
        self.text_area.tag_configure("Function", foreground="#ffc66d")
    
    def highlight_syntax(self, event=None):
        """Aplica colores al código escrito usando expresiones regulares"""
        for tag in ["Keyword", "Type", "String", "Comment", "Number", "Function"]:
            self.text_area.tag_remove(tag, "1.0", tk.END)
            
        texto = self.text_area.get("1.0", tk.END)
        if not texto.strip(): return
        
        # 1. Comentarios //
        for match in re.finditer(r'//.*', texto):
            inicio = f"1.0 + {match.start()} chars"
            fin = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("Comment", inicio, fin)
            
        # 2. Cadenas de texto "..." o `...`
        for match in re.finditer(r'(".*?"|`.*?`)', texto):
            inicio = f"1.0 + {match.start()} chars"
            fin = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("String", inicio, fin)
            
        # 3. Números
        for match in re.finditer(r'\b\d+(\.\d+)?\b', texto):
            inicio = f"1.0 + {match.start()} chars"
            fin = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("Number", inicio, fin)
            
        # 4. Palabras reservadas (Go)
        pattern_kw = r'\b(' + '|'.join(KEYWORDS_GO) + r')\b'
        for match in re.finditer(pattern_kw, texto):
            inicio = f"1.0 + {match.start()} chars"
            fin = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("Keyword", inicio, fin)
            
        # 5. Tipos de datos básicos
        pattern_types = r'\b(' + '|'.join(TIPOS_BASICOS) + r')\b'
        for match in re.finditer(pattern_types, texto):
            inicio = f"1.0 + {match.start()} chars"
            fin = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("Type", inicio, fin)
            
        # 6. Funciones Custom (Lo que esté antes de un paréntesis que no sea un keyword)
        for match in re.finditer(r'\b([a-zA-Z_]\w*)\s*\(', texto):
            nombre_func = match.group(1)
            if nombre_func not in KEYWORDS_GO and nombre_func not in TIPOS_BASICOS:
                inicio = f"1.0 + {match.start(1)} chars"
                fin = f"1.0 + {match.end(1)} chars"
                self.text_area.tag_add("Function", inicio, fin)
    
    def update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        texto_editor = str(self.text_area.get(1.0, tk.END))
        
        if texto_editor:
            if texto_editor.endswith('\n'):
                texto_editor = texto_editor[:len(texto_editor)-1]
            line_count = texto_editor.count('\n') + 1
        else:
            line_count = 1
        
        # Generar números de línea
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert(1.0, line_numbers_text)
        self.line_numbers.config(state='disabled')
        
        # Sincronizar el scroll
        self.line_numbers.yview_moveto(self.text_area.yview()[0])
    
    def on_textscroll(self, *args):
        self.scrollbar.set(*args)
        self.line_numbers.yview_moveto(args[0])
    
    def on_scrollbar(self, *args):
        self.text_area.yview(*args)
        self.line_numbers.yview_moveto(args[0])
    
    def on_key_release(self, event=None):
        if event and event.keysym in ['Return', 'BackSpace', 'Delete']:
            self.update_line_numbers()
        self.update_status()
        self.validar_en_tiempo_real()
        self.highlight_syntax()
        
    def on_enter_key(self, event=None):
        """Autoindentación: replica la sangría de la línea anterior"""
        linea_actual_str = self.text_area.get("insert linestart", "insert lineend")
        identacion_coincidencia = re.match(r'^(\s+)', linea_actual_str)
        
        espacio_a_insertar = ""
        if identacion_coincidencia:
            espacio_a_insertar = identacion_coincidencia.group(1)
            
        # Si la línea terminó en {, agregamos sangría extra
        if linea_actual_str.strip().endswith('{'):
            espacio_a_insertar += "    "
            
        if espacio_a_insertar:
            self.text_area.insert("insert lineend", "\n" + espacio_a_insertar)
            self.update_line_numbers()
            self.update_status()
            self.highlight_syntax()
            return "break"
    
    def validar_en_tiempo_real(self):
        linea_actual = self.text_area.get("insert linestart", "insert lineend").strip()
        if linea_actual:
            palabras = linea_actual.split()
            for palabra in palabras:
                if es_tipo_dato(palabra):
                    for siguiente in palabras[palabras.index(palabra)+1:]:
                        if es_identificador_valido(siguiente):
                            self.semantic.variables_encontradas.add(siguiente)
                            break
    
    def on_mousewheel(self, event=None):
        self.update_line_numbers()
    
    def update_status(self):
        texto_editor = str(self.text_area.get(1.0, tk.END))
        
        char_count = len(texto_editor) - 1
        line_count = texto_editor.count('\n')
        status_text = f"Caracteres: {char_count} | Líneas: {line_count}"
        self.status_label.config(text=status_text)
    
    def update_file_info(self):
        if self.current_file:
            filename = os.path.basename(self.current_file)
            file_size = os.path.getsize(self.current_file) if os.path.exists(self.current_file) else 0
            file_info = f"{filename} | {file_size} bytes"
        else:
            file_info = "Sin guardar"
        self.file_info_label.config(text=file_info)
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nuevo", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Abrir...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Guardar", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Guardar como...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Deshacer", accelerator="Ctrl+Z", command=lambda: self.text_area.event_generate("<<Undo>>"))
        edit_menu.add_command(label="Rehacer", accelerator="Ctrl+Y", command=lambda: self.text_area.event_generate("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cortar", accelerator="Ctrl+X", command=lambda: self.text_area.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copiar", accelerator="Ctrl+C", command=lambda: self.text_area.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Pegar", accelerator="Ctrl+V", command=lambda: self.text_area.event_generate("<<Paste>>"))
        
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Compilación", menu=run_menu)
        run_menu.add_command(label="Paso 1: Análisis Léxico (Tokens)", accelerator="F5", command=self.analizar_lexico)
        run_menu.add_separator()
        run_menu.add_command(label="Paso 2a: Validar Bloques (Sintáctico)", accelerator="F6", command=self.validar_estructura)
        run_menu.add_command(label="Paso 2b: Generar Árbol de Parseo", accelerator="F7", command=self.generar_arbol_parseo)
        run_menu.add_separator()
        run_menu.add_command(label="Paso 3: Análisis Semántico", accelerator="F8", command=self.validar_declaraciones_go)
        run_menu.add_separator()
        run_menu.add_command(label="Ver Tabla de Símbolos Generada", accelerator="F10", command=self.mostrar_tabla_simbolos)
        run_menu.add_separator()
        run_menu.add_command(label="Ejecutar Pipeline Completo", accelerator="F9", command=self.compilar_codigo)
        
        compiler_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=compiler_menu)
        compiler_menu.add_command(label="Limpiar Consola de Resultados", command=self.limpiar_resultados)
        compiler_menu.add_separator()
        compiler_menu.add_command(label="Exportar Análisis a TXT", command=self.guardar_analisis)
        compiler_menu.add_separator()
        compiler_menu.add_command(label="Limpiar Errores del Sistema", accelerator="F11", command=self.limpiar_errores_sistema)
        compiler_menu.add_command(label="Mostrar Errores Detallados", accelerator="F12", command=self.mostrar_errores_detallados)
        
        variables_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Variables", menu=variables_menu)
        variables_menu.add_command(label="Ver Variables", command=self.ver_variables)
        variables_menu.add_command(label="Limpiar Variables", command=self.limpiar_variables)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Ayuda", command=self.show_help)
        help_menu.add_command(label="Acerca de...", command=self.show_about)
        
        self.setup_shortcuts()
    
    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("Nuevo archivo - Compilador Mini-Go")
        
        self.semantic.variables_encontradas.clear()
        self.semantic.tabla_simbolos = TablaSimbolos()
        limpiar_errores()
        
        self.update_line_numbers()
        self.update_file_info()
        self.update_status()
    
    def open_file(self):
        file_types = [("Archivos Go", "*.go"), ("Archivos Python", "*.py"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(1.0, file.read())
                self.current_file = file_path
                self.root.title(f"{file_path} - Compilador Mini-Go")
                self.highlight_syntax()
                
                self.semantic.variables_encontradas.clear()
                self.semantic.tabla_simbolos = TablaSimbolos()
                limpiar_errores() 
                
                self.update_line_numbers()
                self.update_file_info()
                self.update_status()
                self.status_label.config(text=f"Archivo abierto: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
    
    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get(1.0, tk.END))
                messagebox.showinfo("Guardado", f"Archivo guardado: {self.current_file}")
                self.update_file_info()
                self.status_label.config(text=f"Archivo guardado: {os.path.basename(self.current_file)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        file_types = [("Archivos Go", "*.go"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        
        file_path = filedialog.asksaveasfilename(filetypes=file_types, defaultextension=".go")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.text_area.get(1.0, tk.END))
                self.current_file = file_path
                self.root.title(f"{file_path} - Compilador Mini-Go")
                messagebox.showinfo("Guardado", f"Archivo guardado: {file_path}")
                self.update_file_info()
                self.status_label.config(text=f"Archivo guardado: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
    
    def compilar_codigo(self):
        """Función completa de compilación con sistema de errores integrado"""
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No hay código para compilar.\n")
            return
        
        limpiar_errores()
        
        self.semantic.variables_encontradas.clear()
        self.semantic.tabla_simbolos = TablaSimbolos()
        
        self.parser = AnalizadorSintactico()
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Iniciando compilación (Mini-Go Compiler v1.0)\n")
        self.results_text.insert(tk.END, "-" * 60 + "\n\n")
        
        # 1. Análisis léxico con detección de errores
        self.results_text.insert(tk.END, "[Fase 1] Análisis Léxico (Tokenizado)\n")
        
        lineas = codigo.split('\n')
        tokens_totales = []
        
        for i, linea in enumerate(lineas, 1):
            if linea.strip():
                tokens_linea = self.lexer.procesar(linea, i)
                tokens_totales.extend(tokens_linea)
        
        self.results_text.insert(tk.END, f"  > Total de tokens identificados: {len(tokens_totales)}\n")
        
        # 2. Análisis sintáctico estructural
        self.results_text.insert(tk.END, "\n[Fase 2] Análisis Sintáctico (Parser)\n")
        
        es_sintaxis_valida = True
        for i, linea in enumerate(lineas, 1):
            if linea.strip() and not linea.strip().startswith('//'):
                tokens = self.lexer.procesar(linea, i)
                tokens = self.parser.limpiar_tokens(tokens)
                if not tokens:
                    continue
                if not self.parser.validar_sintaxis_go(tokens, i, omitir_balance_simbolos=True):
                    es_sintaxis_valida = False
                self.parser.procesar_linea_archivo(tokens, i)
        
        if not self.parser.finalizar_archivo():
            es_sintaxis_valida = False
            
        if es_sintaxis_valida:
            self.results_text.insert(tk.END, "  > Status: Sintaxis de bloques estructuralmente válida.\n")
        else:
            self.results_text.insert(tk.END, "  > Status: (ERROR) Se detectaron bloques o estructuras inválidas.\n")

        # 3. Análisis semántico completo
        self.results_text.insert(tk.END, "\n[Fase 3] Análisis Semántico (Declaraciones)\n")
        
        declaraciones_validas: int = 0
        declaraciones_invalidas: int = 0
        lineas_ignoradas: int = 0
        
        assert isinstance(declaraciones_validas, int)
        assert isinstance(declaraciones_invalidas, int)
        assert isinstance(lineas_ignoradas, int)
        
        for i, linea in enumerate(lineas, 1):
            if not linea.strip() or linea.strip().startswith('//'):
                continue
            
            tokens = self.lexer.procesar(linea, i)
            tokens = self.parser.limpiar_tokens(tokens)
            if not tokens:
                continue
                
            es_valido, mensaje, simbolo = self.semantic.validar_declaracion(tokens)
            
            if es_valido:
                self.results_text.insert(tk.END, f"  [PASS] Línea {i}: {mensaje}\n")
                declaraciones_validas = int(declaraciones_validas) + 1
            elif 'no es declaración' in mensaje.lower() or 'llamada a función' in mensaje.lower() or 'estructura de control' in mensaje.lower():
                self.results_text.insert(tk.END, f"  [INFO] Línea {i}: {mensaje}\n")
                lineas_ignoradas = int(lineas_ignoradas) + 1
            else:
                self.results_text.insert(tk.END, f"  [FAIL] Línea {i}: {mensaje}\n")
                declaraciones_invalidas = int(declaraciones_invalidas) + 1
            
            assert isinstance(declaraciones_validas, int)
            assert isinstance(declaraciones_invalidas, int)
            assert isinstance(lineas_ignoradas, int)
        
        # 4. Resumen del análisis
        self.results_text.insert(tk.END, f"\n[Reporte de Validación]\n")
        self.results_text.insert(tk.END, f"Líneas procesadas: {len(lineas)}\n")
        self.results_text.insert(tk.END, f"  - Declaraciones válidas: {declaraciones_validas}\n")
        self.results_text.insert(tk.END, f"  - Declaraciones inválidas: {declaraciones_invalidas}\n")
        self.results_text.insert(tk.END, f"  - Estructuras ignoradas: {lineas_ignoradas}\n")
        
        # 5. Mostrar errores detectados por el sistema
        self.results_text.insert(tk.END, f"\n[Diagnóstico de Errores Global]\n")
        
        resumen_errores = obtener_resumen_errores()
        
        if resumen_errores['total_errores'] > 0:
            self.results_text.insert(tk.END, f"  [!] ERRORES SINTÁCTICOS: {resumen_errores['total_sintacticos']}\n")
            for cat, count in resumen_errores['detalle_sintacticos'].items():
                if count > 0:
                    self.results_text.insert(tk.END, f"      > {cat}: {count}\n")
            
            self.results_text.insert(tk.END, f"\n  [!] ERRORES SEMÁNTICOS: {resumen_errores['total_semanticos']}\n")
            for cat, count in resumen_errores['detalle_semanticos'].items():
                if count > 0:
                    self.results_text.insert(tk.END, f"      > {cat}: {count}\n")
        else:
            self.results_text.insert(tk.END, "  > 0 errores detectados transversalmente.\n")
        
        # 6. Estado de la tabla de símbolos
        self.results_text.insert(tk.END, f"\n[Tabla de Símbolos]\n")
        
        variables: int = 0
        funciones: int = 0
        structs: int = 0
        imports: int = 0
        
        assert isinstance(variables, int)
        assert isinstance(funciones, int)
        assert isinstance(structs, int)
        assert isinstance(imports, int)
        
        sintacticos: int = 0
        semanticos: int = 0
        
        assert isinstance(sintacticos, int)
        assert isinstance(semanticos, int)
        assert isinstance(semanticos, int)
        
        assert isinstance(variables, int)
        assert isinstance(funciones, int)
        assert isinstance(structs, int)
        assert isinstance(imports, int)
        
        for nombre, simbolos_lista in self.semantic.tabla_simbolos.simbolos.items():
            for simbolo in simbolos_lista:
                if simbolo.tipo_simbolo.value == 'variable':
                    variables = int(variables) + 1
                elif simbolo.tipo_simbolo.value == 'funcion':
                    funciones = int(funciones) + 1
                elif simbolo.tipo_simbolo.value == 'tipo_dato' and simbolo.tipo_dato == 'struct':
                    structs = int(structs) + 1
                elif 'pkg_' in nombre:
                    imports = int(imports) + 1
                elif simbolo.tipo_dato == 'import':
                    imports = int(imports) + 1
                
                assert isinstance(variables, int)
                assert isinstance(funciones, int)
                assert isinstance(structs, int)
                assert isinstance(imports, int)
        
        self.results_text.insert(tk.END, f"  Registros Totales: {len(self.semantic.tabla_simbolos.simbolos)}\n")
        self.results_text.insert(tk.END, f"  Formatos: ({variables} Vars, {funciones} Funcs, {structs} Structs, {imports} PKGs)\n")
        
        # 7. Resultado final
        self.results_text.insert(tk.END, f"\n[COMPILATION RESULT]\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n")
        
        if resumen_errores['total_errores'] == 0:
            self.results_text.insert(tk.END, "BUILD SUCCESSFUL\n")
            self.status_label.config(text="Status: BUILD SUCCESSFUL")
        else:
            self.results_text.insert(tk.END, f"BUILD FAILED with {resumen_errores['total_errores']} errors.\n")
            self.status_label.config(text=f"Status: BUILD FAILED ({resumen_errores['total_errores']} err)")
        
        # 8. Opciones adicionales
        self.results_text.insert(tk.END, f"\n# Comandos adicionales:\n")
        self.results_text.insert(tk.END, "  [F12] Mostrar Reporte Detallado de Errores\n")
        self.results_text.insert(tk.END, "  [F10] Inspeccionar RAM de Tabla de Símbolos\n")
    
    def analizar_lexico(self):
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No hay código para analizar.\n")
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== ANÁLISIS LÉXICO ===\n\n")
        
        tokens = self.lexer.procesar(codigo)
        for tipo, valor in tokens:
            self.results_text.insert(tk.END, f"<{tipo}, '{valor}'>\n")
        
        self.status_label.config(text="Análisis léxico completado")
    
    def validar_estructura(self):
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No hay código para validar.\n")
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== VALIDACIÓN ESTRUCTURAL ===\n\n")
        
        if self.parser.validar_apertura_cierres(codigo):
            self.results_text.insert(tk.END, "✓ Estructura válida: Paréntesis, corchetes y llaves balanceados correctamente.\n")
            self.status_label.config(text="Estructura válida")
        else:
            self.results_text.insert(tk.END, "✗ Error estructural: Símbolos sin abrir/cerrar o cruzados.\n")
            self.status_label.config(text="Error estructural")
    
    def validar_sintaxis_completa(self):
        """Validación sintáctica completa usando análisis de archivo completo (compilador real)"""
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No hay código para validar.\n")
            return
        
        limpiar_errores()
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, " VALIDACIÓN SINTÁCTICA\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        es_valido = self.parser.validar_archivo_completo(codigo)
        
        errores = self.parser.obtener_errores()
        
        if es_valido and len(errores) == 0:
            self.results_text.insert(tk.END, "No se encontraron errores sintácticos.\n")
            self.results_text.insert(tk.END, "Estructura de bloques correcta (llaves balanceadas).\n")
            self.status_label.config(text="Sintaxis válida (compilador real)")
        else:
            self.results_text.insert(tk.END, f"Se encontraron {len(errores)} errores sintácticos:\n\n")
            
            errores_por_linea: dict[int, list[str]] = {}
            for error in errores:
                if ": " in error:
                    linea_str = error.split(":")[0].replace("Línea ", "")
                    try:
                        linea_num = int(linea_str)
                        if linea_num not in errores_por_linea:
                            errores_por_linea[linea_num] = []
                        errores_por_linea[linea_num].append(error)
                    except ValueError:
                        continue
            
            for linea_num in sorted(errores_por_linea.keys()):
                lineas_codigo = codigo.split('\n')
                if 0 < linea_num <= len(lineas_codigo):
                    linea_codigo = lineas_codigo[linea_num - 1].strip()
                    self.results_text.insert(tk.END, f"Línea {linea_num}: {linea_codigo}\n")
                    
                    for error in errores_por_linea[linea_num]:
                        self.results_text.insert(tk.END, f" {error}\n")
                    self.results_text.insert(tk.END, "\n")
            
            otros_errores = [e for e in errores if not (": " in e and "Línea " in e)]
            if otros_errores:
                self.results_text.insert(tk.END, "Otros errores:\n")
                for error in otros_errores:
                    self.results_text.insert(tk.END, f" {error}\n")
                self.results_text.insert(tk.END, "\n")
            
            self.status_label.config(text=f" {len(errores)} errores sintácticos")
        
        resumen_errores = obtener_resumen_errores()
        if resumen_errores['total_errores'] > 0:
            self.results_text.insert(tk.END, "\n RESUMEN DEL SISTEMA DE ERRORES:\n")
            self.results_text.insert(tk.END, f"Total: {resumen_errores['total_errores']}\n")
            self.results_text.insert(tk.END, f"Sintácticos: {resumen_errores['total_sintacticos']}\n")
            self.results_text.insert(tk.END, f"Semánticos: {resumen_errores['total_semanticos']}\n")
    
    def generar_arbol_parseo(self):
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No hay código para analizar.\n")
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== ÁRBOL DE PARSEO ===\n\n")
        
        tokens = self.lexer.procesar(codigo)
        
        arbol = self.parser.generar_arbol_parseo(tokens)
        
        self.results_text.insert(tk.END, f"Expresión: {codigo}\n\n")
        self.results_text.insert(tk.END, arbol)
        
        self.status_label.config(text="Árbol de parseo generado")
    
    def validar_declaraciones_go(self):
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No hay código para validar.\n")
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== VALIDACIÓN DE DECLARACIONES GO ===\n\n")
        
        self.semantic.variables_encontradas.clear()
        from symbol_table import TablaSimbolos
        self.semantic.tabla_simbolos = TablaSimbolos()
        
        lineas = codigo.split('\n')
        declaraciones_validas: int = 0
        declaraciones_invalidas: int = 0
        lineas_ignoradas: int = 0
        
        # Help Pyre
        assert isinstance(declaraciones_validas, int)
        assert isinstance(declaraciones_invalidas, int)
        assert isinstance(lineas_ignoradas, int)
        
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
                
            tokens = self.lexer.procesar(linea)
            tokens = self.parser.limpiar_tokens(tokens)
            if not tokens:
                continue
                
            es_valido, mensaje, simbolo = self.semantic.validar_declaracion(tokens)
            
            if es_valido:
                self.results_text.insert(tk.END, f"✓ {linea}\n")
                self.results_text.insert(tk.END, f"  {mensaje}\n")
                declaraciones_validas = int(declaraciones_validas) + 1
            elif "no es declaración" in mensaje.lower() or "llamada a función" in mensaje.lower() or "estructura de control" in mensaje.lower() or "línea vacía" in mensaje.lower():
                self.results_text.insert(tk.END, f"○ {linea}\n")
                self.results_text.insert(tk.END, f"  {mensaje}\n")
                lineas_ignoradas = int(lineas_ignoradas) + 1
            else:
                self.results_text.insert(tk.END, f"✗ {linea}\n")
                self.results_text.insert(tk.END, f"  ERROR: {mensaje}\n")
                declaraciones_invalidas = int(declaraciones_invalidas) + 1
            
            assert isinstance(declaraciones_validas, int)
            assert isinstance(declaraciones_invalidas, int)
            assert isinstance(lineas_ignoradas, int)
        
        self.results_text.insert(tk.END, f"\nResumen:\n")
        self.results_text.insert(tk.END, f"✓ Declaraciones válidas: {declaraciones_validas}\n")
        self.results_text.insert(tk.END, f"✗ Declaraciones inválidas: {declaraciones_invalidas}\n")
        if lineas_ignoradas > 0:
            self.results_text.insert(tk.END, f"○ Líneas ignoradas (no son declaraciones): {lineas_ignoradas}\n")
        self.status_label.config(text=f"Validación Go: {declaraciones_validas} válidas, {declaraciones_invalidas} inválidas")
    
    def mostrar_tabla_simbolos(self):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== TABLA COMPLETA DE SÍMBOLOS ===\n\n")
        
        self.semantic.imprimir_tabla_completa()
        
        variables = self.semantic.variables_encontradas
        if variables:
            self.results_text.insert(tk.END, f"\nVariables compatibilidad (set): {len(variables)}\n")
            for var in sorted(variables):
                self.results_text.insert(tk.END, f"  • {var}\n")
        
        self.status_label.config(text="Tabla de símbolos mostrada")
    
    def mostrar_errores_detallados(self):
        """Muestra reporte detallado de errores del sistema"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "REPORTE DETALLADO DE ERRORES\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n\n")
        
        resumen_errores = obtener_resumen_errores()
        
        if resumen_errores['total_errores'] == 0:
            self.results_text.insert(tk.END, "No hay errores registrados.\n")
        else:
            self.results_text.insert(tk.END, f"RESUMEN:\n")
            self.results_text.insert(tk.END, f"Total de errores: {resumen_errores['total_errores']}\n")
            self.results_text.insert(tk.END, f"Sintácticos: {resumen_errores['total_sintacticos']}\n")
            self.results_text.insert(tk.END, f"Semánticos: {resumen_errores['total_semanticos']}\n\n")
            
            from errors import error_manager
            error_manager.imprimir_todos_errores()
        
        self.status_label.config(text="Reporte de errores mostrado")
    
    def limpiar_errores_sistema(self):
        """Limpia todos los errores del sistema"""
        limpiar_errores()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Errores del sistema limpiados.\n")
        self.status_label.config(text="Errores limpiados")
    

    def ver_variables(self):
        variables = self.semantic.variables_encontradas
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== VARIABLES REGISTRADAS (Tabla de Símbolos) ===\n\n")
        
        if variables:
            for var in sorted(variables):
                self.results_text.insert(tk.END, f"• {var}\n")
            self.results_text.insert(tk.END, f"\nTotal: {len(variables)} variables\n")
        else:
            self.results_text.insert(tk.END, "No hay variables registradas.\n")
        
        self.status_label.config(text=f"{len(variables)} variables")
    
    def limpiar_variables(self):
        self.semantic.variables_encontradas.clear()
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Variables limpiadas.\n")
        self.status_label.config(text="Variables eliminadas")
    
    def limpiar_resultados(self):
        self.results_text.delete(1.0, tk.END)
        self.status_label.config(text="Resultados limpiados")
    
    def guardar_analisis(self):
        contenido = self.results_text.get(1.0, tk.END).strip()
        if not contenido:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(contenido)
                messagebox.showinfo("Guardado", f"Análisis guardado en: {file_path}")
                self.status_label.config(text="Análisis guardado")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    def setup_shortcuts(self):
        self.root.bind_all('<Control-n>', lambda e: self.new_file())
        self.root.bind_all('<Control-o>', lambda e: self.open_file())
        self.root.bind_all('<Control-s>', lambda e: self.save_file())
        self.root.bind_all('<F5>', lambda e: self.analizar_lexico())
        self.root.bind_all('<F6>', lambda e: self.validar_estructura())
        self.root.bind_all('<F7>', lambda e: self.generar_arbol_parseo())
        self.root.bind_all('<F8>', lambda e: self.validar_declaraciones_go())
        self.root.bind_all('<Control-y>', lambda e: self.validar_sintaxis_completa())
        self.root.bind_all('<F9>', lambda e: self.compilar_codigo())
        self.root.bind_all('<F10>', lambda e: self.mostrar_tabla_simbolos())
        self.root.bind_all('<F11>', lambda e: self.limpiar_errores_sistema())
        self.root.bind_all('<F12>', lambda e: self.mostrar_errores_detallados())
        self.root.bind_all('<Control-t>', lambda e: self.mostrar_tabla_simbolos())
    
    def show_help(self):
        messagebox.showinfo("Ayuda", 
            "Editor de código para Mini-Go con Sistema de Errores Integrado\n\n"
            "Atajos de teclado:\n"
            "F5: Análisis Léxico\n"
            "F6: Validar Estructura\n"
            "F7: Generar Árbol de Parseo\n"
            "F8: Validar Declaraciones Go\n"
            "F9: Compilación Completa con Errores\n"
            "F10: Mostrar Tabla de Símbolos\n"
            "F11: Limpiar Errores del Sistema\n"
            "F12: Mostrar Errores Detallados\n"
            "Ctrl+T: Mostrar Tabla de Símbolos\n\n"
            "Atajos de archivo:\n"
            "Ctrl+N: Nuevo archivo\n"
            "Ctrl+O: Abrir archivo\n"
            "Ctrl+S: Guardar archivo\n\n"
            "Características del Sistema de Errores:\n"
            "• Detección automática de errores léxicos y semánticos\n"
            "• Clasificación por categorías específicas\n"
            "• Reportes detallados con línea y contexto\n"
            "• Exportación en múltiples formatos (texto, JSON)\n"
            "• Integración completa con el compilador")
    
    def show_about(self):
        messagebox.showinfo("Acerca de", "IDE de Compilación v2.0 - Mini-Go\nSistema de Errores Integrado\nArquitectura modular implementada.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditor(root)
    root.mainloop()
