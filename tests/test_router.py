import json
import uuid
from pathlib import Path

import pytest
from src.router.graph import graph

CASOS_PATH = Path("tests/casos_router.json")
MINIMO_ACIERTOS = 13


def _cargar_casos():
    with open(CASOS_PATH, encoding="utf-8") as f:
        return json.load(f)


casos = _cargar_casos()


@pytest.mark.parametrize("caso", casos, ids=lambda c: c["mensaje"][:40])
def test_router_caso(caso):
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
    assert obtenido == esperado, (
        f"Mensaje: {mensaje!r}\n"
        f"Esperado: {esperado}\n"
        f"Obtenido: {obtenido}\n"
        f"Motivo: {resultado.get('motivo', '')}"
    )


def test_router_minimo_aciertos():
    aciertos = 0
    total = len(casos)
    fallados = []

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
        if obtenido == esperado:
            aciertos += 1
        else:
            fallados.append((mensaje, esperado, obtenido, resultado.get("motivo", "")))

    porcentaje = (aciertos / total) * 100
    print(f"\nAciertos router: {aciertos}/{total} ({porcentaje:.1f}%)")
    if fallados:
        print("Fallados:")
        for mensaje, esperado, obtenido, motivo in fallados:
            print(f"  - {mensaje!r} | esperado={esperado} | obtenido={obtenido} | motivo={motivo}")

    assert aciertos >= MINIMO_ACIERTOS, (
        f"Se requieren al menos {MINIMO_ACIERTOS} aciertos de {total}, "
        f"pero solo hubo {aciertos}."
    )
