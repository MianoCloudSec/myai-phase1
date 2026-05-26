# agent_v4_tavily.py - Phase 1 Day 4 Bonus
# Wires real Tavily web search into the agent
# Everything same as agentv3.py except web_search now calls real Tavily API
# Brain: Groq llama-3.3-70b-versatile
# Search: Tavily real web search
# Next step: swap Groq for Anthropic in Week 2 — tools stay the same

import os
import json
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Two clients — one for the brain, one for search
client = Groq(api_key=os.environ["GROQ_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


# ── TOOLS ──────────────────────────────────────────────────────────────────

# UPGRADED — web_search now calls real Tavily API
# Why: fake search returned same hardcoded string for every query
# What: Tavily searches the web and returns clean results for the model
# How: TavilyClient.search() returns a list of results with url, title, content
def web_search(query):
    try:
        results = tavily.search(query=query, max_results=3)
        output = []
        for r in results.get("results", []):
            output.append(f"Source: {r['url']}\n{r['content']}")
        return "\n\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

# FIX 2 & 3 — minimum distance and after hours surcharge
def calculate_tow_price(distance_km, after_hours=False):
    # Minimum distance — anything under 10km returns base fee R350
    if distance_km < 10:
        price = 350
    else:
        base = 350
        per_km = 12
        price = base + (distance_km - 10) * per_km
    # After hours — 30% surcharge for night and weekend
    if after_hours:
        price = price * 1.3
    return f"R{price:.0f}"

def write_file(path, content):
    # Writes content to a file on disk
    with open(path, 'w') as f:
        f.write(content)
    return f"File written to {path}"

def read_file(path):
    # Reads content from a file on disk
    with open(path, 'r') as f:
        return f.read()


# ── TOOL SCHEMAS ───────────────────────────────────────────────────────────
# Same schemas as agentv3.py
# Model doesn't know web_search changed internally — only the function changed
# Schema stays the same because the inputs and outputs are the same

tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information. Use this when you need facts, prices or news you do not already know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query. Be specific."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tow_price",
            "description": "Calculate exact towing price for Khopfa Towing. ALWAYS use this before quoting any price. Never guess. Pass after_hours as 'true' if customer mentions night, evening, after 7pm, Sunday or weekend.",
            "parameters": {
                "type": "object",
                "properties": {
                    "distance_km": {
                        "type": "number",
                        "description": "Distance in kilometres"
                    },
                    "after_hours": {
                        "type": "string",
                        "description": "Pass 'true' if after 7pm or weekend, 'false' otherwise"
                    }
                },
                "required": ["distance_km", "after_hours"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Use when asked to save or export information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write to"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content from a file. Use when asked to retrieve saved information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read from"
                    }
                },
                "required": ["path"]
            }
        }
    }
]


# ── EXECUTE TOOL ───────────────────────────────────────────────────────────
# Bridge between model and actual functions
# FIX 4 — boolean conversion for after_hours
# Groq sends after_hours as string — convert to Python boolean before use

def execute_tool(tool_name, tool_input):
    if "after_hours" in tool_input:
        val = tool_input["after_hours"]
        if isinstance(val, str):
            tool_input["after_hours"] = val.strip().lower() == "true"
        else:
            tool_input["after_hours"] = bool(val)

    if tool_name == "web_search":
        return web_search(**tool_input)
    elif tool_name == "calculate_tow_price":
        return calculate_tow_price(**tool_input)
    elif tool_name == "write_file":
        return write_file(**tool_input)
    elif tool_name == "read_file":
        return read_file(**tool_input)
    else:
        return f"Unknown tool: {tool_name}"


# ── AGENT LOOP ─────────────────────────────────────────────────────────────
# Same loop as agentv3.py
# Only difference — web_search now returns real Tavily results

def run_agent(user_message, messages=None):
    # FIX 1 — input validation
    if not user_message or not user_message.strip():
        return "Please describe what you need help with."

    if messages is None:
        messages = [
            {
                "role": "system",
                "content": "You are a towing assistant for Khopfa Towing in Limpopo. ALWAYS call calculate_tow_price before quoting any price. Pass after_hours as 'true' if customer mentions night, evening, after 7pm, Sunday or weekend. You can search the web and read and write files when asked. Politely refuse anything completely unrelated to towing."
            }
        ]

    messages.append({"role": "user", "content": user_message})

    while True:
        # Gate 1 — catch API failures
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"

        stop_reason = response.choices[0].finish_reason

        if stop_reason == "stop":
            messages.append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })
            return response.choices[0].message.content

        if stop_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls
            messages.append(response.choices[0].message)

            tool_results = []

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                # Gate 2 — catch tool failures
                try:
                    result = execute_tool(tool_name, tool_input)
                except FileNotFoundError:
                    result = f"File not found: {tool_input.get('path', 'unknown path')}"
                except PermissionError:
                    result = f"Permission denied: {tool_input.get('path', 'unknown path')}"
                except Exception as e:
                    result = f"Tool error: {str(e)}"

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

            for tool_result in tool_results:
                messages.append(tool_result)


# ── ENTRY POINT ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    # Test 1 — direct Tavily search, bypasses the agent
    print("=== DIRECT TAVILY SEARCH ===")
    print(web_search("current towing prices in Limpopo South Africa"))
    print()
    
    # Test 2 — agent for towing quote, uses calculate_tow_price
    print("=== AGENT TOWING QUOTE ===")
    print(run_agent("How much to tow my car 25km in Polokwane?"))