# fusionar_universal.py
"""
Fusiona TODOS los items de jsons_recuperados.json en un único
semilla_ejercicios_full.json, eliminando duplicados.
"""

import json
import os

BASE = "/workspaces/Academia_Puente_Digital"
RECUPERADOS = os.path.join(BASE, "jsons_recuperados.json")
SALIDA = os.path.join(BASE, "semilla_ejercicios_full.json")

def get_first(d, *keys, default=""):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k]:
            v = d[k]
            return v if isinstance(v, str) else str(v)
    return default

def normalizar_item(item, categoria_fallback, idx):
    if not isinstance(item, dict):
        return None

    categoria = get_first(item, "categoria", "category", "tipo",
                          "categoria_nombre", default=categoria_fallback)

    pregunta = get_first(
        item,
        "pregunta", "ejercicio", "exercise", "question",
        "titulo", "titulo_es", "name", "nombre", "element",
        "oracion", "historia", "teoria",
        default=""
    )

    respuesta = get_first(
        item,
        "respuesta", "suggestedAnswer", "self_evaluation",
        "ejercicio_correcto", "answer", "respuesta_correcta",
        "clasificacion", default=""
    )

    if not pregunta:
        return None

    return {
        "id": idx,
        "categoria": categoria or categoria_fallback,
        "pregunta": pregunta[:500],
        "respuesta": respuesta or "(sin respuesta)",
    }

def main():
    print("=" * 70)
    print("FUSIÓN UNIVERSAL")
    print("=" * 70)
    
    with open(RECUPERADOS, encoding="utf-8") as f:
        recuperados = json.load(f)
    
    print("\nArchivos cargados: %d\n" % len(recuperados))
    
    todos = []
    vistos = set()  # (categoria, pregunta) para detectar duplicados
    duplicados = 0
    contador = 1
    
    for nombre, data in recuperados.items():
        items = data["data"] if isinstance(data, dict) and "data" in data else data
        if not isinstance(items, list):
            items = [items]
        
        cat_fallback = nombre.replace(".json", "")[:100]
        agregados = 0
        
        for raw in items:
            norm = normalizar_item(raw, cat_fallback, contador)
            if not norm:
                continue
            
            # Clave para detectar duplicados
            clave = (norm["categoria"][:50], norm["pregunta"][:100])
            if clave in vistos:
                duplicados += 1
                continue
            
            vistos.add(clave)
            todos.append(norm)
            contador += 1
            agregados += 1
        
        print("  %-60s → %3d items" % (nombre[:60], agregados))
    
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print("  Total items únicos: %d" % len(todos))
    print("  Duplicados quitados: %d" % duplicados)
    print()
    print("  💾 %s" % SALIDA)

if __name__ == "__main__":
    main()
