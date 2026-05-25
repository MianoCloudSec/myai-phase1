# agent_v2.py - Phase 1 Day 3
# Adds error handling and parallel tool call support to agent.py

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


# ── TOOLS ──────────────────────────────────────────────────────────────────

def web_search(query):
    # Fake search - in production this calls Tavily API
    return f"Search results for: {query} - Limpopo towing market is growing 15% annually"

def calculate_tow_price(distance_km, after_hours=False):
    # Calculates towing price for Khopfa Towing
    base = 350
    per_km = 12
    price = base + (distance_km - 10) * per_km
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
            "description": "Calculate exact towing price for Khopfa Towing. ALWAYS use this before quoting any price. Never guess.",
            "parameters": {
                "type": "object",
                "properties": {
                    "distance_km": {
                        "type": "number",
                        "description": "Distance in kilometres"
                    }
                },
                "required": ["distance_km"]
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
# **tool_input unpacks dict into individual arguments

def execute_tool(tool_name, tool_input):
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

def run_agent(user_message):
    messages = [
        {
            "role": "system",
            "content": "You are a towing assistant for Khopfa Towing in Limpopo. ALWAYS call calculate_tow_price before quoting any price. Only answer towing related questions. Politely refuse anything unrelated to towing."
        },
        {"role": "user", "content": user_message}
    ]

    while True:
        # Step 1 - send messages and tools to model
        # Gate 1 - catch API failures
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"

        # Step 2 - check stop reason
        stop_reason = response.choices[0].finish_reason

        # Step 3 - done, return answer
        if stop_reason == "stop":
            return response.choices[0].message.content

        # Step 4 - model wants tools
        if stop_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls

            # Add assistant message to history
            messages.append(response.choices[0].message)

            # Step 5 - collect ALL tool results before sending any back
            # This handles parallel tool calls correctly
            tool_results = []

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                # Gate 2 - catch tool failures
                try:
                    result = execute_tool(tool_name, tool_input)
                except FileNotFoundError:
                    result = f"File not found: {tool_input.get('path', 'unknown path')}"
                except PermissionError:
                    result = f"Permission denied: {tool_input.get('path', 'unknown path')}"
                except Exception as e:
                    result = f"Tool error: {str(e)}"

                # Collect result - don't send yet
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

            # Step 6 - send ALL results together in one batch
            for tool_result in tool_results:
                messages.append(tool_result)

            # Step 7 - loop back to Step 1


# ── ENTRY POINT ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(run_agent("Calculate the price for a 20km tow and also a 50km tow"))