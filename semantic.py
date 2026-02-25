# semantic.py

class AutomataSemantico:
    def __init__(self):
        self.estado = 'inicio'
        self.prohibidos = {'$', '#', '(', '@'}
        # Tipos de datos válidos
        self.tipos_datos = {'int', 'double', 'str', 'bool'}
        # ESTO ES TU TABLA DE SÍMBOLOS:
        self.variables_encontradas = set() 

    # (Mantuve tu código original de transicion y validar_variable para consistencia)
    def transicion(self, caracter):
        if self.estado == 'inicio':
            if caracter.isalpha() or caracter == '_':
                self.estado = 'valido'
            else:
                self.estado = 'invalido'
        elif self.estado == 'valido':
            if caracter.isalnum() or caracter in '_.:' and caracter not in self.prohibidos:
                self.estado = 'valido'
            else:
                self.estado = 'invalido'

    def validar_variable(self, nombre):
        self.estado = 'inicio'
        for caracter in nombre:
            self.transicion(caracter)
            if self.estado == 'invalido': return False
        return self.estado == 'valido'
    
    def get_descripcion_tipo(self, tipo):
        descripciones = {
            'int': 'tipo de dato entero corto',
            'double': 'tipo de dato entero largo',
            'str': 'tipo de dato cadena',
            'bool': 'tipo de dato booleano'
        }
        return descripciones.get(tipo.lower(), 'tipo de dato desconocido')
    
    def registrar_y_validar_variable(self, tipo_dato, variable):
        # Adaptación de tu lógica de ambigüedad
        descripcion = self.get_descripcion_tipo(tipo_dato)
        
        if variable in self.variables_encontradas:
            return f"{tipo_dato} {variable} // {descripcion}, ERROR: ambigüedad con variable existente"
        else:
            self.variables_encontradas.add(variable)
            return f"{tipo_dato} {variable} // {descripcion}, registrada correctamente"