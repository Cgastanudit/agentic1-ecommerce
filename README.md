# agente-viajes-a2a

Proyecto del Curso 2. Contiene:

- **`src/router/`** · agente LangGraph que enruta mensajes de un chat de ecommerce a `preventa`, `postventa` o `generica`.
- **`api/app.py`** · API FastAPI que expone el router por HTTP (`/health`, `/chat`, `/telegram`).
- **`src/agente_viajes/`** · agente de viajes expuesto por A2A nativo (servidor de LangGraph). Ya está hecho.
- **`src/swarm/`** · swarm vuelos + hoteles (hecho); pendiente: agregar agente de actividades.
- **`scripts/`** y **`tests/`** · scripts sueltos y pruebas pytest.
- **`bruno/`** · colección para probar la API.

## Reglas de arquitectura (AGENTS.md)

1. Los agentes van en `src/{nombre_agente}/` con `graph.py`, `prompts.py` y `tools.py`; cada nodo con su propio prompt en `prompts.py`, nada de reglas dentro de `graph.py`.
2. Se ejecutan desde la raíz: `python main.py {nombre_agente} "mensaje"`.
   - Flag `--saltos`: imprime los nodos por los que pasó el grafo.
   - Flag `--diagrama`: imprime el Mermaid del grafo sin ejecutarlo.
3. La API va en `api/app.py` (FastAPI) y se levanta con: `uvicorn api.app:app --reload --port 8000`.
4. Los scripts sueltos van en `scripts/` y las pruebas en `tests/` (pytest).
5. Para Heroku: un `Procfile` con `web: uvicorn api.app:app --host 0.0.0.0 --port $PORT`, un archivo `.python-version` con `3.12`, y `requirements.txt` siempre actualizado.
6. `.gitignore` con `.env`, `.venv`, `__pycache__` y `.langgraph_api`.
7. Nunca valores reales en el código: las claves van solo en `.env` (ignorado) y el ejemplo está en `.env.example`.

---

## Entorno

Python 3.12 (ver `.python-version`).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1   # si da error de permisos: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
cp .env.example .env          # pega tu GOOGLE_API_KEY (y el resto si aplica)
```

En Linux/macOS cambia `.venv\Scripts\Activate.ps1` por `source .venv/bin/activate`.

---

## 1. Correr el router en local (CLI)

Desde la raíz del proyecto:

```powershell
.venv\Scripts\python.exe main.py router "¿tienen la polera azul en talla M?" --saltos --thread-id router_test
.venv\Scripts\python.exe main.py router "mi pedido 4521 llegó roto" --saltos --thread-id router_test
.venv\Scripts\python.exe main.py router "hola" --saltos --thread-id router_test
```

Flags disponibles:
- `--saltos`: imprime los nodos visitados y el motivo del router.
- `--diagrama`: imprime el Mermaid del grafo sin ejecutarlo.
- `--thread-id`: ID de conversación (UUID). Si no se pasa, se genera uno aleatorio.

---

## 2. Levantar la API (FastAPI)

Desde la raíz:

```powershell
uvicorn api.app:app --reload --port 8000
```

La API queda en `http://localhost:8000`.

Endpoints:

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | `{"ok": true, "modelo": "..."}` |
| `POST` | `/chat` | Body `{"user_id": "...", "texto": "..."}` → `{"ruta", "motivo", "respuesta"}` |
| `POST` | `/telegram` | Webhook placeholder → `{"ok": true}` (oculto de Swagger) |

Documentación interactiva (Swagger/OpenAPI con "Try it out"): `http://localhost:8000/docs`

Ejemplo con `curl`:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","texto":"¿tienen la polera azul en talla M?"}' | python3 -m json.tool
```

Respuesta esperada:

```json
{
  "ruta": "preventa",
  "motivo": "El usuario pregunta por la disponibilidad de un producto ...",
  "respuesta": "Soy el agente de preventa. Recibí: ¿tienen la polera azul en talla M?. Pronto podré ayudarte con productos y compras."
}
```

Bruno: abre `bruno/`, define la variable de entorno `base_url` (`http://localhost:8000` local o tu URL de Heroku) y ejecuta `health`, `chat-preventa`, `chat-postventa` y `chat-generica`.

---

## 3. Correr las pruebas

Pruebas del router (tabla + resumen):

```powershell
.venv\Scripts\python.exe scripts/test_router.py
```

Pruebas con pytest (exige al menos 13 de 15 aciertos):

```powershell
.venv\Scripts\python.exe -m pytest tests/test_router.py -v
```

---

## 4. Desplegar en Heroku

1. Crea la app en Heroku y configura las variables de entorno:
   ```bash
   heroku config:set GOOGLE_API_KEY=TU_CLAVE
   heroku config:set MODELO=gemini-3.5-flash-lite
   heroku config:set TELEGRAM_SECRET=cambiame
   heroku config:set PUBLIC_URL=https://TU_APP.herokuapp.com
   ```
2. El `Procfile` ya está listo:
   ```
   web: uvicorn api.app:app --host 0.0.0.0 --port $PORT
   ```
3. El `.python-version` declara `3.12`.
4. Sube el código:
   ```bash
   git push heroku main
   ```
5. Verifica:
   ```bash
   curl https://TU_APP.herokuapp.com/health
   ```

---

## 5. Conectar Telegram (pendiente — parte 5)

El endpoint `POST /telegram` ya existe como placeholder (`{"ok": true}`). Cuando se implemente la parte 5:

1. Crea el bot con **BotFather** y obtén el `TELEGRAM_TOKEN`.
2. Configura el webhook apuntando a `https://TU_PUBLIC_URL/telegram`.
3. Telegram envía un `X-Telegram-Bot-Api-Secret-Token` en cada request; compáralo con `TELEGRAM_SECRET`.
4. Las variables van en `.env` (nunca en el código):
   - `TELEGRAM_TOKEN` — vacío hasta este paso.
   - `TELEGRAM_SECRET` — el secreto que verifica cada webhook.
   - `PUBLIC_URL` — la URL https pública (tu app de Heroku).

---

## Estructura del repositorio

```
agente-viajes-a2a/
├── AGENTS.md
├── plan.json
├── langgraph.json
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── .python-version
├── Procfile
├── main.py
├── README.md
├── api/
│   └── app.py
├── bruno/
│   └── router/
├── scripts/
│   └── test_router.py
├── src/
│   ├── router/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── prompts.py
│   │   └── tools.py
│   ├── agente_viajes/   (A2A nativo, ya hecho)
│   └── swarm/           (vuelos + hoteles, ya hecho)
└── tests/
    ├── casos_router.json
    ├── test_router.py
    └── test_placeholder.py
```

---

## Subir a GitHub (repositorio vacío)

```powershell
git init
git add .
git commit -m "router + api + telegram"
# Luego pega exactamente los comandos que GitHub muestra para "push an existing repository",
# por ejemplo:
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```
