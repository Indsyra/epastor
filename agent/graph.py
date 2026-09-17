from langgraph.graph import StateGraph, END
from agent.nodes import AgentState, make_retrieval_node, make_generation_node, make_book_extraction_node

def build_agent_graph(session):
    graph = StateGraph(AgentState)

    graph.add_node("retrieval", make_retrieval_node(session))
    graph.add_node("generation", make_generation_node())
    graph.add_node("book_extraction", make_book_extraction_node(session))

    graph.set_entry_point("retrieval")
    graph.add_edge("retrieval", "generation")
    graph.add_edge("generation", "book_extraction")
    graph.add_edge("book_extraction", END)

    return graph.compile()