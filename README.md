# Compilador Mini-Go

Un compilador completo para el lenguaje Go con detección avanzada de errores.

## 🏗️ Arquitectura

### Componentes Principales:
- **lexer.py** - Análisis léxico y tokenización
- **parser.py** - Análisis sintáctico y validación de estructura
- **semantic.py** - Análisis semántico y validación de tipos
- **symbol_table.py** - Gestión de tabla de símbolos
- **errors.py** - Sistema de detección y reporte de errores
- **ast_nodes.py** - Nodos para Árbol de Sintaxis Abstracta
- **main_gui.py** - Interfaz gráfica del compilador

## 🚀 Uso

### Iniciar la GUI:
```bash
python main_gui.py
```

### Funciones Principales:
- **F5**: Análisis léxico
- **F6**: Validación estructural
- **F7**: Generar árbol de parseo
- **F8**: Validar declaraciones Go
- **Ctrl+Y**: Validar sintaxis completa
- **F9**: Compilación con errores
- **F10**: Mostrar tabla de símbolos
- **F11**: Limpiar errores del sistema
- **F12**: Mostrar errores detallados
- **Ctrl+E**: Exportar errores

## 🔍 Detección de Errores

### Errores Sintácticos:
- Punto y coma faltante
- Declaraciones incompletas
- Identificadores inválidos
- Símbolos desbalanceados
- Operadores no existentes
- Uso incorrecto de keywords

### Errores Semánticos:
- Tipos incompatibles
- Redefinición de variables
- Variables no declaradas
- Errores de ámbito

## 📋 Estructura del Proyecto

```
Compilador_GO_RVC/
├── lexer.py              # Tokenización del código
├── parser.py              # Análisis sintáctico
├── semantic.py            # Análisis semántico
├── symbol_table.py        # Tabla de símbolos
├── errors.py              # Sistema de errores
├── ast_nodes.py           # Nodos AST
└── main_gui.py            # Interfaz gráfica
```

## 🎯 Características

- ✅ Detección automática de errores
- ✅ Reportes detallados por línea
- ✅ Clasificación de errores por tipo
- ✅ Interfaz gráfica intuitiva
- ✅ Atajos de teclado para todas las funciones
- ✅ Exportación de errores en múltiples formatos

## 🚧 Próximos Pasos

Para convertir en compilador real:
1. Generación de código intermedio (IR)
2. Optimización de código
3. Generación de ensamblador
4. Linker y generación de código máquina
