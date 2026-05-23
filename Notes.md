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

 #Tool Schema
This is the description of available tools, when to use and how to use them.

#Execute Tool
This tool readsand interpret the input, it finds the right function to solve input context and runs it

#Total building experience
Building agent.py is the start of more raw agents from scratch,I domnt really understand python but i can read code. The setup for me was way crazier, how to know if environment is ready and good to build. The reasoning behiund setups, secondly the tool schema and the rest of code is something I still need to study, hopefully it contributes to my final documentation. Wrote for claude.ai and chatgpt.