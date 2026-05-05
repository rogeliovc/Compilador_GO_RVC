import tkinter as tk 
from tkinter import ttk, messagebox, filedialog, font, simpledialog
import os
import re
import typing
import shutil
import json

from lexer import AnalizadorLexico
from parser import AnalizadorSintactico
from semantic import AnalizadorSemanticoAST
from symbol_table import TablaSimbolos
from codegen import GeneradorIntermedio
from asm_gen import GeneradorEnsamblador
from errors import limpiar_errores, imprimir_errores, obtener_resumen_errores
from utils import es_identificador_valido, es_tipo_dato, KEYWORDS_GO, TIPOS_BASICOS

class CodeEditor:
    def __init__(self, root):
        # ... (código existente) ...
        
        # Estado para controlar si hubo redimensionamiento reciente
        self._recent_resize = False
        self._resize_time = 0
        self.root = root
        self.root.title("Compilador Mini-Go - Sistema de Errores")
        self.root.geometry("1000x700")
        self.current_file = None

        self.lexer = AnalizadorLexico()
        self.parser = AnalizadorSintactico()
        self.semantic = AnalizadorSemanticoAST()
        self.codegen = GeneradorIntermedio()
        
        # Establecer coordinación entre parser y semantic analyzer
        self.parser.set_semantic_analyzer(self.semantic)
        
        # IDE Components state
        self.tree: typing.Any = None
        self.tree_scroll: typing.Any = None
        self.current_workspace: str = ""
        
        self.style = ttk.Style()
        self.setup_theme()
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')
        
        # La barra de menú nativa maneja las opciones de archivo, edit y compilación

        # --- PanedWindow para dividir la ventana principal ---
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(expand=True, fill='both', padx=5, pady=5)
        
        # --- Sidebar (Left) ---
        self.sidebar_frame = ttk.Frame(self.paned_window, width=200, style='Sidebar.TFrame')
        self.paned_window.add(self.sidebar_frame, weight=0)
        self.setup_sidebar()

        # --- Contenedor Derecho (Editor + Consola) ---
        self.right_container = ttk.PanedWindow(self.paned_window, orient=tk.VERTICAL)
        self.paned_window.add(self.right_container, weight=1)

        # Panel superior para el editor (dentro del contenedor derecho)
        self.editor_frame = ttk.Frame(self.right_container, style='Editor.TFrame')
        self.right_container.add(self.editor_frame, weight=3)
        
        # Panel inferior colapsable para resultados
        self.results_frame = ttk.Frame(self.right_container)
        self.right_container.add(self.results_frame, weight=1)
        
        # El contenedor derecho maneja la división entre el editor y resultados
        # Se elimina el bind de <Configure> para evitar parpadeos molestos.
        
        # Header de la consola para colapsar
        self.console_header = ttk.Frame(self.results_frame, style='Header.TFrame')
        self.console_header.pack(fill=tk.X, side=tk.TOP)
        
        self.console_title = ttk.Label(self.console_header, text="▼ Resultados del Análisis", style='Header.TLabel')
        self.console_title.pack(side=tk.LEFT, padx=5, pady=2)
        self.console_title.bind("<Button-1>", self.toggle_console)
        
        self.console_content = ttk.Frame(self.results_frame)
        self.console_content.pack(fill='both', expand=True)

        self.console_visible = True
        
        # Configuración del Editor de Texto
        editor_font = ('Consolas', 11)
        
        self.line_numbers = tk.Text(self.editor_frame, width=4, padx=5, pady=5,
                                   background='#1e1e1e', foreground='#858585',
                                   font=editor_font, state='disabled',
                                   wrap=tk.NONE, cursor='arrow', bd=0, highlightthickness=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        self.text_area = tk.Text(self.editor_frame, wrap=tk.NONE, font=editor_font, 
                               background='#1e1e1e', foreground='#d4d4d4',
                               insertbackground='#ffffff', selectbackground='#264f78',
                               padx=10, pady=5, yscrollcommand=self.on_textscroll,
                               bd=0, highlightthickness=0)
        self.text_area.pack(side=tk.LEFT, expand=True, fill='both')
        
        self.scrollbar = ttk.Scrollbar(self.editor_frame, orient='vertical',
                                command=self.on_scrollbar)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_area.config(yscrollcommand=self.on_textscroll)
        
        # Configuración de la Consola de Resultados
        self.results_text = tk.Text(self.console_content, wrap=tk.WORD, font=('Consolas', 10),
                                   background='#000000', foreground='#00ff00',
                                   padx=10, pady=10, bd=0, highlightthickness=0)
        self.results_scrollbar = ttk.Scrollbar(self.console_content, orient='vertical',
                                            command=self.results_text.yview)
        self.results_text.config(yscrollcommand=self.results_scrollbar.set)
        
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.pack(side=tk.LEFT, expand=True, fill='both')
        
        # --- Barra de Estado (Bottom) ---
        self.status_bar = ttk.Frame(self.root, style='Status.TFrame')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text=" Listo", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.file_info_label = ttk.Label(self.status_bar, text="Sin guardar   ", style='Status.TLabel')
        self.file_info_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Bindings
        self.text_area.bind('<KeyRelease>', self.on_key_release)
        self.text_area.bind('<MouseWheel>', self.on_mousewheel)
        self.text_area.bind('<Return>', self.on_enter_key)
        
        self.text_area.bind('<Button-1>', lambda e: self.root.after(10, self.highlight_current_line))
        self.text_area.bind('<B1-Motion>', lambda e: self.root.after(10, self.highlight_current_line))
        self.text_area.bind('<Key>', self.on_key_press)
        self.text_area.bind('<Alt-Up>', self.move_line_up)
        self.text_area.bind('<Alt-Down>', self.move_line_down)
        self.text_area.bind('<Tab>', self.on_tab)
        self.text_area.bind('<Shift-Tab>', self.on_shift_tab)
        self.text_area.bind('<ISO_Left_Tab>', self.on_shift_tab)
        
        self.text_area.tag_configure("CurrentLine", background="#2a2d2e")
        
        self.update_line_numbers()
        self.setup_menu()
        self.setup_syntax_highlighting()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.load_config)
        
    def load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ide_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                if 'geometry' in config:
                    self.root.geometry(config['geometry'])
                if 'workspace' in config and os.path.isdir(config['workspace']):
                    self.current_workspace = config['workspace']
                    self.populate_tree()
                if 'sash_sidebar' in config:
                    self.paned_window.sashpos(0, config['sash_sidebar'])
                if 'sash_console' in config:
                    self.right_container.sashpos(0, config['sash_console'])
                    
                if config.get('zoomed', False):
                    try:
                        self.root.state('zoomed')
                    except tk.TclError:
                        self.root.attributes('-zoomed', True)
            except Exception as e:
                print(f"Error loading config: {e}")

    def on_closing(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ide_config.json')
        try:
            is_zoomed = False
            try:
                if self.root.state() == 'zoomed':
                    is_zoomed = True
            except tk.TclError:
                try:
                    if self.root.attributes('-zoomed'):
                        is_zoomed = True
                except tk.TclError:
                    pass
            
            config = {
                'geometry': self.root.geometry(),
                'zoomed': is_zoomed,
                'workspace': self.current_workspace,
                'sash_sidebar': self.paned_window.sashpos(0),
                'sash_console': self.right_container.sashpos(0)
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
            
        self.root.destroy()

    def setup_theme(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colores
        bg_dark = '#252526'
        bg_darker = '#1e1e1e'
        fg_light = '#cccccc'
        accent_blue = '#0e639c'
        accent_blue_hover = '#1177bb'
        
        self.root.configure(bg=bg_darker)
        
        # Configurar estilos de los Frames
        self.style.configure('TFrame', background=bg_darker)
        self.style.configure('Toolbar.TFrame', background=bg_dark)
        self.style.configure('Sidebar.TFrame', background=bg_dark)
        self.style.configure('Header.TFrame', background=accent_blue)
        self.style.configure('Status.TFrame', background=accent_blue)
        
        # Configurar estilos de Labels
        self.style.configure('TLabel', background=bg_darker, foreground=fg_light, font=('Segoe UI', 9))
        self.style.configure('Header.TLabel', background=accent_blue, foreground='white', font=('Segoe UI', 9, 'bold'))
        self.style.configure('Sidebar.TLabel', background=bg_dark, foreground=fg_light, font=('Segoe UI', 10, 'bold'))
        self.style.configure('Status.TLabel', background=accent_blue, foreground='white')
        
        # Configurar estilos de Botones
        self.style.configure('Sidebar.TButton', 
                           background=bg_dark, foreground=fg_light, 
                           borderwidth=0, focuscolor=bg_dark,
                           font=('Segoe UI', 10), padding=5, anchor='w')
        self.style.map('Sidebar.TButton', 
                     background=[('active', '#37373d'), ('pressed', '#0e639c')],
                     foreground=[('active', 'white')])
                     
        self.style.configure('Toolbar.TButton', 
                           background=bg_dark, foreground=fg_light, 
                           borderwidth=0, focuscolor=bg_dark)
        self.style.map('Toolbar.TButton', 
                     background=[('active', '#37373d')])
                     
        # Scrollbars
        self.style.configure('Vertical.TScrollbar', background='#424242', troughcolor=bg_darker, borderwidth=0, arrowcolor=fg_light)



    def setup_treeview_styles(self):
        bg_dark = '#252526'
        bg_darker = '#1e1e1e'
        fg_light = '#cccccc'
        accent_blue = '#0e639c'

        self.style.configure('Treeview', 
                           background=bg_darker, foreground=fg_light, 
                           fieldbackground=bg_darker, borderwidth=0)
        self.style.configure('Treeview.Heading', 
                           background=bg_dark, foreground=fg_light, 
                           borderwidth=0, font=('Segoe UI', 9, 'bold'))
        self.style.map('Treeview', 
                     background=[('selected', '#37373d')], 
                     foreground=[('selected', 'white')])

    def setup_sidebar(self):
        self.setup_treeview_styles()
        
        # Tools header
        explorer_header = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        explorer_header.pack(fill=tk.X, side=tk.TOP)
        
        lbl_title = ttk.Label(explorer_header, text=" EXPLORADOR", style='Sidebar.TLabel')
        lbl_title.pack(side=tk.LEFT, pady=(10, 5), padx=5)
        
        btn_workspace = ttk.Button(explorer_header, text=" 📁 ", command=self.change_workspace, width=4, style='Toolbar.TButton')
        btn_workspace.pack(side=tk.RIGHT, pady=(10, 5), padx=5)

        btn_refresh = ttk.Button(explorer_header, text=" 🔄 ", command=self.populate_tree, width=4, style='Toolbar.TButton')
        btn_refresh.pack(side=tk.RIGHT, pady=(10, 5), padx=2)

        # Treeview
        self.tree = ttk.Treeview(self.sidebar_frame, show='tree', selectmode='browse')
        self.tree.pack(expand=True, fill='both', padx=2, pady=5)
        
        self.tree_scroll = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side='right', fill='y')
        
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.bind('<Double-Button-1>', self.on_tree_double_click)  # Alternativa
        self.tree.bind('<<TreeviewOpen>>', self.on_tree_open)
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        # Agregar binding para diagnóstico
        self.tree.bind('<Button-1>', self.on_tree_single_click)
        
        self.current_workspace = os.getcwd()
        self.populate_tree()

    def change_workspace(self):
        new_dir = filedialog.askdirectory(initialdir=self.current_workspace)
        if new_dir:
            self.current_workspace = new_dir
            self.populate_tree()

    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        root_node = self.tree.insert('', 'end', text=os.path.basename(self.current_workspace), open=True)
        self._populate_node(root_node, self.current_workspace)

    def _populate_node(self, parent, path):
        try:
            dirs = []
            files = []
            for p in os.listdir(path):
                abspath = os.path.join(path, p)
                if os.path.isdir(abspath):
                    dirs.append(p)
                else:
                    files.append(p)
                    
            dirs.sort()
            files.sort()
            
            for d in dirs:
                abspath = os.path.join(path, d)
                oid = self.tree.insert(parent, 'end', text="📁 " + d, tags=(abspath, 'dir'))
                self.tree.insert(oid, 'end', text='...')
                
            for f in files:
                abspath = os.path.join(path, f)
                icon = "📄 "
                self.tree.insert(parent, 'end', text=icon + f, tags=(abspath, 'file'))
        except PermissionError:
            pass
            
    def on_tree_open(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        tags = self.tree.item(item_id, "tags")
        if not tags: return
        abspath = tags[0]
        
        # Remove dummy
        children = self.tree.get_children(item_id)
        if len(children) == 1 and self.tree.item(children[0], "text") == '...':
            self.tree.delete(children[0])
            self._populate_node(item_id, abspath)
            
    def on_tree_single_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            print(f"DEBUG: Single-clicked item_id: {item_id}")
            self.tree.selection_set(item_id)
            self.tree.focus(item_id)
    
    def on_tree_double_click(self, event):
        print(f"DEBUG: Double-click event received: {event}")
        print(f"DEBUG: Event x,y: {event.x}, {event.y}")
        
        # Intentar obtener el item debajo del cursor
        item_id = self.tree.identify_row(event.y)
        
        # Si no se puede identificar por posición, intentar con focus
        if not item_id:
            item_id = self.tree.focus()
        
        if not item_id: 
            print("DEBUG: No item_id found")
            return
        
        print(f"DEBUG: Double-clicked item_id: {item_id}")
        
        # Establecer el focus y selección explícitamente
        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        
        tags = self.tree.item(item_id, "tags")
        print(f"DEBUG: Tags: {tags}")
        
        if tags:
            abspath = tags[0]
            print(f"DEBUG: Absolute path: {abspath}")
            print(f"DEBUG: Is file: {os.path.isfile(abspath)}")
            
            if os.path.isfile(abspath):
                print(f"DEBUG: Loading file: {abspath}")
                self.load_file_content(abspath)
            else:
                print("DEBUG: Not a file, ignoring")
        else:
            print("DEBUG: No tags found")

    def _compilar_desde_arbol(self, abspath, accion):
        self.load_file_content(abspath)
        accion()

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.tree.focus(item_id)
            tags = self.tree.item(item_id, "tags")
            if not tags: return
            abspath = tags[0]
            is_dir = len(tags) > 1 and tags[1] == 'dir'
            
            menu = tk.Menu(self.root, bg='#252526', fg='#cccccc', activebackground='#0e639c', activeforeground='white', tearoff=0, border=0)
            
            if not is_dir and abspath.endswith('.go'):
                menu.add_command(label="▶ Compilar Pipeline Completo", command=lambda: self._compilar_desde_arbol(abspath, self.compilar_codigo))
                menu.add_separator()
                menu.add_command(label="Paso 1: Análisis Léxico", command=lambda: self._compilar_desde_arbol(abspath, self.analizar_lexico))
                menu.add_command(label="Paso 2: Análisis Sintáctico", command=lambda: self._compilar_desde_arbol(abspath, self.validar_estructura))
                
                # Asumo que self.validar_declaraciones_go existe. En caso de que se llame diferente internamente,
                # Python fallaría al llamar a _compilar_desde_arbol, pero en versiones vemos que era invocado desde setup_menu.
                if hasattr(self, 'validar_declaraciones_go'):
                    menu.add_command(label="Paso 3: Análisis Semántico", command=lambda: self._compilar_desde_arbol(abspath, self.validar_declaraciones_go))
                
                menu.add_separator()
            
            if is_dir or item_id == self.tree.get_children()[0]: # Es carpeta o root
                menu.add_command(label="Nuevo Archivo aquí", command=lambda: self.create_new_file_in(abspath))
                menu.add_command(label="Nueva Carpeta aquí", command=lambda: self.create_new_folder_in(abspath))
            else:
                parent_dir = os.path.dirname(abspath)
                menu.add_command(label="Nuevo Archivo aquí", command=lambda: self.create_new_file_in(parent_dir))
            
            if item_id != self.tree.get_children()[0]: # No permitir borrar el root del workspace
                menu.add_command(label="Eliminar", command=lambda: self.delete_item(abspath))
                
            menu.add_separator()
            menu.add_command(label="Actualizar Explorador", command=self.populate_tree)
            
            menu.tk_popup(event.x_root, event.y_root)

    def create_new_file_in(self, path):
        nombre = simpledialog.askstring("Nuevo Archivo", "Nombre del archivo:", parent=self.root)
        if nombre:
            try:
                open(os.path.join(path, nombre), 'w').close()
                self.populate_tree()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def create_new_folder_in(self, path):
        nombre = simpledialog.askstring("Nueva Carpeta", "Nombre de la carpeta:", parent=self.root)
        if nombre:
            try:
                os.makedirs(os.path.join(path, nombre))
                self.populate_tree()
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def delete_item(self, path):
        if messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar {os.path.basename(path)}?"):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.populate_tree()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def toggle_console(self, event=None):
        if self.console_visible:
            self.console_content.pack_forget()
            self.console_title.config(text="▶ Resultados del Análisis")
            self.console_visible = False
        else:
            self.console_content.pack(fill='both', expand=True)
            self.console_title.config(text="▼ Resultados del Análisis")
            self.console_visible = True

    def setup_syntax_highlighting(self):
        """Configura los colores (tags) para el editor de código"""
        self.text_area.tag_configure("Keyword", foreground="#c586c0", font=('Consolas', 11, 'bold')) # Pink/Purple
        self.text_area.tag_configure("Type", foreground="#4ec9b0", font=('Consolas', 11, 'italic')) # Teal
        self.text_area.tag_configure("String", foreground="#ce9178") # Orange/Brown
        self.text_area.tag_configure("Comment", foreground="#6a9955", font=('Consolas', 11, 'italic')) # Green
        self.text_area.tag_configure("Number", foreground="#b5cea8") # Light green
        self.text_area.tag_configure("Function", foreground="#dcdcaa") # Yellow
    
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
        # Guardar posición actual del scroll antes de actualizar
        current_scroll = self.text_area.yview()[0]
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        # Obtener el conteo exacto de líneas directamente de Tkinter
        line_count = int(self.text_area.index('end-1c').split('.')[0])
        if line_count < 1:
            line_count = 1
        
        # Generar números de línea
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert(1.0, line_numbers_text)
        self.line_numbers.config(state='disabled')
        
        # Restaurar posición exacta del scroll después de actualizar
        self.text_area.yview_moveto(current_scroll)
        self.line_numbers.yview_moveto(current_scroll)
    
    def on_textscroll(self, *args):
        self.scrollbar.set(*args)
        # Scroll normal - sincronizar de manera directa sin retardo
        self.line_numbers.yview_moveto(args[0])
    
    def on_scrollbar(self, *args):
        self.text_area.yview(*args)
        # Sincronizamos también la barra de números en la misma invocación
        self.line_numbers.yview(*args)
    
    def on_key_release(self, event=None):
        if event and event.keysym in ['Return', 'BackSpace', 'Delete']:
            self.update_line_numbers()
        self.update_status()
        self.validar_en_tiempo_real()
        self.highlight_syntax()
        self.highlight_current_line()
        
    def on_enter_key(self, event=None):
        """Autoindentación: replica la sangría de la línea anterior"""
        # Obtener posición actual del cursor
        cursor_pos = self.text_area.index(tk.INSERT)
        linea_num = int(cursor_pos.split('.')[0])
        col_num = int(cursor_pos.split('.')[1])
        
        # Obtener línea completa actual
        linea_actual_str = self.text_area.get(f"{linea_num}.0", f"{linea_num}.end")
        
        # Separar parte izquierda y derecha del cursor
        parte_izquierda = linea_actual_str[:col_num]
        parte_derecha = linea_actual_str[col_num:]
        
        # Calcular indentación basada en la parte izquierda
        identacion_coincidencia = re.match(r'^(\s+)', parte_izquierda)
        
        espacio_a_insertar = ""
        if identacion_coincidencia:
            espacio_a_insertar = identacion_coincidencia.group(1)
            
        # Si la parte izquierda termina en {, agregamos sangría extra
        if parte_izquierda.strip().endswith('{'):
            espacio_a_insertar += "    "
            
        # Reemplazar la línea actual con la parte izquierda
        self.text_area.delete(f"{linea_num}.0", f"{linea_num}.end")
        self.text_area.insert(f"{linea_num}.0", parte_izquierda)
        
        # Insertar nueva línea con indentación y parte derecha
        nueva_linea = f"\n{espacio_a_insertar}{parte_derecha}"
        self.text_area.insert("insert", nueva_linea)
        
        # Mover cursor al inicio de la parte derecha en la nueva línea
        nueva_linea_num = linea_num + 1
        nueva_col = len(espacio_a_insertar)
        self.text_area.mark_set(tk.INSERT, f"{nueva_linea_num}.{nueva_col}")
        
        self.update_line_numbers()
        self.update_status()
        self.highlight_syntax()
        self.highlight_current_line()
        return "break"

    def highlight_current_line(self, event=None):
        self.text_area.tag_remove("CurrentLine", "1.0", tk.END)
        self.text_area.tag_add("CurrentLine", "insert linestart", "insert lineend+1c")

    def on_key_press(self, event):
        char = event.char
        pairs = {'{':'}', '[':']', '(':')', '"':'"', "'":"'"}
        if char in pairs:
            self.text_area.insert(tk.INSERT, char + pairs[char])
            self.text_area.mark_set(tk.INSERT, "insert-1c")
            self.root.after(10, self.highlight_current_line)
            return "break"

    def move_line_up(self, event):
        cursor = self.text_area.index(tk.INSERT)
        line = int(cursor.split('.')[0])
        col = int(cursor.split('.')[1])
        if line == 1: return "break"
        text = self.text_area.get(f"{line}.0", f"{line}.end")
        self.text_area.delete(f"{line}.0", f"{line}.end+1c")
        self.text_area.insert(f"{line-1}.0", text + "\n")
        self.text_area.mark_set(tk.INSERT, f"{line-1}.{col}")
        self.highlight_current_line()
        return "break"

    def move_line_down(self, event):
        cursor = self.text_area.index(tk.INSERT)
        line = int(cursor.split('.')[0])
        col = int(cursor.split('.')[1])
        last = int(self.text_area.index("end-1c").split('.')[0])
        if line == last: return "break"
        text = self.text_area.get(f"{line}.0", f"{line}.end")
        self.text_area.delete(f"{line}.0", f"{line}.end+1c")
        self.text_area.insert(f"{line+1}.0", text + "\n")
        self.text_area.mark_set(tk.INSERT, f"{line+1}.{col}")
        self.highlight_current_line()
        return "break"

    def on_tab(self, event):
        try:
            start = self.text_area.index("sel.first")
            end = self.text_area.index("sel.last")
            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0])
            if end.split('.')[1] == '0' and end_line > start_line:
                end_line -= 1
            for l in range(start_line, end_line + 1):
                self.text_area.insert(f"{l}.0", "    ")
            return "break"
        except tk.TclError:
            self.text_area.insert(tk.INSERT, "    ")
            return "break"

    def on_shift_tab(self, event):
        try:
            start = self.text_area.index("sel.first")
            end = self.text_area.index("sel.last")
            start_line = int(start.split('.')[0])
            end_line = int(end.split('.')[0])
            if end.split('.')[1] == '0' and end_line > start_line:
                end_line -= 1
        except tk.TclError:
            start_line = int(self.text_area.index(tk.INSERT).split('.')[0])
            end_line = start_line

        for l in range(start_line, end_line + 1):
            line_text = self.text_area.get(f"{l}.0", f"{l}.end")
            if line_text.startswith("    "):
                self.text_area.delete(f"{l}.0", f"{l}.4")
            elif line_text.startswith("\t"):
                self.text_area.delete(f"{l}.0", f"{l}.1")
        return "break"
    
    def validar_en_tiempo_real(self):
        # Real-time logic validation might need adjustment, skipped for AST simplicity.
        pass
    
    def on_mousewheel(self, event=None):
        # No actualizar números de línea durante el scroll para evitar desalineación
        # Los números de línea solo se actualizan cuando el contenido cambia
        pass
    
    def on_pane_resize(self, event=None):
        # Esta función ha sido descartada para evitar carga de CPU excesiva y desincronización
        pass
    
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
        # Opciones comunes para los menús para evitar transparencias en Linux/Arch
        menu_options = {
            'bg': '#252526',
            'fg': '#cccccc',
            'activebackground': '#0e639c',
            'activeforeground': 'white',
            'border': 0
        }
        menubar = tk.Menu(self.root, **menu_options)
        self.root.config(menu=menubar)
        
        # 1. Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0, **menu_options)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nuevo", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Abrir...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Guardar", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Guardar como...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # 2. Menú Editar
        edit_menu = tk.Menu(menubar, tearoff=0, **menu_options)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Deshacer", accelerator="Ctrl+Z", command=lambda: self.text_area.event_generate("<<Undo>>"))
        edit_menu.add_command(label="Rehacer", accelerator="Ctrl+Y", command=lambda: self.text_area.event_generate("<<Redo>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cortar", accelerator="Ctrl+X", command=lambda: self.text_area.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copiar", accelerator="Ctrl+C", command=lambda: self.text_area.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Pegar", accelerator="Ctrl+V", command=lambda: self.text_area.event_generate("<<Paste>>"))
        
        # 3. Menú Ejecutar
        run_menu = tk.Menu(menubar, tearoff=0, **menu_options)
        menubar.add_cascade(label="Ejecutar", menu=run_menu)
        run_menu.add_command(label="Compilar Pipeline Completo", accelerator="F9", command=self.compilar_codigo)
        run_menu.add_command(label="Limpiar Resultados", command=self.limpiar_resultados)
        
        # 4. Menú Compiladores
        compiler_menu = tk.Menu(menubar, tearoff=0, **menu_options)
        menubar.add_cascade(label="Compiladores", menu=compiler_menu)
        compiler_menu.add_command(label="Análisis Léxico", accelerator="F5", command=self.analizar_lexico)
        compiler_menu.add_command(label="Análisis Sintáctico", accelerator="F7", command=self.generar_arbol_parseo)
        compiler_menu.add_command(label="Análisis Semántico", command=self.analizar_semantico)
        compiler_menu.add_command(label="Código Intermedio (TAC)", command=self.generar_tac)
        compiler_menu.add_command(label="Código Ensamblador (x86_64)", command=self.generar_asm)
        
        # 5. Menú Variables
        var_menu = tk.Menu(menubar, tearoff=0, **menu_options)
        menubar.add_cascade(label="Variables", menu=var_menu)
        var_menu.add_command(label="Ver Tabla de Símbolos", accelerator="F10", command=self.mostrar_tabla_simbolos)
        
        # 6. Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0, **menu_options)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Ayuda", command=self.show_help)
        help_menu.add_command(label="Acerca de...", command=self.show_about)
        
        self.setup_shortcuts()
    
    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("Nuevo archivo - Compilador Mini-Go")
        
        self.semantic = AnalizadorSemanticoAST()
        limpiar_errores()
        
        self.update_line_numbers()
        self.update_file_info()
        self.update_status()
    
    def load_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, file.read())
            self.current_file = file_path
            self.root.title(f"{file_path} - Compilador Mini-Go")
            self.highlight_syntax()
            
            self.semantic = AnalizadorSemanticoAST()
            limpiar_errores() 
            
            self.update_line_numbers()
            self.update_file_info()
            self.update_status()
            self.status_label.config(text=f"Archivo abierto: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

    def open_file(self):
        file_types = [("Archivos Go", "*.go"), ("Archivos Python", "*.py"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            self.load_file_content(file_path)
    
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
        
        self.semantic = AnalizadorSemanticoAST()
        self.parser = AnalizadorSintactico()
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "Iniciando compilación (AST-Based Mini-Go Compiler)\n")
        self.results_text.insert(tk.END, "-" * 60 + "\n\n")
        
        # 1. Análisis léxico
        self.results_text.insert(tk.END, "[Fase 1] Análisis Léxico (Tokenizado)\n")
        tokens_totales = self.lexer.procesar(codigo)
        
        self.results_text.insert(tk.END, f"  > Total de tokens identificados: {len(tokens_totales)}\n")
        
        # 2. Análisis sintáctico estructural
        self.results_text.insert(tk.END, "\n[Fase 2] Análisis Sintáctico (Parser AST)\n")
        arbol = self.parser.parsear_programa(tokens_totales)
        errores_sintacticos = self.parser.obtener_errores()
        
        if errores_sintacticos:
            self.results_text.insert(tk.END, "  > Status: (ERROR) Se detectaron errores sintácticos:\n")
            for error in errores_sintacticos:
                self.results_text.insert(tk.END, f"    - {error}\n")
        else:
            self.results_text.insert(tk.END, "  > Status: Sintaxis de bloques estructuralmente válida.\n")

        # 3. Análisis semántico
        self.results_text.insert(tk.END, "\n[Fase 3] Análisis Semántico (AST Visitor)\n")
        
        self.semantic.procesar(arbol)
        errores_semanticos = self.semantic.obtener_errores()
        
        if errores_semanticos:
            self.results_text.insert(tk.END, "  > Status: (ERROR) Errores semánticos detectados:\n")
            for error in errores_semanticos:
                self.results_text.insert(tk.END, f"    - {error}\n")
        else:
             self.results_text.insert(tk.END, "  > Status: Semántica válida.\n")
             
             # 4. Generación de Código Intermedio (TAC)
             self.results_text.insert(tk.END, "\n[Fase 4] Generación de Código Intermedio (TAC)\n")
             self.codegen.generar(arbol)
             self.results_text.insert(tk.END, "  > Status: TAC generado con éxito.\n")
             self.results_text.insert(tk.END, "\n--- CÓDIGO INTERMEDIO ---\n")
             self.results_text.insert(tk.END, self.codegen.obtener_codigo() + "\n")
        
        # 4. Resumen
        self.results_text.insert(tk.END, f"\n[Tabla de Símbolos]\n")
        
        class Resumen:
            variables: int = 0
            funciones: int = 0
            structs: int = 0
            imports: int = 0
        resumen = Resumen()
        
        for nombre, simbolos_lista in self.semantic.tabla_simbolos.simbolos.items():
            for simbolo in simbolos_lista:
                if simbolo.tipo_simbolo.value == 'variable':
                    resumen.variables += 1
                elif simbolo.tipo_simbolo.value == 'funcion':
                    resumen.funciones += 1
                elif simbolo.tipo_simbolo.value == 'tipo_dato' and simbolo.tipo_dato == 'struct':
                    resumen.structs += 1
                elif 'pkg_' in nombre:
                    resumen.imports += 1
                elif getattr(simbolo, 'tipo_dato', None) == 'import':
                    resumen.imports += 1
        
        self.results_text.insert(tk.END, f"  Registros Totales: {len(self.semantic.tabla_simbolos.simbolos)}\n")
        self.results_text.insert(tk.END, f"  Formatos: ({resumen.variables} Vars, {resumen.funciones} Funcs, {resumen.structs} Structs, {resumen.imports} PKGs)\n")
        
        # 5. Resultado final
        self.results_text.insert(tk.END, f"\n[COMPILATION RESULT]\n")
        self.results_text.insert(tk.END, "=" * 60 + "\n")
        
        total_errores = len(errores_sintacticos) + len(errores_semanticos)
        
        if total_errores == 0:
            self.results_text.insert(tk.END, "BUILD SUCCESSFUL\n")
            self.status_label.config(text="Status: BUILD SUCCESSFUL")
        else:
            self.results_text.insert(tk.END, f"BUILD FAILED with {total_errores} errors.\n")
            self.status_label.config(text=f"Status: BUILD FAILED ({total_errores} err)")
        
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
        for tipo, valor, linea in tokens:
            self.results_text.insert(tk.END, f"<{tipo}, '{valor}'>\n")
        
        self.status_label.config(text="Análisis léxico completado")
    

    def generar_arbol_parseo(self):
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No hay código para analizar.\n")
            return
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== ÁRBOL DE PARSEO (AST) ===\n\n")
        
        tokens_totales = self.lexer.procesar(codigo)
                
        arbol = self.parser.parsear_programa(tokens_totales)
        
        # Un simple print de AST usando __str__
        def print_ast(nodo, nivel=0):
            if nodo is None: return ""
            res = "  " * nivel + str(nodo) + "\n"
            for h in nodo.hijos:
                res += print_ast(h, nivel + 1)
            return res
            
        self.results_text.insert(tk.END, print_ast(arbol))
        self.status_label.config(text="Árbol de parseo generado")
    

    def mostrar_tabla_simbolos(self):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== TABLA COMPLETA DE SÍMBOLOS ===\n\n")
        
        # self.semantic.imprimir_tabla_completa() - Console print removed for UI
        variables = [s.nombre for s in self.semantic.tabla_simbolos.simbolos.values() for s in s if s.tipo_simbolo.value == 'variable']
        variables = set(variables)
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
        self.root.bind_all('<F7>', lambda e: self.generar_arbol_parseo())
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
            "F7: Generar Árbol de Parseo\n"
            "F9: Compilación Completa (Pipeline AST)\n"
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

    def generar_tac(self):
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo: return
        tokens = self.lexer.procesar(codigo)
        arbol = self.parser.parsear_programa(tokens)
        self.semantic = AnalizadorSemanticoAST()
        self.semantic.procesar(arbol)
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== CÓDIGO INTERMEDIO (TAC) ===\n\n")
        self.codegen.generar(arbol)
        self.results_text.insert(tk.END, self.codegen.obtener_codigo())

    def generar_asm(self):
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo: return
        
        tokens = self.lexer.procesar(codigo)
        arbol = self.parser.parsear_programa(tokens)
        self.semantic = AnalizadorSemanticoAST()
        self.semantic.procesar(arbol)
        
        # Generar TAC primero
        instrucciones_tac = self.codegen.generar(arbol)
        
        # Traducir a Ensamblador (pasamos la tabla de símbolos para detectar tamaños de arreglos)
        asm_gen = GeneradorEnsamblador(instrucciones_tac, self.semantic.tabla_simbolos)
        codigo_asm = asm_gen.generar()
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=== CÓDIGO ENSAMBLADOR (x86_64 / NASM) ===\n\n")
        self.results_text.insert(tk.END, codigo_asm)
        self.status_label.config(text="Código ensamblador generado")

    def analizar_semantico(self):
        self.limpiar_resultados()
        codigo = self.text_area.get(1.0, tk.END).strip()
        if not codigo: return

        limpiar_errores()
        tokens = self.lexer.procesar(codigo)
        arbol = self.parser.parsear_programa(tokens)
        
        # Primero validamos que no haya errores sintácticos
        if self.parser.obtener_errores():
            self.results_text.insert(tk.END, "=== ANÁLISIS SEMÁNTICO ===\n\n")
            self.results_text.insert(tk.END, "[!] Detenido: Se encontraron errores sintácticos previos.\n")
            self.mostrar_errores_detallados()
            return

        # Ejecutamos el análisis semántico
        self.semantic = AnalizadorSemanticoAST()
        es_valido = self.semantic.procesar(arbol)
        
        self.results_text.insert(tk.END, "=== ANÁLISIS SEMÁNTICO ===\n\n")
        if es_valido:
            self.results_text.insert(tk.END, "[OK] Validación semántica completada con éxito.\n")
            
            # Extraer estadísticas de la tabla de símbolos
            vars_count = 0
            funcs_count = 0
            pkgs_count = 0
            
            for lista in self.semantic.tabla_simbolos.simbolos.values():
                for s in lista:
                    if s.tipo_dato == "import" or s.tipo_dato == "package": pkgs_count += 1
                    elif s.tipo_simbolo.value == "variable": vars_count += 1
                    elif s.tipo_simbolo.value == "funcion": funcs_count += 1
            
            self.results_text.insert(tk.END, f"\nDetalles del Análisis:\n")
            self.results_text.insert(tk.END, f"  • Variables procesadas: {vars_count}\n")
            self.results_text.insert(tk.END, f"  • Funciones validadas: {funcs_count}\n")
            self.results_text.insert(tk.END, f"  • Paquetes/Imports: {pkgs_count}\n")
            self.results_text.insert(tk.END, f"  • Chequeo de tipos: Correcto\n")
            self.results_text.insert(tk.END, f"  • Control de flujo: Consistente\n")
            
            self.status_label.config(text="Semántica válida")
        else:
            self.results_text.insert(tk.END, "[ERROR] Se encontraron problemas semánticos.\n")
            self.mostrar_errores_detallados()
            self.status_label.config(text="Errores semánticos detectados")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditor(root)
    root.mainloop()
