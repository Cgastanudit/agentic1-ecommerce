import argparse
import importlib
import uuid


def cargar_grafo(nombre_agente):
    modulo = importlib.import_module(f"src.{nombre_agente}.graph")
    return getattr(modulo, "graph", None) or getattr(modulo, "compiled", None)


def main():
    parser = argparse.ArgumentParser(description="Ejecuta un agente LangGraph")
    parser.add_argument("nombre_agente", help="Nombre del agente (carpeta en src/)")
    parser.add_argument("mensaje", help="Mensaje de entrada")
    parser.add_argument("--saltos", action="store_true", help="Imprime los nodos visitados")
    parser.add_argument("--diagrama", action="store_true", help="Imprime Mermaid del grafo sin ejecutar")
    parser.add_argument("--thread-id", default=None, help="ID de conversación (UUID)")
    args = parser.parse_args()

    graph = cargar_grafo(args.nombre_agente)
    thread_id = args.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}

    if args.diagrama:
        try:
            print(graph.get_graph().draw_mermaid())
        except Exception:
            print(graph.get_graph().to_dot())
        return

    estado_inicial = {
        "messages": [("user", args.mensaje)],
        "mensaje": args.mensaje,
        "ruta": "",
        "motivo": "",
        "respuesta": "",
        "saltos": [],
    }
    resultado = graph.invoke(estado_inicial, config=config)

    print("Ruta:", resultado.get("ruta"))
    print("Motivo:", resultado.get("motivo"))
    print("Respuesta:", resultado.get("respuesta"))

    if args.saltos:
        print("Saltos:")
        for s in resultado.get("saltos", []):
            print("  -", s)


if __name__ == "__main__":
    main()
