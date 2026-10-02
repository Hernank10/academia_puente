# recuperador_json.py
"""
Recuperador universal de archivos JSON rotos.

Prueba múltiples estrategias para parsear archivos que fallan
con json.loads() estándar. Guarda los recuperados con éxito.
"""

import json
import os
import re
import glob
import sys

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────

CARPETA = "templates/ejercicios_completos-lengua-castellana"
SALIDA = "jsons_recuperados.json"
REPORTE = "reporte_recuperacion.txt"


# ─────────────────────────────────────────────────────────────
# ESTRATEGIAS DE REPARACIÓN
# ─────────────────────────────────────────────────────────────

def estrategia_directa(texto):
    """Intenta parsear tal cual."""
    try:
        return json.loads(texto), "directo"
    except json.JSONDecodeError:
        return None, None


def estrategia_envolver_array(texto):
    """Si empieza con { y termina con ], envolver en []."""
    t = texto.strip()
    if t.startswith("{") and t.endswith("]"):
        intento = "[" + t[:-1] + "]"
        try:
            return json.loads(intento), "envuelto en []"
        except json.JSONDecodeError:
            pass
    return None, None


def estrategia_extraer_array_interno(texto):
    """Buscar primer [ y último ] y extraer el contenido."""
    i = texto.find("[")
    j = texto.rfind("]")
    if i >= 0 and j > i:
        intento = texto[i:j+1]
        try:
            return json.loads(intento), "array interno extraido"
        except json.JSONDecodeError:
            pass
    return None, None


def estrategia_envolver_objeto(texto):
    """Si empieza con { y termina con }, envolver en []."""
    t = texto.strip()
    if t.startswith("{") and t.endswith("}"):
        intento = "[" + t + "]"
        try:
            return json.loads(intento), "objeto envuelto en []"
        except json.JSONDecodeError:
            pass
    return None, None


def estrategia_raw_decode_multiple(texto):
    """Parsear objetos JSON uno a uno con raw_decode."""
    resultados = []
    decoder = json.JSONDecoder()
    idx = 0
    n = len(texto)
    while idx < n:
        # Saltar espacios y comas
        while idx < n and texto[idx] in " \t\n\r,":
            idx += 1
        if idx >= n:
            break
        try:
            obj, fin = decoder.raw_decode(texto, idx)
            resultados.append(obj)
            idx = fin
        except json.JSONDecodeError:
            # Buscar siguiente { posible
            siguiente = texto.find("{", idx + 1)
            if siguiente == -1:
                break
            idx = siguiente
    if resultados and all(isinstance(r, dict) for r in resultados):
        return resultados, "raw_decode multiple (%d objetos)" % len(resultados)
    return None, None


def estrategia_limpiar_comillas(texto):
    """Escapa comillas dobles internas en valores string."""
    lineas = texto.split('\n')
    arregladas = []
    for linea in lineas:
        # Solo procesar líneas con formato: "clave": "valor..." (con cierre y coma/llave)
        m = re.match(r'^(\s*"[^"]+"\s*:\s*")(.*)("(?:,|\s*$))', linea)
        if m:
            ini, contenido, cierre = m.groups()
            contenido_escapado = contenido.replace('"', '\\"')
            linea = ini + contenido_escapado + cierre
        arregladas.append(linea)
    intento = '\n'.join(arregladas)
    try:
        return json.loads(intento), "comillas internas escapadas"
    except json.JSONDecodeError:
        pass
    return None, None


def estrategia_quitar_comas_finales(texto):
    """Quita comas finales antes de ] o } (trailing commas)."""
    intento = re.sub(r',(\s*[\]\}])', r'\1', texto)
    try:
        return json.loads(intento), "comas finales quitadas"
    except json.JSONDecodeError:
        pass
    return None, None


def estrategia_reemplazar_comillas_simples(texto):
    """Reemplaza comillas simples por dobles (cuando todo usa ')."""
    try:
        return json.loads(texto.replace("'", '"')), "comillas simples -> dobles"
    except json.JSONDecodeError:
        pass
    return None, None


def estrategia_cortar_al_primer_objeto(texto):
    """Toma solo el primer objeto JSON válido."""
    decoder = json.JSONDecoder()
    try:
        obj, idx = decoder.raw_decode(texto.lstrip())
        return obj, "primer JSON valido"
    except json.JSONDecodeError:
        return None, None


def estrategia_limpiar_bom(texto):
    """Quita BOM UTF-8 (a veces aparece como \ufeff al inicio)."""
    intento = texto.lstrip('\ufeff')
    try:
        return json.loads(intento), "BOM quitado"
    except json.JSONDecodeError:
        pass
    return None, None


# Lista ordenada de estrategias a probar
ESTRATEGIAS = [
    ("directo", estrategia_directa),
    ("bom", estrategia_limpiar_bom),
    ("comillas_internas", estrategia_limpiar_comillas),
    ("comas_finales", estrategia_quitar_comas_finales),
    ("envolver_array", estrategia_envolver_array),
    ("array_interno", estrategia_extraer_array_interno),
    ("envolver_objeto", estrategia_envolver_objeto),
    ("comillas_simples", estrategia_reemplazar_comillas_simples),
    ("raw_decode_multi", estrategia_raw_decode_multiple),
    ("cortar_al_primero", estrategia_cortar_al_primer_objeto),
]


# ─────────────────────────────────────────────────────────────
# LÓGICA PRINCIPAL
# ─────────────────────────────────────────────────────────────

def extraer_items(data):
    """Extrae lista de items de cualquier estructura."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("tecnicas", "historias", "items", "ejercicios",
                    "preguntas", "datos", "data", "contenido", "registros"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return []


def recuperar_archivo(path):
    """Intenta recuperar un archivo con todas las estrategias."""
    nombre = os.path.basename(path)
    
    try:
        with open(path, encoding="utf-8") as f:
            texto = f.read()
    except UnicodeDecodeError:
        try:
            with open(path, encoding="latin-1") as f:
                texto = f.read()
            encoding = "latin-1"
        except Exception as e:
            return None, "no se pudo leer: %s" % e
    except Exception as e:
        return None, "error de lectura: %s" % e
    
    # Probar cada estrategia
    for nombre_est, funcion in ESTRATEGIAS:
        data, metodo = funcion(texto)
        if data is not None:
            items = extraer_items(data)
            if items:
                return {
                    "data": items,
                    "metodo": metodo or nombre_est,
                    "total": len(items),
                }, None
            else:
                # Parseó pero sin items
                return {
                    "data": [],
                    "metodo": "%s (sin items)" % (metodo or nombre_est),
                    "total": 0,
                }, None
    
    return None, "ninguna estrategia funcionó"


def main():
    print("=" * 70)
    print("RECUPERADOR UNIVERSAL DE JSON")
    print("=" * 70)
    print("Carpeta: %s" % CARPETA)
    print()
    
    archivos = sorted(glob.glob(os.path.join(CARPETA, "*.json")))
    print("Encontrados %d archivos .json\n" % len(archivos))
    
    validos = []
    recuperados = []
    fallidos = []
    vacios = []
    
    resultados = {}
    
    for path in archivos:
        nombre = os.path.basename(path)
        
        # 1. ¿Es válido tal cual?
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            items = extraer_items(data)
            if items:
                validos.append(nombre)
                resultados[nombre] = {"data": items, "metodo": "directo (ya válido)"}
                print("  ✅ %-60s → %d items" % (nombre[:60], len(items)))
            else:
                vacios.append(nombre)
                print("  ⚪ %-60s → 0 items" % nombre[:60])
        except json.JSONDecodeError:
            # 2. Intentar recuperar
            resultado, error = recuperar_archivo(path)
            if resultado:
                recuperados.append(nombre)
                resultados[nombre] = resultado
                print("  🔧 %-60s → %d items (%s)" % (
                    nombre[:60], resultado["total"], resultado["metodo"]))
            else:
                fallidos.append(nombre)
                print("  ❌ %-60s → %s" % (nombre[:60], error))
        except Exception as e:
            fallidos.append(nombre)
            print("  ❌ %-60s → %s" % (nombre[:60], e))
    
    # Guardar todo
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    # Reporte
    total_items = sum(len(v["data"]) for v in resultados.values())
    
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print("  Válidos:      %3d" % len(validos))
    print("  Recuperados:  %3d" % len(recuperados))
    print("  Vacíos:       %3d" % len(vacios))
    print("  Fallidos:     %3d" % len(fallidos))
    print("  ─────────────────")
    print("  Archivos OK:  %3d" % (len(validos) + len(recuperados)))
    print("  Total items:  %3d" % total_items)
    print()
    print("  💾 %s" % SALIDA)
    
    if fallidos:
        print()
        print("  ⚠️  Fallidos:")
        for n in fallidos:
            print("     - %s" % n)
    
    # Reporte en texto
    with open(REPORTE, "w", encoding="utf-8") as f:
        f.write("REPORTE DE RECUPERACIÓN\n")
        f.write("=" * 70 + "\n\n")
        f.write("VÁLIDOS (%d):\n" % len(validos))
        for n in validos:
            f.write("  ✓ %s\n" % n)
        f.write("\nRECUPERADOS (%d):\n" % len(recuperados))
        for n in recuperados:
            r = resultados[n]
            f.write("  🔧 %s (%d items, %s)\n" % (n, r["total"], r["metodo"]))
        f.write("\nVACÍOS (%d):\n" % len(vacios))
        for n in vacios:
            f.write("  ⚪ %s\n" % n)
        f.write("\nFALLIDOS (%d):\n" % len(fallidos))
        for n in fallidos:
            f.write("  ❌ %s\n" % n)
    
    print("  📄 %s" % REPORTE)


if __name__ == "__main__":
    main()
