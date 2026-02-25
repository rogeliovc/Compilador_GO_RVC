import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

from lexer import AnalizadorLexico
from parser import AnalizadorSintactico
from semantic import AutomataSemantico

class CodeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador Mini-Go")
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
        
        # Área de texto para resultados
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
        
        self.update_line_numbers()
        self.setup_menu()
    
    def update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        content = self.text_area.get(1.0, tk.END)
        if content:
            if content.endswith('\n'):
                content = content[:-1]
            line_count = content.count('\n') + 1
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
    
    def validar_en_tiempo_real(self):
        linea_actual = self.text_area.get("insert linestart", "insert lineend").strip()
        if linea_actual:
            palabras = linea_actual.split()
            for palabra in palabras:
                if palabra in self.semantic.tipos_datos:
                    for siguiente in palabras[palabras.index(palabra)+1:]:
                        if self.semantic.validar_variable(siguiente):
                            self.semantic.variables_encontradas.add(siguiente)
                            break
    
    def on_mousewheel(self, event=None):
        self.update_line_numbers()
    
    def update_status(self):
        try:
            content = self.text_area.get(1.0, tk.END)
            char_count = len(content) - 1
            line_count = content.count('\n')
            status_text = f"Caracteres: {char_count} | Líneas: {line_count}"
            self.status_label.config(text=status_text)
        except:
            self.status_label.config(text="Listo")
    
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
        menubar.add_cascade(label="Ejecutar", menu=run_menu)
        run_menu.add_command(label="Analizar Léxicamente", accelerator="F5", command=self.analizar_lexico)
        run_menu.add_command(label="Validar Estructura", accelerator="F6", command=self.validar_estructura)
        run_menu.add_command(label="Generar Árbol de Parseo", accelerator="F7", command=self.generar_arbol_parseo)
        run_menu.add_command(label="Compilar", accelerator="F9", command=self.compilar_codigo)
        
        compiler_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Compiladores", menu=compiler_menu)
        compiler_menu.add_command(label="Limpiar Resultados", command=self.limpiar_resultados)
        compiler_menu.add_separator()
        compiler_menu.add_command(label="Guardar Análisis", command=self.guardar_analisis)
        
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
        self.update_line_numbers()
        self.update_file_info()
        self.update_status()
    
    def open_file(self):
        file_types = [("Archivos Python", "*.py"),("Archivos Go", "*.go"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(1.0, file.read())
                self.current_file = file_path
                self.root.title(f"{file_path} - Compilador Mini-Go")
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
    
    def show_help(self):
        messagebox.showinfo("Ayuda", "Editor de código básico para Mini-Go\n\n"
                                  "Atajos:\n"
                                  "F5: Análisis Léxico\nF6: Validar Estructura\nF9: Compilación Completa\n")
    
    def setup_shortcuts(self):
        self.root.bind_all('<Control-n>', lambda e: self.new_file())
        self.root.bind_all('<Control-o>', lambda e: self.open_file())
        self.root.bind_all('<Control-s>', lambda e: self.save_file())
        self.root.bind_all('<F5>', lambda e: self.analizar_lexico())
        self.root.bind_all('<F6>', lambda e: self.validar_estructura())
        self.root.bind_all('<F7>', lambda e: self.generar_arbol_parseo())
        self.root.bind_all('<F9>', lambda e: self.compilar_codigo())
    
    def show_about(self):
        messagebox.showinfo("Acerca de", "IDE de Compilación v2.0 - Mini-Go\nArquitectura modular implementada.")
    
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
    
    def compilar_codigo(self):
        self.analizar_lexico()
        self.results_text.insert(tk.END, "\n")
        self.validar_estructura()
        self.generar_arbol_parseo()
        self.results_text.insert(tk.END, "\n=== COMPILACIÓN COMPLETADA ===\n")
        self.status_label.config(text="Compilación finalizada")
    
    def limpiar_resultados(self):
        self.results_text.delete(1.0, tk.END)
        self.status_label.config(text="Resultados limpiados")
    
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

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditor(root)
    root.mainloop()