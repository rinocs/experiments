from typing import TypedDict, List, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langchain_openai import ChatOpenAI
from app.schemas import GradeResult
from app.rag import retrieve_chunks, generate_answer

class AgentState(TypedDict):
    question: str
    chunks: List[dict]
    answer: str
    sources: List[dict]
    confidence: float
    attempts: Annotated[int, add]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
graded_llm = llm.with_structured_output(GradeResult)

MAX_REWRITES = 2

def retrieve_node(state: AgentState):
    return {"chunks": retrieve_chunks(state["question"]), "attempts": 1}

def grade_node(state: AgentState):
    if state.get("attempts", 0) > MAX_REWRITES:
        return "answer"  # evita loop infinito
    if not state["chunks"]:
        return "rewrite"
    context = "

".join(c["text"] for c in state["chunks"])
    result = graded_llm.invoke(
        f"Valuta se il contesto risponde alla domanda.
Domanda: {state['question']}
Contesto: {context}"
    )
    return "answer" if result.relevance == "relevant" else "rewrite"

def rewrite_node(state: AgentState):
    new_q = llm.invoke(f"Riscrivi per retrieval documentale più efficace. Domanda: {state['question']}").content.strip()
    return {"question": new_q, "attempts": 1}

def answer_node(state: AgentState):
    answer, sources, confidence = generate_answer(state["question"], state["chunks"])
    return {"answer": answer, "sources": sources, "confidence": confidence}

graph = StateGraph(AgentState)
graph.add_node("retrieve", retrieve_node, retry=RetryPolicy(max_attempts=2))
graph.add_node("rewrite", rewrite_node)
graph.add_node("answer", answer_node, retry=RetryPolicy(max_attempts=2))
graph.add_edge(START, "retrieve")
graph.add_conditional_edges("retrieve", grade_node, {"answer": "answer", "rewrite": "rewrite"})
graph.add_edge("rewrite", "retrieve")
graph.add_edge("answer", END)
rag_graph = graph.compile()
