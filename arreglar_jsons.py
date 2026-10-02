# arreglar_jsons.py
import json
import os
import re

CARPETA = "templates/ejercicios_completos-lengua-castellana"

ROTOS = [
    "Técnicas 51-75_Expositivo Científico.json",
    "Técnicas 61 a 100 - Narrativa Española.json",
    "Técnicas 7-25 (continuación narrativo).json",
    "Técnicas 76-100_Argumentativo Científico.json",
    "Técnicas_ 26-50_Descriptivo Científico.json",
    "100 técnicas de Redacción Científica Hispanoamericana.json",
]

def intentar_parsear(texto):
    """Intenta varias estrategias para parsear un JSON roto."""
    
    # Estrategia 1: tal cual
    try:
        return json.loads(texto), "directo"
    except json.JSONDecodeError:
        pass
    
    # Estrategia 2: envolver en array (si empieza con { y termina con ])
    if texto.lstrip().startswith("{") and texto.rstrip().endswith("]"):
        intento = "[" + texto.rstrip()[:-1] + "]"
        try:
            return json.loads(intento), "envolvuelto en []"
        except json.JSONDecodeError:
            pass
    
    # Estrategia 3: quitar último ] si no hay [
    if texto.count("[") == 0 and texto.count("]") > 0:
        intento = "[" + texto.replace("]", "", 1) + "]"
        try:
            return json.loads(intento), "corchete suelto arreglado"
        except json.JSONDecodeError:
            pass
    
    # Estrategia 4: buscar el primer [ y tomar desde ahí hasta el último ]
    match_inicio = texto.find("[")
    match_fin = texto.rfind("]")
    if match_inicio >= 0 and match_fin > match_inicio:
        intento = texto[match_inicio:match_fin+1]
        try:
            return json.loads(intento), "extraido del rango [ ... ]"
        except json.JSONDecodeError:
            pass
    
    # Estrategia 5: intentar quitar "extra data" - solo el primer JSON
    try:
        decoder = json.JSONDecoder()
        obj, idx = decoder.raw_decode(texto.lstrip())
        return obj, "primer JSON valido extraido"
    except json.JSONDecodeError:
        pass
    
    return None, "no se pudo arreglar"

def procesar(path):
    nombre = os.path.basename(path)
    print("=" * 60)
    print("ARCHIVO:", nombre)
    print("=" * 60)
    
    with open(path, encoding="utf-8") as f:
        texto = f.read()
    
    print("  Primeros 30 chars:", repr(texto[:30]))
    print("  Últimos 30 chars:", repr(texto[-30:]))
    
    data, metodo = intentar_parsear(texto)
    
    if data is None:
        print("  ❌ No se pudo arreglar")
        return None
    
    # Contar items
    if isinstance(data, list):
        n = len(data)
    elif isinstance(data, dict):
        n = 1
    else:
        n = 0
    
    print("  ✅ Arreglado con: %s" % metodo)
    print("  📦 %d items extraíbles" % n)
    return data

def main():
    print("Intentando arreglar %d JSONs rotos...\n" % len(ROTOS))
    
    arreglados = {}
    for nombre in ROTOS:
        path = os.path.join(CARPETA, nombre)
        if not os.path.exists(path):
            print("⚠️  No existe: %s" % nombre)
            continue
        data = procesar(path)
        if data:
            arreglados[nombre] = data
        print()
    
    # Guardar los arreglados
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for nombre, data in arreglados.items():
        print("  ✅ %s" % nombre)
    
    with open("jsons_arreglados.json", "w", encoding="utf-8") as f:
        json.dump(arreglados, f, ensure_ascii=False, indent=2)
    
    print("\n💾 Guardado en: jsons_arreglados.json")

if __name__ == "__main__":
    main()
