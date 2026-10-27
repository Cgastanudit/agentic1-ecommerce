import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.router.graph import graph

CASOS_PATH = Path("tests/casos_router.json")


def main():
    with open(CASOS_PATH, encoding="utf-8") as f:
        casos = json.load(f)

    aciertos = 0
    fallados = []

    print(f"{'Mensaje':<45} {'Esperado':<12} {'Obtenido':<12} {'Resultado':<10} Motivo")
    print("-" * 110)

    for caso in casos:
        mensaje = caso["mensaje"]
        esperado = caso["esperado"]

        estado_inicial = {
            "messages": [("user", mensaje)],
            "mensaje": mensaje,
            "ruta": "",
            "motivo": "",
            "respuesta": "",
            "saltos": [],
        }
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}
        resultado = graph.invoke(estado_inicial, config=config)

        obtenido = resultado.get("ruta", "")
        motivo = resultado.get("motivo", "")
        ok = obtenido == esperado
        marca = "OK" if ok else "XX"

        if ok:
            aciertos += 1
        else:
            fallados.append({"mensaje": mensaje, "esperado": esperado, "obtenido": obtenido})

        print(f"{mensaje:<45} {esperado:<12} {obtenido:<12} {marca:<10} {motivo}")

    total = len(casos)
    porcentaje = (aciertos / total) * 100

    print("-" * 110)
    print(f"Aciertos: {aciertos}/{total} ({porcentaje:.1f}%)")

    if fallados:
        print("\nCasos fallados:")
        for f in fallados:
            print(f"  - '{f['mensaje']}' | esperado: {f['esperado']} | obtenido: {f['obtenido']}")
    else:
        print("\nTodos los casos pasaron.")


if __name__ == "__main__":
    main()
