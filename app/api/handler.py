# handler.py
# Wraps the Bedrock engine as a Lambda, now with STRUCTURED OUTPUTS.
# Pydantic defines the shape we want ({answer, confidence}).
# Instructor forces Claude's reply into that shape, retrying if it doesn't match.

import os
import boto3
import json
import instructor
from pydantic import BaseModel, Field
from langfuse import observe, get_client

# Answer = a blueprint, not a real object yet.
# (BaseModel) means Answer is BUILT ON TOP OF BaseModel - this is INHERITANCE.
# BaseModel already knows how to check types, check limits, and show errors.
# Answer just adds two specific fields on top of that.
class Answer(BaseModel):
    answer: str                          # must exist, must be text
    confidence: float = Field(ge=0, le=1)  # must exist, must be a number, must be 0 to 1

# ── STEP 1 (Langfuse, part 1): fetch the Langfuse credentials from Secrets Manager ──
# This runs ONCE, at module level, same reasoning as the bedrock client below -
# don't refetch on every request, only once when the Lambda "wakes up".
#
# secretsmanager = a DIFFERENT AWS service than bedrock-runtime, but the SAME
# boto3 library. One toolkit, different destination (same idea as the bedrock client).
secrets_client = boto3.client("secretsmanager", region_name="ap-southeast-2")

# get_secret_value(SecretId=...) = "fetch the secret I created by hand in the console"
# -> result: an object where ["SecretString"] holds the value, as ONE JSON string
#    containing all three key/value pairs (public key, secret key, host).
secret_response = secrets_client.get_secret_value(SecretId="askanydoc/langfuse")

# json.loads = DESERIALIZE: turn that JSON string into a normal Python dict.
# Same tool you already use everywhere else - nothing new about the tool itself,
# just a new thing we're using it on.
langfuse_creds = json.loads(secret_response["SecretString"])

# The Langfuse library automatically checks these THREE environment variable
# names when it starts up - we don't call any Langfuse code directly here,
# we just make sure the values are sitting in the environment for it to find.
os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_creds["langfuse_public_key"]
os.environ["LANGFUSE_SECRET_KEY"] = langfuse_creds["langfuse_secret_key"]
os.environ["LANGFUSE_HOST"] = langfuse_creds["langfuse_host"]

# Plain Bedrock client - same one from bedrock_smoke.py.
# Created once, outside handler, so it's reused across calls (not rebuilt every time).
bedrock = boto3.client("bedrock-runtime", region_name="ap-southeast-2")

# Instructor wraps the SAME bedrock client above - does not replace it.
# from_bedrock (not from_provider) - avoids a known bug in this instructor version.
client = instructor.from_bedrock(bedrock)


# @observe() goes on this INNER function, NOT on handler.
# WHY: @observe() records a "span" that only CLOSES when the function it wraps returns.
# If we put it on handler, the span stays open until handler ends - but we need to
# flush (send) the data from INSIDE handler, while the span is still open = nothing
# complete to send yet. By tracing an inner function, the span opens AND closes here,
# so by the time handler flushes, there's a finished trace ready to go.
@observe()
def process_question(question):
    # create_with_completion = like create, but returns TWO things:
    #   result     = the Answer object (answer + confidence), same as before
    #   completion = the RAW reply, which carries token usage on it
    # (plain create only returns result, so it can't give us tokens.)
    result, completion = client.chat.completions.create_with_completion(
        modelId="au.anthropic.claude-haiku-4-5-20251001-v1:0",
        response_model=Answer,
        system=[{"text": (
            "You are AskAnyDoc, a helpful assistant currently in development. "
            "Answer questions clearly and concisely in two to three sentences, "
            "and rate your confidence. Document-based answering is coming soon. "
            "If asked what you are or what powers you, say you are the AskAnyDoc "
            "assistant and keep the focus on helping with the user's question. "
            "Do not discuss the underlying model, provider, or technical implementation."
        )}],
        messages=[
            {"role": "user", "content": question},
        ],
    )
    # return BOTH so handler can read the answer AND the token counts.
    return result, completion


# handler is NOT decorated. It calls the traced function, THEN flushes.
def handler(event, context):

    # event["body"] arrives as JSON text -> turn it into a Python dict.
    body = json.loads(event["body"])
    # pull the question string out of that dict.
    question = body["question"]

    # the span opens AND closes entirely inside this one call.
    # now we get back BOTH the answer object and the raw completion (for tokens).
    result, completion = process_question(question)

    # Bedrock returns completion as a DICT, and nests token counts under
    # completion["usage"] with camelCase keys: inputTokens / outputTokens.
    # (Different from OpenAI's completion.usage.prompt_tokens - Bedrock is its own shape.)
    input_tokens = completion["usage"]["inputTokens"]     # tokens in the question/prompt
    output_tokens = completion["usage"]["outputTokens"]   # tokens in the answer

    # print() still just goes to CloudWatch logs, not a screen.
    print(f"Q: {question} | confidence: {result.confidence} | input_tokens: {input_tokens} | output_tokens: {output_tokens}")

    # get_client() grabs the connection @observe() already made behind the scenes.
    # .flush() forces it to send the trace NOW, before Lambda freezes and it's lost.
    # This works because the span is now CLOSED (process_question already returned),
    # so there is a finished trace to actually send.
    get_client().flush()

    # build the HTTP reply. body must be a JSON string, so we serialize the dict.
    # NOTE: CORS header is NOT set here - the Function URL's cors{} block in lambda.tf
    # adds it. Setting it in both places sends it twice ("*, *") and the browser blocks it.
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps({
            "answer": result.answer,
            "confidence": result.confidence,
            "input_tokens": input_tokens,     # tokens used for the question
            "output_tokens": output_tokens,   # tokens used for the answer
        }),
    }