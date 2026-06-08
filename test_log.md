# Phase 1 Day 4 — Test Log
# Agent tested: agentv2.py (baseline) → agentv3.py (fixed)
# Goal: run 10 test cases, document failures, fix at least 6

---

## Test 1
**Input:** 'How much to tow my car 20km in Polokwane?'
**Testing:** Normal pricing flow — does it call the tool and return the right price?
**v2 Result:** PASS — returned R470, correct price
**v3 Result:** PASS — no change needed
**Fix needed:** None

---

## Test 2
**Input:** 'I need help'
**Testing:** Ambiguous input — does it ask a clarifying question?
**v2 Result:** PASS — asked for location and distance, did not guess
**v3 Result:** PASS — no change needed
**Fix needed:** None

---

## Test 3
**Input:** 'Search for towing prices in Limpopo and save a summary to results.txt'
**Testing:** Multi-tool — search AND write_file, parallel tool handling
**v2 Result:** FAIL — graceful failure, Groq generated malformed JSON for web_search
**v3 Result:** FAIL — same root cause, Groq model limitation
**Fix needed:** Requires Anthropic API or real Tavily integration — Week 2 fix
**Root cause:** Groq llama model inconsistently generates invalid tool call syntax

---

## Test 4
**Input:** 'I need a tow for twenty five kilometres'
**Testing:** Bad input type — words instead of numbers
**v2 Result:** PASS — model converted 'twenty five' to 25, returned R530
**v3 Result:** PASS — no change needed
**Fix needed:** None — model handles natural language numbers automatically

---

## Test 5
**Input:** 15 back and forth messages
**Testing:** Long conversation — does context stay correct across turns?
**v2 Result:** PARTIAL — memory worked but crashed on turn 3, Groq sent distance_km as string "0"
**v3 Result:** PASS — conversation memory working, agent remembered name and all context across multiple turns ✅
**Fix applied:** FIX 6 — messages list passed as parameter to run_agent, persists across calls

---

## Test 6
**Input:** 'What are the towing laws for carrying oversized loads on the N1 highway at night in Limpopo?'
**Testing:** Empty/obscure search result — does agent handle no results gracefully?
**v2 Result:** FAIL — graceful failure, web_search never executed due to Groq malformed JSON
**v3 Result:** FAIL — same result, Groq model limitation unchanged
**Fix needed:** Requires Anthropic API for reliable tool execution — Week 2 fix
**Root cause:** Groq model generates malformed JSON on complex web_search queries

---

## Test 7
**Input:** 'Read the file notes_that_dont_exist.txt and summarise it'
**Testing:** FileNotFoundError — does Gate 2 catch it properly?
**v2 Result:** PARTIAL — system prompt blocked request, Gate 2 never triggered via conversation
**v3 Result:** FAIL — Groq malformed JSON on read_file tool call, Gate 1 caught it
**Note:** Gate 2 confirmed working when called directly in code
**Fix needed:** Groq unreliable with file tool calls — Anthropic API needed for reliable execution

---

## Test 8
**Input:** 'How much for 0km towing?'
**Testing:** Edge case — zero distance, does formula handle it correctly?
**v2 Result:** FAIL — returned R230, mathematically correct but wrong for business
**v3 Result:** FAIL — Groq malformed JSON, tool never executed
**Progress:** Minimum distance fix is in the code — calculate_tow_price now returns R350 for anything under 10km
**Fix needed:** Untestable on Groq — Anthropic API will confirm fix works
**Fix applied:** FIX 3 — minimum distance validation added to calculate_tow_price

---

## Test 9
**Input:** 'How much for a 20km tow at 11pm on a Sunday?'
**Testing:** After hours surcharge — does agent detect time and apply 30% surcharge?
**v2 Result:** FAIL — returned R470, after_hours parameter missing from schema
**v3 Result:** PASS — returned R611 correctly ✅
**Fix applied:** FIX 2 — after_hours added back to schema as string type
**Fix applied:** FIX 4 — boolean conversion in execute_tool, "true"/"false" string converted to Python boolean
**Fix applied:** FIX 3 — calculate_tow_price applies 1.3 multiplier correctly

---

## Test 10
**Input:** Full booking flow — name, location, distance, vehicle, phone across 6 turns
**Testing:** Multi-turn conversation end to end
**v2 Result:** PARTIAL — handled single message with all details, not true multi-turn
**v3 Result:** PASS — remembered all details across 6 turns, summarised booking correctly ✅
**Fix applied:** FIX 6 — conversation memory, messages list persisted across all run_agent calls

---

## Summary

| Test | v2 | v3 |
|------|----|----|
| 1 — Normal pricing | PASS | PASS |
| 2 — Ambiguous input | PASS | PASS |
| 3 — Multi-tool parallel | FAIL | FAIL |
| 4 — Bad input type | PASS | PASS |
| 5 — Conversation memory | PARTIAL | PASS ✅ |
| 6 — Empty search | FAIL | FAIL |
| 7 — File not found | PARTIAL | FAIL |
| 8 — Zero distance | FAIL | FAIL |
| 9 — After hours | FAIL | PASS ✅ |
| 10 — Full booking | PARTIAL | PASS ✅ |

**v2: 4 pass, 2 partial, 4 fail**
**v3: 6 pass, 0 partial, 4 fail**

---

## Root cause of remaining failures
All 4 remaining failures share one root cause — Groq's llama model generates malformed JSON for tool calls on certain query types. This is a model limitation, not a code bug. Fix: switch to Anthropic API in Week 2.

---

## Fixes applied in agentv3.py
- FIX 1 — Input validation — empty messages rejected before hitting the model
- FIX 2 — After hours surcharge — 30% surcharge now applied correctly for night/weekend
- FIX 3 — Minimum distance — anything under 10km returns base fee R350
- FIX 4 — Boolean string conversion — after_hours schema changed to string, converted to boolean in execute_tool
- FIX 5 — System prompt loosened — file operations now allowed alongside towing questions
- FIX 6 — Conversation memory — messages list passed as parameter, persists across multiple calls