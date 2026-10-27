# AGENTS.md

## Reglas de arquitectura

1. Los agentes van en `src/{nombre_agente}/` con `graph.py`, `prompts.py` y `tools.py`; cada nodo con su propio prompt en `prompts.py`, nada de reglas dentro de `graph.py`.
2. Se ejecutan desde la raíz: `python main.py {nombre_agente} "mensaje"`.
   - Flag `--saltos`: imprime los nodos por los que pasó el grafo.
   - Flag `--diagrama`: imprime el Mermaid del grafo sin ejecutarlo.
3. La API va en `api/app.py` (FastAPI) y se levanta con: `uvicorn api.app:app --reload --port 8000`.
4. Los scripts sueltos van en `scripts/` y las pruebas en `tests/` (pytest).
5. Para Heroku: un `Procfile` con `web: uvicorn api.app:app --host 0.0.0.0 --port $PORT`, un archivo `.python-version` con `3.12`, y `requirements.txt` siempre actualizado.
6. `.gitignore` con `.env`, `.venv`, `__pycache__` y `.langgraph_api`.
7. Nunca valores reales en el código: las claves van solo en `.env` (ignorado) y el ejemplo está en `.env.example`.
