from typing import List

class ErrorManager:
    def __init__(self):
        self.errores_sintacticos = {
            'lexicos': [],      # Errores de tokenización
            'estructurales': [], # Errores de estructura (paréntesis, llaves, etc.)
            'patrones': []      # Errores de patrones de declaración
        }
        
        self.errores_semanticos = {
            'declaraciones': [],   # Errores en declaraciones de variables/funciones
            'tipos': [],          # Errores de tipos de datos
            'ambitos': [],        # Errores de ámbito (scope)
            'redefinicion': [],   # Errores de redefinición de símbolos
            'uso': []            # Errores de uso incorrecto de símbolos
        }
        
        self.contador_errores = {
            'sintacticos': 0,
            'semanticos': 0,
            'total': 0
        }
    
    def agregar_error_sintactico(self, categoria, mensaje, linea=0, columna=0, contexto=""):
        error = {
            'mensaje': mensaje,
            'linea': linea,
            'columna': columna,
            'contexto': contexto,
            'tipo': 'sintactico',
            'categoria': categoria,
            'timestamp': self._get_timestamp()
        }
        
        if categoria in self.errores_sintacticos:
            self.errores_sintacticos[categoria].append(error)
            self.contador_errores['sintacticos'] = int(self.contador_errores['sintacticos']) + 1
            self.contador_errores['total'] = int(self.contador_errores['total']) + 1
        else:
            raise ValueError(f"Categoría sintáctica inválida: {categoria}")
    
    def agregar_error_semantico(self, categoria, mensaje, linea=0, columna=0, contexto="", simbolo=None):
        error = {
            'mensaje': mensaje,
            'linea': linea,
            'columna': columna,
            'contexto': contexto,
            'tipo': 'semantico',
            'categoria': categoria,
            'simbolo': simbolo,
            'timestamp': self._get_timestamp()
        }
        
        if categoria in self.errores_semanticos:
            self.errores_semanticos[categoria].append(error)
            self.contador_errores['semanticos'] += 1
            self.contador_errores['total'] += 1
        else:
            raise ValueError(f"Categoría semántica inválida: {categoria}")
    
    def limpiar_errores(self):
        for categoria in self.errores_sintacticos:
            self.errores_sintacticos[categoria] = []

        
        for categoria in self.errores_semanticos:
            self.errores_semanticos[categoria] = []
        
        self.contador_errores = {
            'sintacticos': 0,
            'semanticos': 0,
            'total': 0
        }
    
    def obtener_errores_sintacticos(self, categoria=None):

        if categoria:
            return self.errores_sintacticos.get(categoria, [])
        else:
            todos_errores = []
            for cat, errores in self.errores_sintacticos.items():
                todos_errores.extend(errores)
            return todos_errores
    
    def obtener_errores_semanticos(self, categoria=None):
        if categoria:
            return self.errores_semanticos.get(categoria, [])
        else:
            todos_errores = []
            for cat, errores in self.errores_semanticos.items():
                todos_errores.extend(errores)
            return todos_errores
    
    def obtener_todos_errores(self):
        return self.obtener_errores_sintacticos() + self.obtener_errores_semanticos()
    
    def hay_errores(self):
        return self.contador_errores['total'] > 0
    
    def obtener_resumen(self):  
        return {
            'total_sintacticos': self.contador_errores['sintacticos'],
            'total_semanticos': self.contador_errores['semanticos'],
            'total_errores': self.contador_errores['total'],
            'detalle_sintacticos': {
                cat: len(errores) for cat, errores in self.errores_sintacticos.items()
            },
            'detalle_semanticos': {
                cat: len(errores) for cat, errores in self.errores_semanticos.items()
            }
        }
    
    def imprimir_errores_sintacticos(self, categoria=None):
        errores = self.obtener_errores_sintacticos(categoria)
        
        if not errores:
            print(" No hay errores sintácticos")
            return
        
        print(f" ERRORES SINTÁCTICOS ({len(errores)}):")
        print("=" * 60)
        
        for i, error in enumerate(errores, 1):
            ubicacion = f"Línea {error['linea']}"
            if error['columna'] > 0:
                ubicacion += f", Columna {error['columna']}"
            
            print(f"{i}. [{error['categoria'].upper()}] {error['mensaje']}")
            print(f"    {ubicacion}")
            if error['contexto']:
                print(f"   Contexto: {error['contexto']}")
            print()
    
    def imprimir_errores_semanticos(self, categoria=None):
        errores = self.obtener_errores_semanticos(categoria)
        
        if not errores:
            print(" No hay errores semánticos")
            return
        
        print(f" ERRORES SEMÁNTICOS ({len(errores)}):")
        print("=" * 60)
        
        for i, error in enumerate(errores, 1):
            ubicacion = f"Línea {error['linea']}"
            if error['columna'] > 0:
                ubicacion += f", Columna {error['columna']}"
            
            print(f"{i}. [{error['categoria'].upper()}] {error['mensaje']}")
            print(f"   {ubicacion}")
            if error['contexto']:
                print(f"   Contexto: {error['contexto']}")
            if error['simbolo']:
                print(f"   Símbolo: {error['simbolo']}")
            print()
    
    def imprimir_todos_errores(self):
        print("=" * 80)
        print(" REPORTE COMPLETO DE ERRORES")
        print("=" * 80)
        
        resumen = self.obtener_resumen()
        print(f" Total de errores: {resumen['total_errores']}")
        print(f" Sintácticos: {resumen['total_sintacticos']}")
        print(f" Semánticos: {resumen['total_semanticos']}")
        print()
        
        self.imprimir_errores_sintacticos()
        print()
        self.imprimir_errores_semanticos()
    
    def exportar_errores(self, formato="texto"):
        if formato == "texto":
            return self._exportar_texto()
        raise ValueError(f"Formato no soportado: {formato}")
    
    def _exportar_texto(self):
        resultado: List[str] = []
        resultado.append("REPORTE DE ERRORES - COMPILADOR MINI-GO")
        resultado.append("=" * 50)
        
        resumen = self.obtener_resumen()
        assert isinstance(resumen, dict)
        
        total_err = str(resumen.get('total_errores', 0))
        sintacticos_err = str(resumen.get('total_sintacticos', 0))
        semanticos_err = str(resumen.get('total_semanticos', 0))
        
        resultado.append(f"Total errores: {total_err}")
        resultado.append(f"Sintácticos: {sintacticos_err}")
        resultado.append(f"Semánticos: {semanticos_err}")
        resultado.append("")
        
        # Errores sintácticos
        for categoria_nombre, errores_lista in self.errores_sintacticos.items():
            assert isinstance(categoria_nombre, str)
            assert isinstance(errores_lista, list)
            
            if errores_lista:
                resultado.append(f"ERRORES SINTÁCTICOS - {categoria_nombre.upper()}:")
                for e_dict in errores_lista:
                    assert isinstance(e_dict, dict)
                    l_num = str(e_dict.get('linea', 0))
                    m_text = str(e_dict.get('mensaje', ''))
                    resultado.append(f"  Línea {l_num}: {m_text}")
                resultado.append("")
        
        # Errores semánticos
        for categoria_nombre, errores_lista in self.errores_semanticos.items():
            assert isinstance(categoria_nombre, str)
            assert isinstance(errores_lista, list)
            
            if errores_lista:
                resultado.append(f"ERRORES SEMÁNTICOS - {categoria_nombre.upper()}:")
                for e_dict in errores_lista:
                    assert isinstance(e_dict, dict)
                    l_num = str(e_dict.get('linea', 0))
                    m_text = str(e_dict.get('mensaje', ''))
                    resultado.append(f"  Línea {l_num}: {m_text}")
                resultado.append("")
        
        return "\n".join(resultado)

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

error_manager = ErrorManager()

def agregar_error_lexico(mensaje, linea=0, columna=0, contexto=""):
    error_manager.agregar_error_sintactico('lexicos', mensaje, linea, columna, contexto)

def agregar_error_estructural(mensaje, linea=0, columna=0, contexto=""):
    error_manager.agregar_error_sintactico('estructurales', mensaje, linea, columna, contexto)

def agregar_error_patron(mensaje, linea=0, columna=0, contexto=""):
    error_manager.agregar_error_sintactico('patrones', mensaje, linea, columna, contexto)

def agregar_error_declaracion(mensaje, linea=0, columna=0, contexto="", simbolo=None):
    error_manager.agregar_error_semantico('declaraciones', mensaje, linea, columna, contexto, simbolo)

def agregar_error_tipo(mensaje, linea=0, columna=0, contexto="", simbolo=None):
    error_manager.agregar_error_semantico('tipos', mensaje, linea, columna, contexto, simbolo)

def agregar_error_ambito(mensaje, linea=0, columna=0, contexto="", simbolo=None):
    error_manager.agregar_error_semantico('ambitos', mensaje, linea, columna, contexto, simbolo)

def agregar_error_redefinicion(mensaje, linea=0, columna=0, contexto="", simbolo=None):
    error_manager.agregar_error_semantico('redefinicion', mensaje, linea, columna, contexto, simbolo)

def agregar_error_uso(mensaje, linea=0, columna=0, contexto="", simbolo=None):
    error_manager.agregar_error_semantico('uso', mensaje, linea, columna, contexto, simbolo)

def limpiar_errores():
    error_manager.limpiar_errores()

def obtener_resumen_errores():
    return error_manager.obtener_resumen()

def imprimir_errores():
    error_manager.imprimir_todos_errores()