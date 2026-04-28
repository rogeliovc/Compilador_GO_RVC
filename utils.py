KEYWORDS_GO = {
    'package', 'import', 'func', 'var', 'const', 'if', 'else', 'for', 'break', 
    'continue', 'return', 'struct', 'interface', 'type', 'map', 'range', 'chan', 
    'select', 'defer', 'go', 'int', 'string', 'float', 'bool', 'true', 'false', 'nil',
    'switch', 'case', 'default'
}

TIPOS_BASICOS = [
    'int', 'int8', 'int16', 'int32', 'int64',
    'uint', 'uint8', 'uint16', 'uint32', 'uint64',
    'float32', 'float64', 'complex64', 'complex128',
    'string', 'bool', 'byte', 'rune', 'void'
]

PALABRAS_RESERVADAS = [
    'break', 'case', 'chan', 'const', 'continue', 'default',
    'defer', 'else', 'fallthrough', 'for', 'func', 'go',
    'goto', 'if', 'import', 'interface', 'map', 'package',
    'range', 'return', 'select', 'struct', 'switch', 'type',
    'var', 'true', 'false', 'nil', 'iota'
]

def es_identificador_valido(nombre):
    if not nombre:
        return False
    if nombre[0].isdigit():
        return False
    if not all(c.isalnum() or c == '_' for c in nombre):
        return False
    if nombre in KEYWORDS_GO:
        return False
    return True

import re

def es_tipo_dato(token):
    if not token:
        return False
    # Remover todos los corchetes y números internos, por ej. [5], [3][3], []
    token_limpio = re.sub(r'\[.*?\]', '', token)
    token_limpio = token_limpio.lstrip('*')
    return token_limpio in TIPOS_BASICOS

def es_palabra_reservada(token):
    return token in PALABRAS_RESERVADAS
