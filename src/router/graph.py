from typing import Annotated, Literal
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from .prompts import SYSTEM_ROUTER, PROMPT_PREVENTA, PROMPT_POSTVENTA, PROMPT_GENERICA

load_dotenv()


class Decision(BaseModel):
    ruta: Literal["preventa", "postventa", "generica"] = Field(
        description="A qué agente va el mensaje."
    )
    motivo: str = Field(description="Una frase: por qué esa ruta.")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    mensaje: str
    ruta: str
    motivo: str
    respuesta: str
    saltos: list[str]


def _router_llm():
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("MODELO", "gemini-3.5-flash-lite"), temperature=0
    )
    return llm.with_structured_output(Decision)


def router_node(state: State):
    router_llm = _router_llm()
    decision = router_llm.invoke(
        [
            {"role": "system", "content": SYSTEM_ROUTER},
            {"role": "user", "content": state["mensaje"]},
        ]
    )
    saltos = list(state.get("saltos", []))
    saltos.append(f"router -> {decision.ruta} ({decision.motivo})")
    return {
        "ruta": decision.ruta,
        "motivo": decision.motivo,
        "saltos": saltos,
        "messages": [("user", state["mensaje"])],
    }


def ruta_condicional(state: State):
    return state["ruta"]


def preventa_node(state: State):
    respuesta = PROMPT_PREVENTA.format(mensaje=state["mensaje"])
    saltos = list(state.get("saltos", []))
    saltos.append("preventa")
    return {"respuesta": respuesta, "saltos": saltos}


def postventa_node(state: State):
    respuesta = PROMPT_POSTVENTA.format(mensaje=state["mensaje"])
    saltos = list(state.get("saltos", []))
    saltos.append("postventa")
    return {"respuesta": respuesta, "saltos": saltos}


def generica_node(state: State):
    respuesta = PROMPT_GENERICA
    saltos = list(state.get("saltos", []))
    saltos.append("generica")
    return {"respuesta": respuesta, "saltos": saltos}


builder = StateGraph(State)
builder.add_node("router", router_node)
builder.add_node("preventa", preventa_node)
builder.add_node("postventa", postventa_node)
builder.add_node("generica", generica_node)
builder.set_entry_point("router")
builder.add_conditional_edges("router", ruta_condicional)
builder.add_edge("preventa", END)
builder.add_edge("postventa", END)
builder.add_edge("generica", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
