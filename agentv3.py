# agent_v3.py - Phase 1 Day 4
# Fixed version of agent_v2.py based on 10 test case results
# Fixes applied:
#   1. Input validation — reject empty messages before hitting the model
#   2. Minimum distance — anything under 10km returns base fee R350
#   3. After hours detection — detect time words and apply 30% surcharge
#   4. Boolean fix — convert string "true"/"false" to Python boolean
#   5. System prompt loosened — allow file operations not just towing
#   6. Conversation memory — keep messages alive across multiple calls

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Create connection to Groq - all API calls go through this client
client = Groq(api_key=os.environ["GROQ_API_KEY"])


# ── TOOLS ──────────────────────────────────────────────────────────────────
# Real Python functions - do actual work
# Model never runs these directly - we run them on its behalf

def web_search(query):
    # Fake search - in production this calls Tavily API
    return f"Search results for: {query} - Limpopo towing market is growing 15% annually"

# FIX 2 & 3 — calculate_tow_price now handles:
# - Minimum distance: anything under 10km returns base fee R350
# - After hours: accepts boolean parameter for 30% surcharge
def calculate_tow_price(distance_km, after_hours=False):
    # FIX 3 — minimum distance validation
    # Why: 0km or short distance returns wrong price due to formula
    # What: anything under 10km charges base fee only — no negative discount
    if distance_km < 10:
        price = 350     # base callout fee — minimum charge
    else:
        base = 350
        per_km = 12
        price = base + (distance_km - 10) * per_km

    # FIX 2 — after hours surcharge
    # Why: 11pm Sunday should cost 30% more than normal hours
    # What: multiply price by 1.3 if after_hours is True
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
# The menu the model reads - it never sees the actual functions
# description field is a prompt not a label - write it carefully

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
# **tool_input unpacks dictionary into individual arguments

def execute_tool(tool_name, tool_input):
    # FIX 4 — Boolean fix for after_hours
    # Why: Groq sends after_hours as string "true"/"false" not Python boolean
    # What: convert string to boolean before passing to calculate_tow_price
    # How: check if value is string, convert "true" to True, anything else False
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
# The 7-step loop that powers the agent
# Runs until model says it is done (stop_reason == "stop")

# FIX 6 — Conversation memory
# Why: Test 5 and 10 showed agent forgets context across calls
# What: accept existing messages list as optional parameter
# How: if messages passed in use them, if not build fresh with system prompt

def run_agent(user_message, messages=None):
    # FIX 1 — Input validation
    # Why: empty input caused hallucinated prices in Day 3 testing
    # What: reject empty or whitespace-only messages before hitting the model
    if not user_message or not user_message.strip():
        return "Please describe what you need help with."

    # FIX 6 — build or continue conversation
    if messages is None:
        messages = [
            {
                "role": "system",
                # FIX 5 — System prompt loosened
                # Why: Test 7 showed system prompt blocked legitimate file operations
                # What: allow file operations alongside towing assistance
                "content": "You are a towing assistant for Khopfa Towing in Limpopo. ALWAYS call calculate_tow_price before quoting any price. Pass after_hours as 'true' if customer mentions night, evening, after 7pm, Sunday or weekend. You can also read and write files when asked. Politely refuse anything completely unrelated to towing or file operations."
            }
        ]

    # Append new user message to conversation
    messages.append({"role": "user", "content": user_message})

    while True:
        # Step 1 - send messages and tools list to model
        # Gate 1 - catches API failures before they crash the agent
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"

        # Step 2 - check why model stopped
        stop_reason = response.choices[0].finish_reason

        # Step 3 - model is done, return final answer
        if stop_reason == "stop":
            messages.append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })
            return response.choices[0].message.content

        # Step 4 - model wants to use a tool
        if stop_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls

            # Append assistant message to history
            messages.append(response.choices[0].message)

            # Step 5 - collect ALL tool results before sending any back
            tool_results = []

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                # Gate 2 - catches tool failures without crashing the agent
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

            # Step 6 - send ALL results together in one batch
            for tool_result in tool_results:
                messages.append(tool_result)

            # Step 7 - loop back to Step 1


# ── ENTRY POINT ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    messages = []
    run_agent("Hi my name is Sipho", messages)
    run_agent("I need a tow from Polokwane CBD", messages)
    run_agent("The distance is 25km", messages)
    run_agent("My car is a white Toyota Hilux", messages)
    run_agent("My number is 072 555 0101", messages)
    print(run_agent("What is the total price and confirm my booking details?", messages))