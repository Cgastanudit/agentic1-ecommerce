"""Swarm · dos agentes que se PASAN EL CONTROL (handoff) en vez de tener un supervisor.

Patrón de langgraph-swarm: cada agente es un ReAct con sus herramientas + una herramienta de
"transferir a X". El agente activo atiende; cuando algo no es suyo, transfiere y el otro sigue
la misma conversación. El swarm recuerda quién quedó activo (active_agent) en el checkpointer.

  vuelos  ──transfer_to_hoteles──▶  hoteles
  hoteles ──transfer_to_vuelos───▶  vuelos
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langgraph_swarm import create_handoff_tool, create_swarm

from src.agente_viajes.herramientas import buscar_hoteles, buscar_vuelos
from src.swarm.prompts import SYSTEM_HOTELES, SYSTEM_VUELOS

load_dotenv()
modelo = ChatGoogleGenerativeAI(model=os.environ.get("MODELO", "gemini-3.5-flash-lite"))

# 1. Herramientas de transferencia: son tools normales; el modelo las llama cuando la pregunta no es suya.
a_hoteles = create_handoff_tool(agent_name="hoteles", description="Transfiere al agente de hoteles (alojamiento, noches, zonas).")
a_vuelos = create_handoff_tool(agent_name="vuelos", description="Transfiere al agente de vuelos (rutas, horarios, aerolíneas).")

# 2. Cada agente: un agente ReAct (create_agent) + sus herramientas + a quién puede transferir. El `name` es su identidad en el swarm.
vuelos = create_agent(modelo, tools=[buscar_vuelos, a_hoteles], system_prompt=SYSTEM_VUELOS, name="vuelos")
hoteles = create_agent(modelo, tools=[buscar_hoteles, a_vuelos], system_prompt=SYSTEM_HOTELES, name="hoteles")

# 3. El swarm: lista de agentes + quién parte. El checkpointer guarda el agente activo por thread_id.
swarm = create_swarm([vuelos, hoteles], default_active_agent="vuelos")
graph = swarm.compile(checkpointer=InMemorySaver())


def texto(msg) -> str:
    """El contenido de Gemini puede venir como lista de partes; esto lo aplana a texto."""
    c = msg.content
    return c if isinstance(c, str) else " ".join(p.get("text", "") for p in c if isinstance(p, dict))


if __name__ == "__main__":
    hilo = {"configurable": {"thread_id": "demo-1"}}
    for pregunta in ["Quiero un vuelo de Santiago a Lima el 2026-11-10",
                  "Y un hotel en Lima por 3 noches",
                  "¿Y si mejor vuelo a Bogotá ese mismo día?"]:
        r = graph.invoke({"messages": [{"role": "user", "content": pregunta}]}, hilo)
        print(f"\n> {pregunta}\n[{r.get('active_agent', 'vuelos')}] {texto(r['messages'][-1])}")
