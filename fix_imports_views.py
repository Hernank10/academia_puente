# -*- coding: utf-8 -*-
"""fix_imports_views.py - Anade los imports que faltan en users/views.py."""
from pathlib import Path
import ast, re

BASE = Path(r"E:\02_proyectos\academia_puente\_original")
f = BASE / "users" / "views.py"
txt = f.read_text(encoding="utf-8")

# Modelos que hacen falta
faltantes = ["Evaluacion", "PreguntaEvaluacion", "OpcionRespuesta", "IntentoEvaluacion"]
print("Modelos que la vista usa pero no estan importados:")
for m in faltantes:
    en_import = False
    for line in txt.splitlines():
        if "from courses.models import" in line or (line.strip().startswith(("    ", "        ")) and line.strip().rstrip(",").replace("(", "").strip() == m):
            pass
    # Buscar en el bloque import
    m_import = re.search(r"from courses\.models import \(([^)]+)\)", txt)
    tiene = False
    if m_import:
        tiene = m in m_import.group(1)
    else:
        # Import de una linea
        m_simple = re.search(r"from courses\.models import (.+)", txt)
        if m_simple:
            tiene = m in m_simple.group(1)
    print("  {}  {}".format("OK " if tiene else "FALTA", m))

# Aplicar fix: agregar al bloque "from courses.models import (...)"
m_import = re.search(r"from courses\.models import \(([^)]+)\)", txt)
if m_import:
    bloque = m_import.group(1)
    agregados = []
    for m in faltantes:
        if m not in bloque:
            bloque = bloque.rstrip()
            if not bloque.endswith(","):
                bloque += ","
            bloque += "\n    " + m + ","
            agregados.append(m)
    if agregados:
        nuevo_bloque = "from courses.models import (" + bloque + "\n)"
        txt = txt[:m_import.start()] + nuevo_bloque + txt[m_import.end():]
        f.write_text(txt, encoding="utf-8")
        print("")
        print("OK: agregados -> {}".format(", ".join(agregados)))
    else:
        print("")
        print("OK: ya estaban todos")
else:
    print("ERROR: no encontre 'from courses.models import (...)'")

# Verificar compilacion
try:
    ast.parse(f.read_text(encoding="utf-8"))
    print("OK: users/views.py compila")
except SyntaxError as e:
    print("ERROR sintaxis: " + str(e))

print("LISTO")