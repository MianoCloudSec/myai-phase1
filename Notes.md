#Agent.py
 This is a simple agent built with groq API. Designed for khopfa towing to automate repetitive task based on user experience. Passed a few tools and schemas to describe what the model has to do, it calculates total towing price basedon context inside the instructions.

 #7 Agentic loop steps
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

#Execute Tool
This tool reads and interpret the input, it finds the right function to solve input context and runs it

#Total building experience
Building agent.py is the start of more raw agents from scratch,I domnt really understand python but i can read code. The setup for me was way crazier, how to know if environment is ready and good to build. The reasoning behiund setups, secondly the tool schema and the rest of code is something I still need to study, hopefully it contributes to my final documentation. Wrote for claude.ai and chatgpt.

#AGENTv2 & Day 3

#Failure testing
Second day after building agent.py, I took time to test certain break scenarios to see what breaks it, when it hallucinates and when the model is resilient. Of 10 test cases, 4 failed, 1 was partial and the rest were succesful. Will put up 1 scenario of each, since the Agent is demo and built off a towing company, its for auto quotes on towing so I sent the agent an empty input amd the agent gave me a price back. That alone means the agent hallucinated the distance. I then passed it "Tow my car" no distance and rime, it then crashed since no input to calculate from. Lastly I asked how much for a 5km tow, it responded correctly even though the response was not suitable for business.

#Possible solutions
1-Input validation-Reject empty or off topic messages before they hit the model.
Empty message>"Please describe your problem"
Off topic>"I only respond towing questions"
2-Error handling-wrap API calls in ty/except so errors return a message instead of dying.
3-System prompt tightening-Add a rule to answer only towing questions.

#Parallel tool calling
I also went and explored parallel tool calling, why where and when it matters. If an agent is working and expecting two responses at once and its given one at a time it breaks the conversation structure, waiter example; waiter comes to table 5 with 2 people, takes one order and leaves to kitchen with message and then comes back for 2nd order, that breaks kitchen order instead of serving a table once.

so in day3 I put in parallel tool calling and error handling, we want an agent to return a message to a customer even if there was a failure, rather than losing a customer to traceback messages. An agent in production should not die visibly, let it catch the crash and return a message. An agent needs parallel tool calls also, sometimes it needs two responses at once otherwise the API breaks and throws an error.

#Error handling and Parallel tool calling
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

#Parallel tool calls
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

#Lesson of the day
Reliability is not about the model, its about what you build around it. A smart model surrounded by weak prompts is useless and viceversa or maybe simple models and complicated ones

#Agentv3/4 & Day4
A day before reflection with thorough advesarial testing- breaking the agent before anyone does. Same as day 3, agentv2 was tested on more production possible scenarios with intent to fix whatever that breaks even if its not everything but inportant fixes. It was tested on ten scenarios of which 4 passes,4 failed and 2 were partial. Cause of most of those failures was not codebug, it was groq generating malformed json for tool calls & model limitation. 6 fixes were made, resulting in 6 passes and a new agentv3 that is an improvement from v2. It only generated 6 passes from 4, 3 tests improved and 4 failures still going from the same groq problem. the fixes in names:
- FIX 1 — Input validation — empty messages rejected before hitting the model
- FIX 2 — After hours surcharge — 30% surcharge now applied correctly for night/weekend
- FIX 3 — Minimum distance — anything under 10km returns base fee R350
- FIX 4 — Boolean string conversion — after_hours schema changed to string, converted to boolean in execute_tool
- FIX 5 — System prompt loosened — file operations now allowed alongside towing questions
- FIX 6 — Conversation memory — messages list passed as parameter, persists across multiple calls

#Day4 bonus-Tavily intergration for websearch
I then went on to explore modelinfrastruct ure and the tool is uses. Tavily is a web search API for AI agents, built for context windows and not human eyes meaning it returns text readable by agent and not in html. What changed? Websearch now works.

#Lesson of the week
Tool are independent of the model, model routes between tools based on descriptions and overall Groq was the bottleneck of the agent more to be proved on week 2 of phase1. The loop is everything, every framework is a loop wrapped of code. Context engineering matters, system prompts and tool descriptions are the architecture. Badly written descriptions can break a good agent. Harness determines reliability, the gates, error handling and parallel tool calls. A good agent inside a fragile harness is bad and fails in production. Testing is not optional, the test.md doc is proof of engineering. Silent failures are worse than crashes, a hallucinating agent is dangerous.