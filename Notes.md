## Agent.py
 This is a simple agent built with groq API. Designed for khopfa towing to automate repetitive task based on user experience. Passed a few tools and schemas to describe what the model has to do, it calculates total towing price basedon context inside the instructions.

 ## 7 Agentic loop steps
 Step1- Model receives message with context and what tool to use
 Step2- Model calls a tool and does task till it stops, when it stops it asks fora tool use or its done with the task
 Step3- Model evaluates stop record, is it stop or it needs to use a tool. If stop, modek returns a response to user. If not it proceeds to step4
 Step4- Model decides based on what occured in step3, find tool and do the actual required tool use.
 Step5-Complete task from step four and find results to append them to conversation
 Step6- Model appends response from tool use to conversation, pass to next reevaluation step. 
 Step7- Model retarts loop to check if the info is relevant.

 #System Prompts & why they matter
 These are the instructions you give your model before a conversation starts, they shape model behaviour, tells it what tools to usewhen and how to respond. Basically important model architecture, badly written system prompt breaks model or makes a good model bad, same applies to good written prompts.

 #Tool decision rule-Importance of tools and no tools
 If answers facts and stable no tools are needed model already knows, if answers change overtime and needs real time updates/taking action tools are needed.Adding too many tools causes tool bloat where the model picks the wrong one or calls tools unnecessarily.

 #Tool Schema
This is the description of available tools, when to use and how to use them.

## Execute Tool
This tool reads and interpret the input, it finds the right function to solve input context and runs it

#Total building experience
Building agent.py is the start of more raw agents from scratch,I domnt really understand python but i can read code. The setup for me was way crazier, how to know if environment is ready and good to build. The reasoning behiund setups, secondly the tool schema and the rest of code is something I still need to study, hopefully it contributes to my final documentation. Wrote for claude.ai and chatgpt.

## AGENTv2 & Day 3

## Failure testing
Second day after building agent.py, I took time to test certain break scenarios to see what breaks it, when it hallucinates and when the model is resilient. Of 10 test cases, 4 failed, 1 was partial and the rest were succesful. Will put up 1 scenario of each, since the Agent is demo and built off a towing company, its for auto quotes on towing so I sent the agent an empty input amd the agent gave me a price back. That alone means the agent hallucinated the distance. I then passed it "Tow my car" no distance and rime, it then crashed since no input to calculate from. Lastly I asked how much for a 5km tow, it responded correctly even though the response was not suitable for business.

## Possible solutions
1-Input validation-Reject empty or off topic messages before they hit the model.
Empty message>"Please describe your problem"
Off topic>"I only respond towing questions"
2-Error handling-wrap API calls in ty/except so errors return a message instead of dying.
3-System prompt tightening-Add a rule to answer only towing questions.

## Parallel tool calling
I also went and explored parallel tool calling, why where and when it matters. If an agent is working and expecting two responses at once and its given one at a time it breaks the conversation structure, waiter example; waiter comes to table 5 with 2 people, takes one order and leaves to kitchen with message and then comes back for 2nd order, that breaks kitchen order instead of serving a table once.

so in day3 I put in parallel tool calling and error handling, we want an agent to return a message to a customer even if there was a failure, rather than losing a customer to traceback messages. An agent in production should not die visibly, let it catch the crash and return a message. An agent needs parallel tool calls also, sometimes it needs two responses at once otherwise the API breaks and throws an error.

## Error handling and Parallel tool calling
Handling by gates(1&2)- We build error handling gates around API calls and tool calls. Gate 1 is a try/except rule around API call: Gate1

try:
    response = client.chat.completions.create(...)
except Exception as e:
    return f"I'm having trouble connecting right now. Please try again."

This catches: network failures, API being down and invalid API keys.Basically anything that stop API from completing.

Gate2: around tool execution:

try:
    result = execute_tool(tool_name, tool_input)
except FileNotFoundError:
    result = f"File not found: {tool_input.get('path', 'unknown path')}"
except PermissionError:
    result = f"Permission denied: {tool_input.get('path', 'unknown path')}"
except Exception as e:
    result = f"Tool error: {str(e)}"

This catches file not found, permission denied and tool failures in general.

Difference between two gates, gate1 is outside the loop, catches failure before it happens. Gate2 is inside the loop, catches failures while running a specific tool. Both are important because failures happen at different levels

## Parallel tool calls
Allowing the model to call two tools simultaneously, exaple would be calculating two towing distances at the same time. Wrong thing:
for tool_call in tool_calls:
    result = execute_tool(...)
    messages.append({"role": "tool", ...})  # sends immediately

 sending one result at a time. Problem: APi expects all answers from a batch at once to avoid breaking conversation structure and API returning an error. 
 
 Right thing: Collect all results and send them together:
 tool_results = []

for tool_call in tool_calls:
    result = execute_tool(...)
    tool_results.append({"role": "tool", ...})  # collect, don't send yet

for tool_result in tool_results:
    messages.append(tool_result)  # send all at once after loop

## Lesson of the day
Reliability is not about the model, its about what you build around it. A smart model surrounded by weak prompts is useless and viceversa or maybe simple models and complicated ones

## Agentv3/4 & Day4
A day before reflection with thorough advesarial testing- breaking the agent before anyone does. Same as day 3, agentv2 was tested on more production possible scenarios with intent to fix whatever that breaks even if its not everything but inportant fixes. It was tested on ten scenarios of which 4 passes,4 failed and 2 were partial. Cause of most of those failures was not codebug, it was groq generating malformed json for tool calls & model limitation. 6 fixes were made, resulting in 6 passes and a new agentv3 that is an improvement from v2. It only generated 6 passes from 4, 3 tests improved and 4 failures still going from the same groq problem. the fixes in names:
- FIX 1 — Input validation — empty messages rejected before hitting the model
- FIX 2 — After hours surcharge — 30% surcharge now applied correctly for night/weekend
- FIX 3 — Minimum distance — anything under 10km returns base fee R350
- FIX 4 — Boolean string conversion — after_hours schema changed to string, converted to boolean in execute_tool
- FIX 5 — System prompt loosened — file operations now allowed alongside towing questions
- FIX 6 — Conversation memory — messages list passed as parameter, persists across multiple calls

#Day4 bonus-Tavily intergration for websearch
I then went on to explore modelinfrastruct ure and the tool is uses. Tavily is a web search API for AI agents, built for context windows and not human eyes meaning it returns text readable by agent and not in html. What changed? Websearch now works.

## Lesson of the week
Tool are independent of the model, model routes between tools based on descriptions and overall Groq was the bottleneck of the agent more to be proved on week 2 of phase1. The loop is everything, every framework is a loop wrapped of code. Context engineering matters, system prompts and tool descriptions are the architecture. Badly written descriptions can break a good agent. Harness determines reliability, the gates, error handling and parallel tool calls. A good agent inside a fragile harness is bad and fails in production. Testing is not optional, the test.md doc is proof of engineering. Silent failures are worse than crashes, a hallucinating agent is dangerous.

## Day5 - week 1 reflection
Phase1 week 1 I built my first agent with python only, I didnt know where to start but eventually figured it out. I got confused mostly by understanding what errors mean everytime I came across an error, somewhere I read that errors are alsop readable and at the end they have a message. Proceeding with the agent I also learnt that parallel tool calls are not natural agent capabilities, you as the dev you need to instruct the agent that yes you can.

I then went on with testing, during testing I was surprised by empty search where I searched with nothing expecting the agent to ask for input but it didnt ask, meaning it failed and broke. Amazing thing was me understanding that an agent is a loop that keeps going until stopped, it has sevenn steps, inputting context to the agent and the tools for agent to use. Agent checks message then decide if it needs a tool or it can work on it, then it proceeds for stop with two reasons, tool use or done. Then use tool complete task append message to conversation and restart loop. I now understand that gates are important and they help either i business context or ops.

#Week 2 - Anthropic SDK
Rebuilding entire agent.py on anthropic sdk

## Day 6
CLAUDE.md is a markdown file that lives in the project folder and governs agent behaviour. It contains who the agent is, what tools it has, rules it must never break, and business context. It serves two purposes — permanent system prompt reference and documentation for any developer who opens the project. How you write it determines how the agent behaves — it is architecture not just documentation.

## Day 7
Rebuilt the Khopfa Towing agent on Anthropic SDK. Key differences from Groq:
- stop_reason is "end_turn" not "stop"
- stop_reason is "tool_use" not "tool_calls"
- tool inputs come as Python dictionaries — no json.loads() needed
- tool results go back as "user" role — Anthropic only has user and assistant roles
- response.content is a list of blocks — loop through to find tool_use blocks
- tool schemas use "input_schema" not "parameters", no "type": "function" wrapper

PostToolUse logging hook — runs after every tool execution, logs timestamp, tool name, inputs and result to tool_log.txt. In production this is the audit trail — proof of exactly what the agent calculated for any customer at any time.

Biggest difference from Week 1: everything worked first try. Correct price, correct after hours surcharge, Tavily returning real results. No workarounds needed. Proves that the model matters as much as the harness — Claude must be specifically trained for reliable tool use.

## Day 8 — Sub-agent and ISOLATE primitive
ISOLATE means running a task in a completely separate context. The sub-agent gets its own messages list, its own loop, its own tools — nothing spills into the main conversation.

Built research_agent as a sub-agent. Main agent calls it as a regular tool — doesn't know it's another agent running internally. Sub-agent takes a query, does multiple web searches, returns one clean summary paragraph.

Why isolation matters: complex research would flood the main context with raw search results. Customer conversation gets buried, model loses track. Sub-agent absorbs all that noise in its own bubble and returns one clean result.

The main agent only sees the summary. The customer only sees the answer. All the research noise stayed isolated.

Lesson: ISOLATE is not just a technical pattern — it's a context management strategy. Keep the main conversation lean. Delegate heavy work to isolated workers.

## Known Issue — Distance Assumption
Agent assumes distance from destination names instead of asking.
Example: Polokwane CBD to Makhado Crossing — agent assumed 270km, actual is ~110km.
CLAUDE.md rule says "ask before calculating" but model overrides this with location knowledge.
Fix options:
1. Tighten system prompt — "NEVER assume distance, ALWAYS ask for exact km"
2. Add get_distance tool — search actual driving distance via Tavily
Priority: High — wrong distance = wrong price = bad customer experience
Status: Deferred to agentv4 or production hardening phase

## Day 9 - SDK vs Agent.py
All after using the raw lop and the sdk for agents it actually came down to 4 questions I need to answeer based on what I learnt. What is it that the SDK gives me thst I had to write on the raw agent? I saw that it already converts Json for sgent interpretation, also the loop was/is kind of different. What does it take away or abstract? Firstly its the manual work, secondly control over the agent. How? everything now moves according to SDK, you cant stop loop and verify a result before giving back to users. In the raw loop you can inject logic anywhere — pause before a tool runs, verify a result before sending it back, add a human approval step. The SDK loop runs autonomously — you work with hooks and callbacks instead of direct control. Everything has tradeoffs, what did I see here? Reliability vs Control
SDK gives you reliable infrastructure — clean JSON, correct responses, no crashes. But you trade direct loop control for that reliability. In production that means you can't easily pause the agent before a destructive action — like deleting a file, sending a WhatsApp message to a real customer, or spinning up an AWS server.
For Khopfa Towing — imagine the agent confirms a booking and sends a WhatsApp to a real customer with the wrong price. On a raw loop you could add a human approval step before the message sends. On an automated SDK loop that's harder to inject. That's the real trade-off — speed and reliability vs oversight and control. Lastly, the things I'd add to the SDK: Human in the Loop and confidence scoring.

## Day 10 — File-based conversation memory

Before Day 10 the agent lost all memory when the script stopped. Every new run started fresh — customer had to repeat their name, vehicle, location every time. Not production-ready.

File-based memory solves this. Two functions added:

save_conversation(messages) — converts messages list to JSON text using json.dump() and writes to conversation.json after every turn.

load_conversation() — reads conversation.json on startup using json.load() and returns the messages list. Returns empty list if file doesn't exist — clean start for new customers.

Key lesson: saving raw Anthropic response objects to JSON fails — they contain Python objects that can't be serialised. Fix: extract plain text and tool call details as plain dictionaries before saving. This is why understanding what's inside the messages list matters — if you started on the SDK without building raw first you wouldn't know what to save.

Tested: agent remembered Sipho's name and tow details after script was stopped and restarted. Memory works across sessions.