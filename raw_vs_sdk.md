# Raw SDK vs Anthropic SDK — Analysis
## Phase 1 Week 1 vs Week 2

## Question 1 — What building raw taught me

Building the agent raw in Week 1 gave me deep insight into what is actually happening under the hood. Before Week 1 I knew JSON existed but I did not know what it was used for in real systems. Building raw showed me that the model communicates tool calls as JSON text — and that text has to be parsed into a Python dictionary before your code can use it. That one line, json.loads(tool_call.function.arguments), taught me more about how agents work than any tutorial could.

The Groq JSON crashes were actually valuable. Seeing the agent die because the model generated malformed JSON — and then building Gate 1 and Gate 2 to catch it — taught me why error handling exists. On the Anthropic SDK errors are rare because Claude generates clean JSON every time. But in production you will use multiple APIs, face network failures, rate limits, and timeouts. The gates I built in Week 1 are not just for Groq — they are for every API I will ever call.

The schema was also cleaner on Anthropic — no "type": "function" wrapper, "input_schema" instead of "parameters", and stop reasons that actually make sense — "end_turn" and "tool_use" are more descriptive than "stop" and "tool_calls". Starting on the SDK I would have copied that syntax without understanding what it replaced.
## Question 2 — What Week 1 confirmed going into Week 2

Going into Week 2 everything felt familiar — the loop, the tool schemas, the execute_tool bridge, the messages list. Week 1 confirmed that the architecture is solid regardless of which model you use. The 7 steps work the same way whether you are talking to Groq or Anthropic.

What surprised me was how reliable everything was on Anthropic. Week 1 confirmed the danger of model hallucinations and unreliable tool calling — 4 out of 10 tests failed on Groq. Week 2 confirmed the opposite — Claude Haiku got the price right, the after hours surcharge right, and Tavily working, all on the first try. Same architecture, better model, completely different experience.

CLAUDE.md was also a lesson. I did not load it explicitly in code but writing it forced me to think clearly about what the agent is, what tools it has, and what rules it must follow. That thinking directly shaped the system prompt. CLAUDE.md is a design document first and a technical file second.

## Question 3 — Where Anthropic SDK helps and where it doesn't

The Anthropic SDK makes the agent more reliable at the infrastructure level. JSON is handled correctly every time, tool calls succeed on the first attempt, booleans work without workarounds, and Tavily integration worked immediately without any debugging. Everything that broke repeatedly on Groq just worked on Anthropic.

But the SDK does not fix hallucinations. The distance assumption — agent confidently quoting R3,470 for a 270km tow when the real distance was 110km — happened on Anthropic, not Groq. The model reasoned incorrectly and delivered a wrong answer with full confidence. No amount of reliable JSON handling prevents that.

This is the distinction between infrastructure reliability and reasoning reliability. The SDK solves infrastructure — clean tool calls, correct response format, proper error codes. It does not solve reasoning — the model can still assume distances, make up facts, or misinterpret instructions. That is what Phase 4 evals are for. I will test reasoning failures systematically and fix them through better prompts, tighter rules, and validation logic.

## Question 4 — Raw first or SDK first?

Raw first, always. Starting with the SDK means you build without understanding what you are building. You copy tool schemas, wire up responses, and ship something that works — but you do not know why it works or what to do when it breaks.

Building raw forces you to make every decision yourself. You write the while True loop and understand why it loops. You write json.loads() and understand why JSON needs converting. You write Gate 1 and Gate 2 and understand what each one is protecting against. You run 10 adversarial tests and document what breaks and why.

When you move to the SDK after building raw, everything makes sense. The cleaner syntax is not magic — you know what it replaced. The reliable tool calling is not luck — you know what unreliable looks like. And when something breaks in production, you know where to look because you built the thing from scratch first.

The junior developer who starts with the SDK builds fast but breaks slowly and silently. The one who starts raw builds slower but understands deeply. In agent engineering, understanding is the skill. The SDK is just syntax.

##complete Summary
All after using the raw lop and the sdk for agents it actually came down to 4 questions I need to answeer based on what I learnt. What is it that the SDK gives me thst I had to write on the raw agent? I saw that it already converts Json for sgent interpretation, also the loop was/is kind of different. What does it take away or abstract? Firstly its the manual work, secondly control over the agent. How? everything now moves according to SDK, you cant stop loop and verify a result before giving back to users. In the raw loop you can inject logic anywhere — pause before a tool runs, verify a result before sending it back, add a human approval step. The SDK loop runs autonomously — you work with hooks and callbacks instead of direct control. Everything has tradeoffs, what did I see here? Reliability vs Control
SDK gives you reliable infrastructure — clean JSON, correct responses, no crashes. But you trade direct loop control for that reliability. In production that means you can't easily pause the agent before a destructive action — like deleting a file, sending a WhatsApp message to a real customer, or spinning up an AWS server.
For Khopfa Towing — imagine the agent confirms a booking and sends a WhatsApp to a real customer with the wrong price. On a raw loop you could add a human approval step before the message sends. On an automated SDK loop that's harder to inject. That's the real trade-off — speed and reliability vs oversight and control. Lastly, the things I'd add to the SDK: Human in the Loop and confidence scoring.