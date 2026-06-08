# sdk_agent.py - Phase 1 Week 2 Day 7
# Khopfa Towing agent rebuilt on Anthropic SDK
# Same tools and logic as agentv3.py — different API, better reliability
# Key differences from Groq version:
#   - stop_reason is "end_turn" not "stop"
#   - stop_reason is "tool_use" not "tool_calls"
#   - tool inputs come as dict — no json.loads() needed
#   - tool results go back as "user" role not "tool" role
#   - response content is a list of blocks — loop through to find tool_use

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Anthropic client — reliable tool calling, clean JSON every time
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── TOOLS ──────────────────────────────────────────────────────────────────
# Same tools as agentv3.py — tools are independent of the model
# Swapping Groq for Anthropic changes nothing about the tools themselves

from tavily import TavilyClient
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def web_search(query):
    # Real Tavily search — returns clean web results for the model
    try:
        results = tavily.search(query=query, max_results=3)
        output = []
        for r in results.get("results", []):
            output.append(f"Source: {r['url']}\n{r['content']}")
        return "\n\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

def calculate_tow_price(distance_km, after_hours=False):
    # Minimum distance — under 10km returns base fee R350
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
# Anthropic format is slightly different from Groq
# after_hours is back to boolean — Claude handles it correctly
# No more string "true"/"false" workaround needed

tools = [
    {
        "name": "web_search",
        "description": "Search the web for current information. Use this when you need facts, prices or news you do not already know.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate_tow_price",
        "description": "Calculate exact towing price for Khopfa Towing. ALWAYS use this before quoting any price. Never guess. Pass after_hours as true if customer mentions night, evening, after 7pm, Sunday or weekend.",
        "input_schema": {
            "type": "object",
            "properties": {
                "distance_km": {
                    "type": "number",
                    "description": "Distance in kilometres"
                },
                "after_hours": {
                    "type": "boolean",
                    "description": "True if after 7pm or weekend, False otherwise"
                }
            },
            "required": ["distance_km"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Use when asked to save or export information.",
        "input_schema": {
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
    },
    {
        "name": "read_file",
        "description": "Read content from a file. Use when asked to retrieve saved information.",
        "input_schema": {
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
]

import datetime

def log_tool_call(tool_name, tool_input, result):
    # PostToolUse hook — logs every tool call to a file
    # Why: audit trail for production, debug tool for development
    # When: after every tool execution, before result goes back to model
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] TOOL: {tool_name} | INPUT: {tool_input} | RESULT: {result}\n"
    with open("tool_log.txt", "a") as f:
        f.write(log_entry)

# ── EXECUTE TOOL ───────────────────────────────────────────────────────────
# Same bridge as before — model says which tool, we run it
# No boolean conversion needed — Claude sends proper Python booleans
# No json.loads() needed — Anthropic inputs already come as dictionaries

def execute_tool(tool_name, tool_input):
    if tool_name == "web_search":
        result = web_search(**tool_input)
    elif tool_name == "calculate_tow_price":
        result = calculate_tow_price(**tool_input)
    elif tool_name == "write_file":
        result = write_file(**tool_input)
    elif tool_name == "read_file":
        result = read_file(**tool_input)
    else:
        result = f"Unknown tool: {tool_name}"
    
    # PostToolUse hook — log every tool call
    log_tool_call(tool_name, tool_input, result)
    return result
    
# ── AGENT LOOP ─────────────────────────────────────────────────────────────
# Same 7-step loop — different Anthropic syntax
# Key differences from Groq:
#   - stop_reason is "end_turn" not "stop"
#   - stop_reason is "tool_use" not "tool_calls"  
#   - loop through response.content blocks to find tool_use
#   - tool inputs already a dict — no json.loads() needed
#   - tool results go back as "user" role with content list

def run_agent(user_message, messages=None):
    # Input validation — reject empty messages
    if not user_message or not user_message.strip():
        return "Please describe what you need help with."

    # Build or continue conversation
    if messages is None:
        messages = []

    # Append new user message
    messages.append({"role": "user", "content": user_message})

    while True:
        # Step 1 - send messages and tools to model
        # Gate 1 - catch API failures
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system="You are a towing assistant for Khopfa Towing in Limpopo. ALWAYS call calculate_tow_price before quoting any price. Pass after_hours as true if customer mentions night, evening, after 7pm, Sunday or weekend. You can search the web and read and write files when asked. Politely refuse anything unrelated to towing.",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"

        # Step 2 - check stop reason
        # Anthropic uses "end_turn" not "stop"
        # Anthropic uses "tool_use" not "tool_calls"
        stop_reason = response.stop_reason

        # Step 3 - model is done, return final answer
        if stop_reason == "end_turn":
            # Extract text from content blocks
            answer = ""
            for block in response.content:
                if block.type == "text":
                    answer += block.text
            # Append assistant response to history for memory
            messages.append({"role": "assistant", "content": response.content})
            return answer

        # Step 4 - model wants to use tools
        if stop_reason == "tool_use":
            # Append assistant message to history
            messages.append({"role": "assistant", "content": response.content})

            # Step 5 - collect ALL tool results before sending any back
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input  # already a dict — no json.loads needed

                    # Gate 2 - catch tool failures
                    try:
                        result = execute_tool(tool_name, tool_input)
                    except FileNotFoundError:
                        result = f"File not found: {tool_input.get('path', 'unknown path')}"
                    except PermissionError:
                        result = f"Permission denied: {tool_input.get('path', 'unknown path')}"
                    except Exception as e:
                        result = f"Tool error: {str(e)}"

                    # Collect result with tool_use_id — links back to exact request
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            # Step 6 - send ALL results back as ONE user message
            # Anthropic tool results go back as "user" role — different from Groq
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Step 7 - loop back to Step 1


# ── ENTRY POINT ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(run_agent("How much to tow my car 25km in Polokwane?"))