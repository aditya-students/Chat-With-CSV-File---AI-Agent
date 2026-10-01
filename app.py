"""
app.py  –  AI Agent logic
=========================
Contains:
  - Global dataframe & agent state with thread-safe Lock
  - LangChain tools (get_data_info, filter_data, analyze_data)
  - build_agent()  – initialises the LLM + LangGraph agent
  - run_query()    – invokes the agent and returns the answer string
"""

import os
import threading
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

# Fail silently if no .env file exists (reads system environment variables in production)
load_dotenv()

# Thread lock for global state access under multithreaded Gunicorn
_state_lock = threading.Lock()

# ── Global state ──────────────────────────────────────────────────────────────
_df:            pd.DataFrame | None = None
_agent                               = None
_csv_filename:  str | None           = None
_chat_history:  list                 = []


def get_df() -> pd.DataFrame | None:
    """Return the currently loaded dataframe."""
    with _state_lock:
        return _df


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def get_data_info() -> str:
    """Get columns, data types, shape, and first 5 rows of the uploaded CSV file."""
    df = get_df()
    if df is None:
        return "No CSV loaded. Please upload a CSV file first."
    return f"""
Shape: {df.shape}
Columns & Types:
{df.dtypes.to_string()}
First 5 rows:
{df.head().to_string()}
"""


@tool
def filter_data(condition: str) -> str:
    """
    Filter rows using a pandas query condition.
    Example: "age > 30 and loan_status == 'Default'"
    """
    df = get_df()
    if df is None:
        return "No CSV loaded."
    try:
        try:
            result = df.query(condition)
        except Exception:
            result = df.query(condition, engine="python")
        return f"Found {len(result)} rows:\n{result.head(20).to_string()}"
    except Exception as e:
        return f"Error: {e}"


@tool
def analyze_data(expression: str) -> str:
    """
    Run a pandas expression on the dataframe (referred to as 'df').
    Examples:
        df['loan_amnt'].mean()
        df.groupby('loan_status')['loan_amnt'].mean()
        df['person_home_ownership'].value_counts()
        df.describe()
    """
    df = get_df()
    if df is None:
        return "No CSV loaded."

    SAFE_BUILTINS = {
        "len": len, "round": round, "sum": sum, "min": min, "max": max,
        "abs": abs, "sorted": sorted, "list": list, "dict": dict,
        "str": str, "int": int, "float": float, "range": range,
    }

    forbidden = ["__", "import", "open(", "exec(", "eval(", "os.", "sys.",
                 "read_", "to_", "subprocess"]
    for item in forbidden:
        if item in expression:
            return f"Error: Access denied. Expression contains restricted element '{item}'."

    try:
        result = eval(expression, {"__builtins__": SAFE_BUILTINS}, {"df": df, "pd": pd})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# ── Agent builder ─────────────────────────────────────────────────────────────

def build_agent(df: pd.DataFrame) -> None:
    """
    Load a dataframe into global state and (re)initialise the LangGraph agent.
    Call this every time a new CSV is uploaded.
    """
    global _df, _agent

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Please set it in your environment or .env file.")

    all_tools = [get_data_info, filter_data, analyze_data]

    llm = ChatGroq(model="openai/gpt-oss-20b", api_key=api_key)

    system_prompt = """You are an expert data analyst assistant. You help users explore and analyze CSV data interactively.

Use the available tools to answer questions:
- get_data_info   -> see columns, types and sample rows
- filter_data     -> filter rows by a pandas query condition
- analyze_data    -> run pandas expressions for statistics and aggregations

Guidelines:
- Always use get_data_info first if you are unsure about column names.
- Give clear, concise answers with insights.
- Format numbers nicely (e.g., round to 2 decimal places).
- When showing data, summarize rather than dumping all rows.
- Provide actionable insights when relevant.
- IMPORTANT: Never output raw HTML tags like <ul>, <li>, <table>, <tr>, <td>, etc. Always use standard Markdown formatting (e.g. `- item` or `1. item` for lists, markdown tables `| col | col |` for tabular data).
"""

    memory = MemorySaver()
    agent_instance = create_agent(
        model=llm,
        tools=all_tools,
        checkpointer=memory,
        system_prompt=system_prompt,
    )

    with _state_lock:
        _df = df
        _agent = agent_instance


# ── Query runner ──────────────────────────────────────────────────────────────

def run_query(user_message: str) -> str:
    """
    Invoke the agent with a user message and return the assistant's answer.
    Raises RuntimeError if no agent is loaded.
    """
    with _state_lock:
        agent_instance = _agent

    if agent_instance is None:
        raise RuntimeError("No CSV loaded. Please upload a CSV file first.")

    result = agent_instance.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config={"configurable": {"thread_id": "frontend-session"}},
    )
    return result["messages"][-1].content


# ── Session helpers ───────────────────────────────────────────────────────────

def get_session_state() -> dict:
    """Return a snapshot of the current session state."""
    with _state_lock:
        return {
            "loaded":    _df is not None,
            "filename":  _csv_filename,
            "shape":     list(_df.shape) if _df is not None else None,
            "columns":   list(_df.columns) if _df is not None else None,
        }


def append_history(role: str, content: str) -> None:
    with _state_lock:
        _chat_history.append({"role": role, "content": content})


def get_history() -> list:
    with _state_lock:
        return list(_chat_history)


def reset_session() -> None:
    """Clear all global state (call on /api/reset)."""
    global _df, _agent, _csv_filename, _chat_history
    with _state_lock:
        _df           = None
        _agent        = None
        _csv_filename = None
        _chat_history = []


def set_filename(name: str) -> None:
    global _csv_filename
    with _state_lock:
        _csv_filename = name
