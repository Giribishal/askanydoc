# bedrock_smoke.py
# Purpose: prove that THIS code, on my laptop, can reach Claude on Bedrock,
# send a prompt, and read back the answer + real token counts.
# A throwaway "smoke test" — minimal proof the plumbing works before Lambda.

# ── imports ──────────────────────────────────────────────────────────────────
# import boto3
#   = "load the AWS SDK for Python — my toolkit for talking to AWS from code"
#   → result: the `boto3` library is available below
# import json
#   = "load Python's built-in JSON tool — converts between dicts and JSON text"
#   → result: the `json` module is available below
# Terms:
#   import → STATEMENT that loads a MODULE (reusable code library) into this file
#   boto3  → the AWS SDK (library); same power as the Week 1 CLI, but from code
#   json   → built-in MODULE for dict↔JSON string conversion
import boto3
import json

# ── create the Bedrock client ────────────────────────────────────────────────
# bedrock = boto3.client("bedrock-runtime", region_name="ap-southeast-2")
#   = "boto3, open a connection to Bedrock's model-CALLING (bedrock-runtime service) service, in Sydney"
#   → result: a client OBJECT stored in variable `bedrock` (a connection handle;
#             nothing is sent to AWS yet — this just creates the handle)
# Terms:
#   boto3                        → the MODULE (imported above)
#   .client(...)                 → a METHOD on boto3 (dot = ATTRIBUTE ACCESS:
#                                  "call client() belonging to boto3")
#   "bedrock-runtime"  (arg 1)   → POSITIONAL ARGUMENT (string): meaning set by
#                                  POSITION. WHAT = model-calling half of Bedrock
#                                  (vs "bedrock" = the management half)
#   region_name="ap-southeast-2" → KEYWORD ARGUMENT (string): meaning set by LABEL.
#                                  WHERE = Sydney
#   bedrock = ...                → ASSIGNMENT: bind the RETURN VALUE to `bedrock`
bedrock = boto3.client("bedrock-runtime", region_name="ap-southeast-2")

# ── confirm the client was created ───────────────────────────────────────────
# print("Bedrock client created OK:", bedrock.meta.region_name)
#   = "show a success message, plus the region the client reports back"
#   → result: prints `Bedrock client created OK: ap-southeast-2`
#             (only works if the line above succeeded — code runs top to bottom,
#              so `bedrock` must already exist)
# Terms:
#   print(...)               → built-in FUNCTION: writes to standard output
#   "Bedrock client..."      → string ARGUMENT (positional)
#   bedrock.meta.region_name → ATTRIBUTE ACCESS chain (no parentheses = READING an
#                              attribute, not calling a method)
print("Bedrock client created OK:", bedrock.meta.region_name)

# Write the actual question as a dictionary: which Claude version rules to follow (anthropic_version),
# how long the answer can be (max_tokens), the system instruction ("be concise"), and the actual user message.
# Terms:
#   { }        → DICT LITERAL (key→value pairs) — this is DATA, not a function
#   "messages" → its value is a LIST ([ ]) containing one DICT (the user turn)
#   fields:
#     anthropic_version → string: required version (boilerplate)
#     max_tokens        → int: cap on OUTPUT length (safety + cost guard)
#     system            → string: standing rules / role for this call
#     messages          → list of dicts: the conversation (here, one user message)
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 300,
    "system": "You are a concise assistant. Answer in two sentences.",
    "messages": [
        {"role": "user", "content": "What is the Australian Cyber Security Centre?"}
    ],
}

# ── send the request ─────────────────────────────────────────────────────────
# response = bedrock.invoke_model(modelId=..., body=...)
#   = "send my request to a specific model, and get its response back"
#   → result: a response OBJECT stored in `response` (holds the answer as raw bytes)
# Terms:
#   .invoke_model(...) → a METHOD on the `bedrock` client object
#   modelId=...        → KEYWORD ARGUMENT (string): WHICH model. The AU inference
#                        PROFILE id (au. prefix), NOT the bare model id — copied from
#                        the console. Bare id errors: "must use an inference profile".
#   body=json.dumps(request_body)
#                      → KEYWORD ARGUMENT. json.dumps() is a FUNCTION CALL that
#                        SERIALIZES the dict → JSON string (the API expects JSON text)
response = bedrock.invoke_model(
    modelId="au.anthropic.claude-haiku-4-5-20251001-v1:0",
    body=json.dumps(request_body),
)

# ── read the response ────────────────────────────────────────────────────────
# result = json.loads(response["body"].read())
#   = "read the raw JSON answer and turn it back into a usable Python dict"
#   → result: a DICTIONARY stored in `result` (contains answer text + usage counts)
# Terms:
#   response["body"] → INDEXING the response dict by key "body" → a stream of raw bytes - 
#  a container with the data not the real data
#   .read()          → METHOD call on that stream: reads the bytes out - 
#   json.loads(...)  → FUNCTION that DESERIALIZES a JSON string → Python dict
#   (pairing: json.dumps = dict→JSON [serialize, OUT]; json.loads = JSON→dict [IN])
result = json.loads(response["body"].read())

# print the whole parsed dict for now (next step: index into it for answer + usage)
#print(result)

# ── extract just the parts we care about ─────────────────────────────────────
# answer = result["content"][0]["text"]
#   = "reach into the result to pull out the answer string"
#   → result: the plain answer text (no surrounding metadata)
# Terms:
#   result["content"] → INDEX dict by key "content"  → returns a LIST of blocks
#   [0]               → INDEX list by position        → first block (a dict)
#   ["text"]          → INDEX that dict by key "text" → the answer STRING
answer = result["content"][0]["text"]

# input_tokens / output_tokens
#   = "reach into the usage sub-dict for the exact token counts"
#   → result: two ints — the real, measured cost data (not estimates)
# Terms:
#   result["usage"]                  → INDEX dict by key "usage" → a sub-DICT
#   ["input_tokens"]/["output_tokens"] → INDEX that sub-dict → ints
input_tokens = result["usage"]["input_tokens"]
output_tokens = result["usage"]["output_tokens"]

# ── compute the cost (AU Haiku 4.5 on-demand rates) ──────────────────────────
# Per-token rates for the AU profile (base $1/$5 per 1M + ~10% AU premium):
#   input  = $1.10 / 1,000,000 = 0.0000011 per token
#   output = $5.50 / 1,000,000 = 0.0000055 per token
# cost = (input_tokens × input_rate) + (output_tokens × output_rate)
#   = "turn the token counts into actual dollars"
#   → result: cost of THIS call in USD
# Terms:
#   0.0000011 / 0.0000055 → float CONSTANTS (the per-token prices)
#   * and +               → arithmetic OPERATORS
#   cost = ...            → ASSIGNMENT: store the computed float in `cost`
cost = (input_tokens * 0.0000011) + (output_tokens * 0.0000055)

# ── print a clean report ─────────────────────────────────────────────────────
# print(...) with f-strings
#   = "show the answer and the cost breakdown in a readable format"
#   → result: a tidy summary instead of the raw dict
# Terms:
#   f"...{var}..." → an F-STRING: a string with {expressions} filled in inline
#   \n             → newline escape (line break inside the text)
#   :.6f / :,      → FORMAT SPECIFIERS: .6f = 6 decimal places; , = thousands commas
print("\n--- ANSWER ---")
print(answer)
print("\n--- USAGE ---")
print(f"Input tokens:  {input_tokens}")
print(f"Output tokens: {output_tokens}")
print(f"Cost (USD):    ${cost:.6f}")


# request_body = per model family. Values inside request_body = per request
# modelId = per specific model, changeable independent of the body.