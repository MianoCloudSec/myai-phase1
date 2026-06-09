# sdk_agent.py - Phase 1 Week 2 Day 7-10
# Khopfa Towing agent rebuilt on Anthropic SDK
# Day 7 - Anthropic SDK, PostToolUse logging hook
# Day 8 - Sub-agents using ISOLATE primitive (research + WhatsApp formatter)
# Day 10 - File-based conversation memory

import os
import json
import datetime
from anthropic import Anthropic
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Two clients — brain and search
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


# ── TOOLS ──────────────────────────────────────────────────────────────────
# Tools are independent of the model — same tools work with any API

def web_search(query):
    # Real Tavily search — clean web results for the model
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
# Anthropic format — cleaner than Groq
# No "type": "function" wrapper needed
# "input_schema" instead of "parameters"
# after_hours is proper boolean — no string workaround needed

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
    },
    {
        "name": "format_whatsapp_booking",
        "description": "Format confirmed booking details into a professional WhatsApp confirmation message. Use this ONLY after collecting all booking details — name, phone, location, vehicle, distance and price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_details": {
                    "type": "string",
                    "description": "All confirmed booking details as a string — name, phone, location, vehicle, distance, price"
                }
            },
            "required": ["booking_details"]
        }
    },
    {
        "name": "research",
        "description": "Research a topic in depth and return a clean summary. Use this when the customer asks about regulations, industry information, or anything requiring multiple searches.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The research topic or question to investigate"
                }
            },
            "required": ["query"]
        }
    }
]


# ── POSTTOOLUSE LOGGING HOOK ────────────────────────────────────────────────
# Runs after every tool execution — audit trail for production
# Logs: timestamp, tool name, inputs, result
# Why: proof of what the agent calculated for any customer at any time

def log_tool_call(tool_name, tool_input, result):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] TOOL: {tool_name} | INPUT: {tool_input} | RESULT: {result}\n"
    with open("tool_log.txt", "a") as f:
        f.write(log_entry)


# ── FILE-BASED CONVERSATION MEMORY ─────────────────────────────────────────
# Why: agent loses all memory when script stops
# What: save messages to JSON file after every turn, load on start
# How: json.dump() saves list to file, json.load() reads it back
# Result: customer returns tomorrow and agent remembers them

def save_conversation(messages, filename="conversation.json"):
    # Save messages list to JSON file
    # "w" overwrites each time — we want the latest full conversation
    try:
        with open(filename, "w") as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        print(f"Could not save conversation: {str(e)}")

def load_conversation(filename="conversation.json"):
    # Load messages from JSON file
    # Returns empty list if file doesn't exist — fresh start for new customers
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # No saved conversation — return empty list
        return []
    except Exception as e:
        print(f"Could not load conversation: {str(e)}")
        return []


# ── SUB-AGENT 1 — RESEARCH (ISOLATE PRIMITIVE) ─────────────────────────────
# Runs in complete isolation from main conversation
# Why: complex research pollutes main context with raw search results
# What: takes query, does deep research, returns one clean summary
# Main agent calls this as a regular tool — doesn't know it's another agent

def research_agent(query):
    research_messages = []
    system = "You are a research assistant. Search for information on the given topic, analyse the results, and return a clear concise summary in 2-3 paragraphs. Only use the information you find — do not guess or make up facts."
    research_messages.append({
        "role": "user",
        "content": f"Research this topic and give me a detailed summary: {query}"
    })
    research_tools = [
        {
            "name": "web_search",
            "description": "Search the web for current information.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    ]

    while True:
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=system,
                messages=research_messages,
                tools=research_tools
            )
        except Exception as e:
            return f"Research failed: {str(e)}"

        stop_reason = response.stop_reason

        if stop_reason == "end_turn":
            summary = ""
            for block in response.content:
                if block.type == "text":
                    summary += block.text
            return summary

        if stop_reason == "tool_use":
            research_messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = web_search(block.input["query"])
                    log_tool_call(f"research_agent:{block.name}", block.input, result[:100])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            research_messages.append({"role": "user", "content": tool_results})


# ── SUB-AGENT 2 — WHATSAPP FORMATTER (ISOLATE PRIMITIVE) ───────────────────
# Formatter only sees booking details — not full conversation
# Why: full conversation is noise for a formatting task
# Benefits: faster, cheaper, more reliable, independently testable
# No tools needed — pure text transformation

def format_booking(booking_details):
    format_messages = [
        {
            "role": "user",
            "content": f"""Format these booking details into a professional WhatsApp confirmation message for Khopfa Towing.

Booking details:
{booking_details}

Requirements:
- Use WhatsApp formatting — *bold* for headers, emojis for visual appeal
- Start with a confirmation header
- List all booking details clearly
- End with a reassuring closing message
- Keep it under 150 words
- Professional but warm South African tone"""
        }
    ]

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system="You are a WhatsApp message formatter for Khopfa Towing. Format booking confirmations professionally. Use WhatsApp markdown — *bold*, emojis. Be warm and professional.",
            messages=format_messages
        )
        log_tool_call("format_booking", {"booking_details": booking_details[:50]}, "formatted message generated")
        return response.content[0].text
    except Exception as e:
        return f"Formatting failed: {str(e)}"


# ── EXECUTE TOOL ───────────────────────────────────────────────────────────
# Bridge between model and actual functions
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
    elif tool_name == "research":
        result = research_agent(**tool_input)
    elif tool_name == "format_whatsapp_booking":
        result = format_booking(**tool_input)
    else:
        result = f"Unknown tool: {tool_name}"

    # PostToolUse hook — log every tool call
    log_tool_call(tool_name, tool_input, str(result)[:200])
    return result


# ── AGENT LOOP ─────────────────────────────────────────────────────────────
# Same 7-step loop — Anthropic syntax
# Key differences from Groq:
#   - stop_reason: "end_turn" and "tool_use"
#   - response.content is list of blocks
#   - tool inputs already dictionaries
#   - tool results go back as "user" role

def run_agent(user_message, messages=None):
    # Input validation — reject empty messages
    if not user_message or not user_message.strip():
        return "Please describe what you need help with."

    # Load conversation from file if no messages passed
    # Day 10 — file-based memory
    if messages is None:
        messages = load_conversation()

    # Append new user message
    messages.append({"role": "user", "content": user_message})

    while True:
        # Gate 1 — catch API failures
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system="You are a towing assistant for Khopfa Towing in Limpopo. ALWAYS call calculate_tow_price before quoting any price. Pass after_hours as true if customer mentions night, evening, after 7pm, Sunday or weekend. NEVER assume or estimate distance from location names — always ask the customer for exact kilometres. You can search the web and read and write files when asked. Politely refuse anything unrelated to towing.",
                messages=messages,
                tools=tools
            )
        except Exception as e:
            return f"I'm having trouble connecting right now. Please try again. (Error: {str(e)})"

        stop_reason = response.stop_reason

        # Step 3 — model is done, return final answer
        if stop_reason == "end_turn":
            # Extract text from content blocks
            answer = ""
            for block in response.content:
                if block.type == "text":
                    answer += block.text
            # Save as plain text — not raw Anthropic objects
            # Why: Anthropic objects can't be serialised to JSON for file storage
            messages.append({"role": "assistant", "content": answer})
            # Save conversation after every turn — persistent memory
            save_conversation(messages)
            return answer

        # Step 4 — model wants tools
        if stop_reason == "tool_use":
            # Save assistant content as plain text for serialisation
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            messages.append({"role": "assistant", "content": assistant_content})

            # Step 5 — collect ALL tool results before sending any back
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

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
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            # Step 6 — send ALL results as ONE user message
            messages.append({"role": "user", "content": tool_results})

            # Step 7 — loop back to Step 1


# ── ENTRY POINT ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(run_agent("what did I say my name was again?"))