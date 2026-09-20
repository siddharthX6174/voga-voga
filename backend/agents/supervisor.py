import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.tools import search_policies, calculate_metrics

load_dotenv()

# Initialize specialized LLMs
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash", 
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

tools = [search_policies, calculate_metrics]

from langgraph.prebuilt import create_react_agent
system_prompt = "You are voga-voga, an AI assistant. Whenever someone asks for your name, identity, or which model you are using, you must always answer 'I am voga-voga'."
agent_executor = create_react_agent(llm, tools=tools, prompt=system_prompt)

def run_multi_agent_workflow(user_query: str) -> str:
    """
    Executes the agent workflow. The LLM will automatically route to the 
    calculator tool for math or the search tool for policy queries.
    """
    try:
        response = agent_executor.invoke({"messages": [("user", user_query)]})
        content = response["messages"][-1].content
        if isinstance(content, list):
            text = "\n".join([part["text"] for part in content if isinstance(part, dict) and "text" in part])
            return text if text else str(content)
        return str(content)
    except Exception as e:
        return f"Agent encountered an error: {str(e)}"
