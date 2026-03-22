import io
import json # <--- NEW IMPORT
from contextlib import redirect_stdout
from typing import Annotated
from typing_extensions import TypedDict

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver 

# ==========================================
# 1. Define the Tool
# ==========================================
@tool
def python_repl_tool(code: str) -> str:
    """
    Executes Python code and returns the standard output.
    Use this to perform math calculations with sympy, numpy, or scipy.
    Always use `print()` to output your final result so you can read it.
    """
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            exec(code, {"__builtins__": __builtins__}, {})
        result = output.getvalue()
        return result if result.strip() else "Code executed successfully. No output."
    except Exception as e:
        return f"Failed to execute. Error: {e}"

tools = [python_repl_tool]

# ==========================================
# 2. Initialize Model & Bind Tools
# ==========================================
llm = ChatOllama(model="qwen2.5", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# ==========================================
# 3. Define the Graph State & Nodes
# ==========================================
class State(TypedDict):
    messages: Annotated[list, add_messages]


system_prompt = SystemMessage(
    content="""You are an expert mathematical AI assistant. 
    You are FORBIDDEN from doing math in your head. 
    You MUST use the `python_repl_tool` for EVERY calculation, no matter how simple (even 4+4).
    
    If you answer a math question without calling the tool, you have failed your primary directive.
    Always print() the final result in your python code.
    
     CRITICAL INSTRUCTIONS:
    1. DO NOT write Python code in Markdown blocks (```python).
    2. DO NOT shown the Python Code until user asks for it.
    3. You must strictly invoke the tool using the provided function calling API. 
    4. NEVER guess, hallucinate, or simulate the output of the tool. Wait for the actual tool to return the result.

    After receiving the real tool output, explain the final answer clearly.

""")

def chatbot_node(state: State):
    """The LLM decides whether to answer or call a tool."""
    messages_to_process = [system_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages_to_process)
    
    # --- 🛡️ THE BULLETPROOF FALLBACK INTERCEPTOR ---
    # If Llama 3.1 outputs the tool call as raw text instead of using the API, 
    # we intercept it, parse the JSON, and manually format it for LangChain.
    if not response.tool_calls and "python_repl_tool" in response.content:
        try:
            # Find the boundaries of the JSON block
            start_idx = response.content.find('{')
            end_idx = response.content.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response.content[start_idx:end_idx+1]
                tool_data = json.loads(json_str)
                
                # Forcefully inject the tool call so LangGraph knows to run the Python node
                response.tool_calls = [{
                    "name": tool_data.get("name", "python_repl_tool"),
                    "args": tool_data.get("parameters", {}),
                    "id": "call_fallback_123"
                }]
                # Wipe the raw JSON from the message content so the user doesn't see it
                response.content = "" 
        except Exception:
            pass # If extraction fails, we just let it pass to the user

    return {"messages": [response]}

tool_node = ToolNode(tools=tools)

# ==========================================
# 4. Build and Compile the Graph
# ==========================================
graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

memory = MemorySaver()

math_agent = graph_builder.compile(checkpointer=memory)

# ==========================================
# 5. API Interface Function
# ==========================================
def get_agent_response(user_input: str, thread_id: str = "default_user") -> str:
    """Sends a message to the graph and returns the final text response."""
    
    # We pass the input. LangGraph's memory will automatically append it to the history.
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    
    # --- NEW: Configuration with Thread ID ---
    config = {"configurable": {"thread_id": thread_id}}
    
    final_text = ""
    
    # Pass the config to the stream
    for event in math_agent.stream(initial_state, config=config):
        for node_name, node_state in event.items():
            latest_message = node_state["messages"][-1]
            
            if node_name == "chatbot" and not latest_message.tool_calls:
                final_text = latest_message.content
                
    return final_text


# ==========================================
# 5. API Interface Function (STREAMING VERSION)
# ==========================================
def stream_agent_response(user_input: str, thread_id: str = "default_user"):
    """Streams the agent's internal state back to the UI in real-time."""
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    config = {"configurable": {"thread_id": thread_id}}
    
    # Stream the graph execution step-by-step
    for event in math_agent.stream(initial_state, config=config):
        for node_name, node_state in event.items():
            latest_message = node_state["messages"][-1]
            
            # If the chatbot node decides to call a tool, ping the frontend!
            if node_name == "chatbot" and latest_message.tool_calls:
                yield json.dumps({"type": "tool_start", "message": "Calling Python tool..."}) + "\n"

    # Once the loop is totally finished, grab the very last message and send it
    final_state = math_agent.get_state(config)
    final_text = final_state.values["messages"][-1].content
    yield json.dumps({"type": "final_answer", "content": final_text}) + "\n"