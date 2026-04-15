from symbol_table import TablaSimbolos, TipoSimbolo, Ambito, Simbolo
from utils import es_identificador_valido, es_tipo_dato

class AutomataSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.variables_encontradas = set()
        
        # Estado para manejar bloques de constantes
        self.en_bloque_const = False 
        
        # Estado para manejar bloques switch y sus casos
        self.en_bloque_switch = False
        self.casos_switch_actual = set()
        
        # Estado para manejar bucles for y su ámbito
        self.en_bloque_for = False
        self.variables_for_locales = set()  # Variables declaradas dentro del for

    def validar_llamada_funcion(self, tokens, linea):
        """Validar si las llamadas a función usan funciones existentes"""
        errores = []
        
        # Buscar patrón: ID . ID ( ... ) - objeto.metodo()
        for i in range(len(tokens) - 2):
            if (tokens[i][0] == "TKN ID" and 
                tokens[i+1][1] == "." and 
                tokens[i+2][0] == "TKN ID"):
                
                objeto = tokens[i][1]
                metodo = tokens[i+2][1]
                
                # Validar si el objeto es un paquete importado
                if not self.tabla_simbolos.existe_simbolo(objeto):
                    errores.append(f"Línea {linea}: SEMÁNTICA - Paquete '{objeto}' no importado o no existe")
                    continue
                
                # Validar funciones comunes de fmt
                if objeto == "fmt":
                    funciones_fmt_validas = ["Print", "Println", "Printf", "Scan", "Scanln", "Scanf"]
                    
                    # Caso especial: fmt.Printl (error común por falta de 'n' en Println)
                    if metodo == "Printl":
                        errores.append(f"Línea {linea}: SEMÁNTICA - Función 'Printl' no existe - se esperaba 'Println'")
                    elif metodo not in funciones_fmt_validas:
                        errores.append(f"Línea {linea}: SEMÁNTICA - Función 'fmt.{metodo}' no existe")
        
        return errores

    def notificar_bucle_for_detectado(self, tokens, linea):
        """Recibir notificación del parser sobre bucle for detectado y gestionar ámbito semántico"""
        if not tokens or tokens[0][1].lower() != 'for':
            return
        
        # Extraer inicialización para detectar variables locales
        semicolons = sum(1 for t in tokens if t[1] == ';')
        
        if semicolons == 2:
            # Extraer la inicialización (primera parte)
            partes = []
            actual = []
            for t in tokens[1:]:  # Ignorar el 'for'
                if t[1] == ';':
                    partes.append(actual)
                    actual = []
                elif t[1] == '{':
                    break  # Llegamos al cuerpo del for
                else:
                    actual.append(t)
            if actual:
                partes.append(actual)
            
            if len(partes) >= 1:
                init_tokens = partes[0]  # La inicialización está en la primera parte
                
                # Detectar variables declaradas con := en la inicialización
                if any(t[1] == ':=' for t in init_tokens):
                    # Entrar al ámbito del for
                    self.en_bloque_for = True
                    self.tabla_simbolos.entrar_ambito_for()
                    
                    # Registrar las variables locales del for
                    for i, token in enumerate(init_tokens):
                        if token[1] == ':=' and i > 0:
                            var_name = init_tokens[i-1][1]
                            if var_name not in self.variables_for_locales:
                                self.variables_for_locales.add(var_name)
                                # Registrar variable en el ámbito local del for
                                self.tabla_simbolos.agregar_variable(var_name, "inferido", linea, es_declaracion_corta=True)
    
    def notificar_condicional_detectado(self, tokens, linea):
        """Recibir notificación del parser sobre condicionales detectados"""
        if not tokens:
            return
        
        # Detectar switch para gestión de casos duplicados
        if any(t[1].lower() == 'switch' for t in tokens):
            self.en_bloque_switch = True
            self.casos_switch_actual = set()
        
        # Detectar case dentro de switch
        elif self.en_bloque_switch and any(t[1].lower() == 'case' for t in tokens):
            idx_case = next(i for i, t in enumerate(tokens) if t[1].lower() == 'case')
            valor_case = ""
            for t in tokens[idx_case+1:]:
                if t[1] in [':', '{']:
                    break
                valor_case += t[1] + " "
            
            valor_case = valor_case.strip()
            
            if valor_case in self.casos_switch_actual:
                # Error de caso duplicado se manejará en validación semántica
                pass
            elif valor_case:
                self.casos_switch_actual.add(valor_case)
        
        # Detectar default (no necesita gestión especial, solo validación sintáctica)
        elif any(t[1].lower() == 'default' for t in tokens):
            pass  # La validación sintáctica la maneja el parser
        
        # Detectar if (no necesita gestión semántica especial)
        elif any(t[1].lower() == 'if' for t in tokens):
            pass  # La validación sintáctica la maneja el parser
    
    def validar_declaracion(self, tokens):
        return self.tabla_simbolos.validar_patron_declaracion(tokens)
    
    def imprimir_tabla_completa(self):
        self.tabla_simbolos.imprimir_tabla()
    
    def validar_declaracion_variable(self, tokens, linea):
        if not tokens:
            return []
        
        errores = []
        
        # Ya no se maneja la detección de for aquí, ahora el parser notifica al semantic
        # a través de notificar_bucle_for_detectado()
        
        # Validación semántica de variables usadas fuera de ámbito
        for t in tokens:
            if t[0] == 'TKN ID' and t[1] in self.variables_for_locales:
                # Si no estamos en un bucle for y la variable fue declarada en un for anterior
                if not self.en_bloque_for and not any(t[1].lower() == 'for' for t in tokens):
                    # Verificar si la variable solo existe en ámbito local
                    simbolo = self.tabla_simbolos.buscar_simbolo(t[1])
                    if simbolo and simbolo.ambito.value == 'local':
                        errores.append(f"Línea {linea}: SEMÁNTICA - Variable '{t[1]}' declarada en bucle for usada fuera de ámbito")
        
        # Validación de declaraciones var
        if tokens and tokens[0][1] == 'var':
            if len(tokens) < 3:
                errores.append(f"Línea {linea}: Declaración var incompleta")
                return errores
            
            if len(tokens) >= 4:
                nombre = tokens[1][1]
                tipo = tokens[2][1] if len(tokens) > 2 else ""
                
                if not es_tipo_dato(tipo) and not self.tabla_simbolos.existe_simbolo(tipo) and tipo != "":
                    errores.append(f"Línea {linea}: SEMÁNTICA - Tipo de dato no reconocido '{tipo}' para la variable '{nombre}'")
                elif self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    if simbolo_existente.tipo_dato != tipo:
                        errores.append(f"Línea {linea}: AMBIGÜEDAD - Variable '{nombre}' declarada previamente como '{simbolo_existente.tipo_dato}' y ahora como '{tipo}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, tipo, linea, es_declaracion_corta=False)

        # Manejar bloques de constantes: const ( Min = 1; Max = 100 )
        if tokens[0][1] == 'const' and len(tokens) > 1 and tokens[1][0] == 'TKN PAREN_A':
            # Inicio de bloque const
            self.en_bloque_const = True
            return errores  # No hay error en la apertura del bloque
        
        elif tokens[0][1] == 'const':
            if len(tokens) < 3:
                errores.append(f"Línea {linea}: Declaración const incompleta")
                return errores
            
            # const PI = 3.14159
            if len(tokens) >= 4:
                nombre = tokens[1][1]
                # Las constantes en Go pueden inferir el tipo del valor
                # Por ahora, registramos como tipo "constante"
                
                if self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    errores.append(f"Línea {linea}: AMBIGÜEDAD - Constante '{nombre}' ya declarada previamente como '{simbolo_existente.tipo_dato}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, "constante", linea, es_declaracion_corta=False)
        
        # Si estamos dentro de un bloque const y encontramos el cierre
        elif self.en_bloque_const and any(t[0] == 'TKN PAREN_C' for t in tokens):
            self.en_bloque_const = False
            return errores
        
        # Si estamos dentro de un bloque const, manejar declaraciones internas
        elif self.en_bloque_const and len(tokens) >= 2 and any(t[1] == '=' for t in tokens):
            # Min = 1 o Max = 100 dentro de bloque const
            pos_igual = next(i for i, t in enumerate(tokens) if t[1] == '=')
            if pos_igual > 0:
                nombre = tokens[pos_igual - 1][1]
                valor = tokens[pos_igual + 1][1] if pos_igual + 1 < len(tokens) else ""
                
                # Si no hay valor, podría ser una constante con valor implícito (iota)
                if self.tabla_simbolos.existe_simbolo(nombre):
                    simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                    errores.append(f"Línea {linea}: AMBIGÜEDAD - Constante '{nombre}' ya declarada previamente como '{simbolo_existente.tipo_dato}'")
                else:
                    self.tabla_simbolos.agregar_variable(nombre, "constante", linea, es_declaracion_corta=False)
            else:
                errores.append(f"Línea {linea}: Declaración de constante inválida")

        # Validación semántica de casos switch duplicados
        if self.en_bloque_switch and any(t[1].lower() == 'case' for t in tokens):
            idx_case = next(i for i, t in enumerate(tokens) if t[1].lower() == 'case')
            valor_case = ""
            for t in tokens[idx_case+1:]:
                if t[1] in [':', '{']:
                    break
                valor_case += t[1] + " "
            
            valor_case = valor_case.strip()
            
            if valor_case in self.casos_switch_actual:
                errores.append(f"Línea {linea}: SEMÁNTICA - Caso duplicado '{valor_case}' en el bloque switch")
        
        elif any((t[1] == ':=') for t in tokens):
            pos = next((i for i, t in enumerate(tokens) if (t[1] == ':=')), -1)
            if pos == 0 or pos >= len(tokens) - 1:
                errores.append(f"Línea {linea}: Declaración corta inválida")
            else:
                nombre = tokens[pos-1][1]
                if es_identificador_valido(nombre):
                    # En Go, := crea una nueva variable (declaración corta)
                    # Solo es error si ya existe y estamos en el mismo ámbito
                    if self.tabla_simbolos.existe_simbolo(nombre):
                        # Verificar si es realmente una redeclaración en el mismo ámbito
                        simbolo_existente = self.tabla_simbolos.buscar_simbolo(nombre)
                        # En Go, := puede redeclarar variables solo en ámbitos diferentes
                        # Por ahora, permitimos la declaración corta sin marcar como duplicado
                        pass
                    # Registrar nueva variable con tipo inferido (declaración corta)
                    self.tabla_simbolos.agregar_variable(nombre, "inferido", linea, es_declaracion_corta=True)
        
        tiene_asignacion = any(t[0] == 'TKN ASIGN' for t in tokens)
        tiene_var = any(t[1] == 'var' for t in tokens)
        tiene_walrus = any(t[0] == 'TKN WALRUS' for t in tokens)

        # ERROR: Variable local del for usada fuera de ámbito
        for t in tokens:
            if t[0] == 'TKN ID' and t[1] in self.variables_for_locales:
                # Si no estamos en un bucle for y la variable fue declarada en un for anterior
                if not self.en_bloque_for and not any(t[1].lower() == 'for' for t in tokens):
                    # Verificar si la variable solo existe en ámbito local
                    simbolo = self.tabla_simbolos.buscar_simbolo(t[1])
                    if simbolo and simbolo.ambito.value == 'local':
                        errores.append(f"Línea {linea}: SEMÁNTICA - Variable '{t[1]}' no declarada en este ámbito (fue declarada dentro de un bucle for)")

        if tiene_asignacion or tiene_walrus:
            asign_token = next(t[0] for t in tokens if t[0] in ['TKN ASIGN', 'TKN WALRUS'])
            pos_asign = next(i for i, t in enumerate(tokens) if t[0] == asign_token)
            
            if tiene_asignacion and not tiene_var:
                lhs_tokens = tokens[:pos_asign]
                for t in lhs_tokens:
                    if t[0] == 'TKN ID' and not self.tabla_simbolos.existe_simbolo(t[1]):
                        errores.append(f"Línea {linea}: SEMÁNTICA - Variable '{t[1]}' no declarada siendo asignada")
            
            rhs_tokens = tokens[pos_asign+1:]
            for t in rhs_tokens:
                if t[0] == 'TKN ID':
                    val = t[1]
                    if '.' in val:
                        base = val.split('.')[0]
                        if not self.tabla_simbolos.existe_simbolo(base):
                            errores.append(f"Línea {linea}: SEMÁNTICA - Base indefinida '{base}' al intentar acceder a atributo en '{val}'")
                    elif not self.tabla_simbolos.existe_simbolo(val) and not es_tipo_dato(val) and val not in ['true', 'false']:
                        errores.append(f"Línea {linea}: SEMÁNTICA - Símbolo '{val}' no declarado siendo usado en expresión")

        return errores
    
    def salir_ambito_for(self):
        """Salir del ámbito de un bucle for y limpiar variables locales"""
        if self.en_bloque_for:
            self.tabla_simbolos.salir_ambito_for()
            self.tabla_simbolos.limpiar_ambito_local()
            self.variables_for_locales.clear()
            self.en_bloque_for = False
    
    def limpiar_variables(self):
        self.variables_encontradas.clear()
        self.tabla_simbolos = TablaSimbolos()
        self.variables_for_locales.clear()
        self.en_bloque_for = False