from langchain.tools import tool
from rag.vectorstore import get_vectorstore

@tool
def search_policies(query: str) -> str:
    """Use this tool to search the enterprise vector database for company policies, guidelines, and HR documents."""
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    
    if not docs:
        return "No relevant documents found in the database."
    
    context = "\n\n".join([f"Source ({doc.metadata.get('page', 'unknown')}): {doc.page_content}" for doc in docs])
    return context

@tool
def calculate_metrics(expression: str) -> str:
    """Use this tool for exact mathematical calculations, budget projections, or numerical operations."""
    try:
        # Note: In a true production environment, use a safer math evaluator than eval()
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error calculating metrics: {str(e)}"
