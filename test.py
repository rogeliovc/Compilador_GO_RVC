import os
from lexer import AnalizadorLexico
from parser import AnalizadorSintactico
from semantic import AutomataSemantico

with open("test_vars.go", "r") as f:
    text = f.read()

lex = AnalizadorLexico()
par = AnalizadorSintactico()
sem = AutomataSemantico()

tokens, lex_err = lex.analizar(text)
par_err = par.parsear(tokens)

print("Lex errs:", lex_err)
print("Par errs:", par_err)

line_tokens = {}
for tk in tokens:
    line = tk[2]
    if line not in line_tokens:
        line_tokens[line] = []
    line_tokens[line].append(tk)

sem_errs = []
for line, tks in sorted(line_tokens.items()):
    val_err = sem.validar_declaracion_variable(tks, line)
    if val_err:
        sem_errs.extend(val_err)

print("Sem errs:", sem_errs)
