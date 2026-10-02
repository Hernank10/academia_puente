# arreglar_jsons2.py
import json
import os

CARPETA = "templates/ejercicios_completos-lengua-castellana"

ROTOS = [
    "Técnicas 51-75_Expositivo Científico.json",
    "Técnicas 61 a 100 - Narrativa Española.json",
    "Técnicas 7-25 (continuación narrativo).json",
    "Técnicas 76-100_Argumentativo Científico.json",
    "Técnicas_ 26-50_Descriptivo Científico.json",
    "100 técnicas de Redacción Científica Hispanoamericana.json",
]

def extraer_todos(texto):
    """Extrae TODOS los objetos JSON posibles del texto."""
    
    # Estrategia A: envolver en [] si empieza con { y termina con ]
    t = texto.strip()
    if t.startswith("{") and t.endswith("]"):
        intento = "[" + t[:-1] + "]"
        try:
            return json.loads(intento), "envolvuelto en []"
        except json.JSONDecodeError:
            pass
    
    # Estrategia B: si empieza con { y termina con ]}, extraer el array interno
    # Buscar el primer [ y el último ]
    i = t.find("[")
    j = t.rfind("]")
    if i >= 0 and j > i:
        intento = t[i:j+1]
        try:
            return json.loads(intento), "array interno extraido"
        except json.JSONDecodeError:
            pass
    
    # Estrategia C: si empieza con { y termina con } y hay comas entre objetos
    # Envolver en []
    if t.startswith("{") and t.endswith("}"):
        intento = "[" + t + "]"
        try:
            return json.loads(intento), "envuelto objeto único en []"
        except json.JSONDecodeError:
            pass
    
    # Estrategia D: parsear cada objeto con raw_decode
    resultados = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(t):
        # Saltar espacios y comas
        while idx < len(t) and t[idx] in " \t\n\r,":
            idx += 1
        if idx >= len(t):
            break
        try:
            obj, fin = decoder.raw_decode(t, idx)
            resultados.append(obj)
            idx = fin
        except json.JSONDecodeError:
            idx += 1
    
    if resultados:
        # Aplanar: si cada obj es un dict, devolver lista
        if all(isinstance(r, dict) for r in resultados):
            return resultados, "raw_decode multiple (%d objetos)" % len(resultados)
    
    # Estrategia E: JSON directo
    try:
        return json.loads(t), "directo"
    except json.JSONDecodeError as e:
        return None, "no se pudo: %s" % e.msg

def main():
    print("Intentando arreglar %d JSONs rotos...\n" % len(ROTOS))
    
    arreglados = {}
    for nombre in ROTOS:
        path = os.path.join(CARPETA, nombre)
        if not os.path.exists(path):
            print("⚠️  No existe: %s\n" % nombre)
            continue
        
        print("=" * 60)
        print("ARCHIVO:", nombre)
        print("=" * 60)
        
        with open(path, encoding="utf-8") as f:
            texto = f.read()
        
        data, metodo = extraer_todos(texto)
        
        if data is None:
            print("  ❌ %s\n" % metodo)
            continue
        
        if isinstance(data, list):
            n = len(data)
        elif isinstance(data, dict):
            # Buscar arrays internos
            if "tecnicas" in data and isinstance(data["tecnicas"], list):
                data = data["tecnicas"]
                n = len(data)
                metodo += " + .tecnicas extraido"
            else:
                n = 1
        else:
            n = 0
        
        print("  ✅ %s" % metodo)
        print("  📦 %d items\n" % n)
        arreglados[nombre] = data
    
    print("=" * 60)
    print("RESUMEN: %d/%d arreglados" % (len(arreglados), len(ROTOS)))
    print("=" * 60)
    for nombre, data in arreglados.items():
        n = len(data) if isinstance(data, list) else 1
        print("  ✅ %-55s → %d items" % (nombre[:55], n))
    
    with open("jsons_arreglados.json", "w", encoding="utf-8") as f:
        json.dump(arreglados, f, ensure_ascii=False, indent=2)
    
    print("\n💾 Guardado en: jsons_arreglados.json")

if __name__ == "__main__":
    main()
