# agent.py - Phase 1 Day 2
# A raw tool-using agent for Khopfa Towing built without frameworks
# Uses Groq API + llama model to answer towing questions

import os       # reads environment variables like API keys
import json     # converts model's JSON text into Python dictionaries
from groq import Groq           # official Groq SDK to call the API
from dotenv import load_dotenv  # reads .env file into memory

# Load API keys from .env file into environment
load_dotenv()

# Create our connection to Groq - all API calls go through this client
client = Groq(api_key=os.environ["GROQ_API_KEY"])


# ── TOOLS ──────────────────────────────────────────────────────────────────
# These are real Python functions - they do actual work
# The model never runs these directly - we run them on its behalf

def web_search(query):
    # Fake search for now - in production this would call Tavily API
    # Returns a string result the model can read and use
    return f"Search results for: {query} - Limpopo towing market is growing 15% annually"

def calculate_tow_price(distance_km, after_hours=False):
    # Calculates towing price for Khopfa Towing based on distance
    # after_hours defaults to False - only pass True for night/weekend jobs
    base = 350          # flat callout fee in rands
    per_km = 12         # cost per km after the first 10km
    price = base + (distance_km - 10) * per_km
    if after_hours:
        price = price * 1.3     # 30% surcharge for after hours
    return f"R{price:.0f}"      # return as rands, no decimals

def write_file(path, content):
    # Writes content to a file on disk
    # Used when model is asked to save or export information
    with open(path, 'w') as f:
        f.write(content)
    return f"File written to {path}"   # confirm success to the model


# ── TOOL SCHEMAS ───────────────────────────────────────────────────────────
# This is the menu the model reads - it never sees the actual functions
# name: how the model refers to the tool
# description: tells the model WHEN to use it - this is a prompt not a label
# parameters: tells the model WHAT inputs to pass
# required: inputs the model must always provide

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
    }
]


# ── EXECUTE TOOL ───────────────────────────────────────────────────────────
# Bridge between the model and the actual functions
# Model says which tool and what inputs - we find the function and run it
# **tool_input unpacks the dictionary into individual arguments
# e.g. {"distance_km": 25} becomes calculate_tow_price(distance_km=25)

def execute_tool(tool_name, tool_input):
    if tool_name == "web_search":
        return web_search(**tool_input)
    elif tool_name == "calculate_tow_price":
        return calculate_tow_price(**tool_input)
    elif tool_name == "write_file":
        return write_file(**tool_input)
    else:
        return f"Unknown tool: {tool_name}"


# ── AGENT LOOP ─────────────────────────────────────────────────────────────
# This is the 7-step loop that powers the agent
# Runs until the model says it is done (stop_reason == "stop")

def run_agent(user_message):
    # Step 1 - build the messages list with system context and user message
    messages = [
        {
            "role": "system",
            "content": "You are a towing assistant for Khopfa Towing in Limpopo. ALWAYS call calculate_tow_price before quoting any price. Only call web_search when you genuinely do not know the answer. For simple geography or general knowledge questions, answer directly without tools."
        },
        {"role": "user", "content": user_message}
    ]

    while True:
        # Step 1 - send messages and tools list to the model
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools
        )

        # Step 2 - check why the model stopped
        stop_reason = response.choices[0].finish_reason

        # Step 3 - if done, return the final answer to the user
        if stop_reason == "stop":
            return response.choices[0].message.content

        # Step 4 - model wants to use a tool
        if stop_reason == "tool_calls":
            tool_calls = response.choices[0].message.tool_calls

            # Append assistant message to history so model remembers what it requested
            messages.append(response.choices[0].message)

            # Step 5 - run each tool the model requested
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)  # convert JSON text to dict

                result = execute_tool(tool_name, tool_input)  # run the actual function

                # Step 6 - append tool result to conversation history
                # tool_call_id links this result back to the exact request the model made
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

            # Step 7 - loop back to Step 1 - model may need more tools or is now ready to answer


# ── ENTRY POINT ────────────────────────────────────────────────────────────
# This runs when you execute agent.py directly
# Change the message here to test different scenarios

if __name__ == "__main__":
    print(run_agent("whats the capital of limpopo"))