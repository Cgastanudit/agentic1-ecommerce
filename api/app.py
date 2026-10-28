import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.router.graph import graph

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ecommerce_router")


class ChatRequest(BaseModel):
    user_id: str = Field(
        ...,
        description="Identificador del usuario (se usa como thread_id de la conversación).",
        example="usuario_123",
    )
    texto: str = Field(
        ...,
        description="Mensaje del usuario a enrutar.",
        example="¿tienen la polera azul en talla M?",
    )


class ChatResponse(BaseModel):
    ruta: str = Field(
        ...,
        description="Ruta asignada por el router: preventa, postventa o generica.",
        example="preventa",
    )
    motivo: str = Field(
        ...,
        description="Una frase explicando por qué se eligió esa ruta.",
        example="El usuario pregunta por disponibilidad de producto y talla antes de comprar.",
    )
    respuesta: str = Field(
        ...,
        description="Respuesta del agente de destino (preventa, postventa o generica).",
        example="Soy el agente de preventa. Recibí: ¿tienen la polera azul en talla M?. Pronto podré ayudarte con productos y compras.",
    )


_grafo = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compila/carga el grafo UNA vez al arrancar la app."""
    global _grafo
    _grafo = graph
    yield


app = FastAPI(
    title="Ecommerce Router API",
    version="1.0.0",
    description=(
        "API para enrutar mensajes de un chat de ecommerce. "
        "El router analiza cada mensaje y lo deriva a uno de tres agentes: "
        "**preventa** (intención de compra, productos, precios, tallas, stock, "
        "promociones, formas de pago antes de comprar), "
        "**postventa** (quejas, reclamos, seguimiento de pedidos ya hechos, "
        "devoluciones, cambios, garantías, productos dañados) o "
        "**generica** (cualquier cosa no relacionada con el ecommerce o saludos sin pedido)."
    ),
    contact={"name": "Soporte Ecommerce"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["salud"],
    summary="Estado de la API",
    response_model=dict[str, Any],
)
def health() -> dict[str, Any]:
    """Devuelve si la API está viva y qué modelo usa el router."""
    return {"ok": True, "modelo": os.getenv("MODELO", "gemini-3.5-flash-lite")}


@app.post(
    "/chat",
    tags=["chat"],
    summary="Enrutar un mensaje de chat",
    response_model=ChatResponse,
    responses={
        200: {
            "description": "Mensaje enrutado correctamente.",
            "model": ChatResponse,
        },
        422: {"description": "Error de validación del cuerpo (falta el campo texto)."},
        502: {"description": "Error al consultar el modelo de lenguaje."},
    },
)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        estado_inicial = {
            "messages": [("user", req.texto)],
            "mensaje": req.texto,
            "ruta": "",
            "motivo": "",
            "respuesta": "",
            "saltos": [],
        }
        config = {"configurable": {"thread_id": req.user_id}, "recursion_limit": 25}
        resultado = _grafo.invoke(estado_inicial, config=config)
        return ChatResponse(
            ruta=resultado.get("ruta", ""),
            motivo=resultado.get("motivo", ""),
            respuesta=resultado.get("respuesta", ""),
        )
    except Exception as exc:
        logger.exception("Error invocando el grafo router")
        raise HTTPException(
            status_code=502,
            detail="El servicio de enrutamiento no está disponible. Intenta nuevamente más tarde.",
        )


@app.post("/telegram", include_in_schema=False)
async def telegram(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    """Webhook de Telegram (sin librerías de bot, solo httpx).

    - Verifica la cabecera X-Telegram-Bot-Api-Secret-Token contra TELEGRAM_SECRET.
    - Extrae chat_id y texto del Update.
    - Invoca el grafo con thread_id = chat_id.
    - Responde al usuario via sendMessage de Telegram.
    - Siempre devuelve 200 a Telegram (rápido).
    """
    # 1. Verificar secreto
    expected_secret = os.getenv("TELEGRAM_SECRET")
    if expected_secret is None or x_telegram_bot_api_secret_token != expected_secret:
        logger.warning("Webhook de Telegram con secreto inválido o faltante")
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    # 2. Parsear el Update
    try:
        update = await request.json()
    except Exception:
        logger.warning("Update de Telegram no es JSON válido")
        return JSONResponse(status_code=200, content={"ok": True})

    message = update.get("message", {})
    if not message:
        return JSONResponse(status_code=200, content={"ok": True})

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    texto = message.get("text")

    # 3. Ignorar updates sin texto ni chat_id
    if not texto or chat_id is None:
        return JSONResponse(status_code=200, content={"ok": True})

    # 4. Si no hay token configurado, no se puede responder; igual 200
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.warning("TELEGRAM_TOKEN no configurado; no se responde al usuario")
        return JSONResponse(status_code=200, content={"ok": True})

    # 5. Invocar el grafo con thread_id = chat_id
    try:
        estado_inicial = {
            "messages": [("user", texto)],
            "mensaje": texto,
            "ruta": "",
            "motivo": "",
            "respuesta": "",
            "saltos": [],
        }
        config = {
            "configurable": {"thread_id": str(chat_id)},
            "recursion_limit": 25,
        }
        resultado = _grafo.invoke(estado_inicial, config=config)
        respuesta = resultado.get("respuesta", "Lo siento, no pude procesar tu mensaje.")
        logger.info(
            "Telegram chat_id=%s ruta=%s motivo=%s",
            chat_id,
            resultado.get("ruta"),
            resultado.get("motivo"),
        )
    except Exception as exc:
        logger.exception("Error invocando el grafo para Telegram")
        respuesta = "Lo siento, hubo un error procesando tu mensaje."

    # 6. Enviar respuesta al usuario via sendMessage
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": respuesta},
                timeout=15.0,
            )
    except Exception as exc:
        logger.exception("Error enviando mensaje a Telegram")

    # 7. Siempre 200 a Telegram (rápido)
    return JSONResponse(status_code=200, content={"ok": True})
