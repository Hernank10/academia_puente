# normalizar_ejercicios.py
import json
import glob
import os

CARPETA = "templates/ejercicios_completos-lengua-castellana"
SALIDA = "semilla_ejercicios.json"

def get_first(d, *keys, default=""):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k]:
            v = d[k]
            return v if isinstance(v, str) else str(v)
    return default

def extraer_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("tecnicas", "historias", "items", "ejercicios",
                    "preguntas", "datos", "data", "contenido", "registros"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return []

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
        "pregunta": pregunta,
        "respuesta": respuesta or "(sin respuesta)",
    }

def main():
    archivos = sorted(glob.glob(os.path.join(CARPETA, "*.json")))
    print("Encontrados %d archivos JSON.\n" % len(archivos))

    salida = []
    contador = 1
    saltados = []

    for path in archivos:
        nombre = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            saltados.append((nombre, "JSON invalido: %s" % e.msg))
            continue
        except Exception as e:
            saltados.append((nombre, "Error: %s: %s" % (type(e).__name__, e)))
            continue

        cat_fallback = nombre.replace(".json", "")[:100]
        if isinstance(data, dict):
            if "titulo" in data:
                cat_fallback = str(data["titulo"])[:100]
            elif "title" in data:
                cat_fallback = str(data["title"])[:100]

        items = extraer_items(data)
        agregados = 0
        for raw in items:
            norm = normalizar_item(raw, cat_fallback, contador)
            if norm:
                salida.append(norm)
                contador += 1
                agregados += 1

        estado = "OK" if agregados else "!!"
        print("  [%s] %-65s -> %d items" % (estado, nombre[:65], agregados))

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print("\nTotal: %d ejercicios -> %s" % (len(salida), SALIDA))
    if saltados:
        print("\nArchivos saltados (%d):" % len(saltados))
        for n, e in saltados:
            print("   - %s: %s" % (n[:60], e))

if __name__ == "__main__":
    main()
