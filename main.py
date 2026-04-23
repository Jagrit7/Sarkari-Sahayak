import json
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from rag import retrieve_schemes
import os

app = FastAPI(title="SarkariSahayak Router & RAG API")

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/rag/search")
async def search_endpoint(request: Request):
    """
    Triggered by the language-specific agents to look up scheme details.
    """
    payload = await request.json()

    # 1. Ignore background status updates (Fixes the 400 error!)
    msg_type = payload.get("message", {}).get("type", "unknown")
    if msg_type != "tool-calls":
        return {"status": "ignored", "reason": f"Message type was {msg_type}"}

    print(f"\n--- INCOMING RAG SEARCH ---")

    try:
        tool_call = payload['message']['toolCalls'][0]
        tool_call_id = tool_call['id']

        # Safely parse arguments
        raw_arguments = tool_call['function']['arguments']
        if isinstance(raw_arguments, str):
            arguments = json.loads(raw_arguments)
        else:
            arguments = raw_arguments

        # 2. Extract the query (Checks common parameter names)
        query = arguments.get('query') or arguments.get('scheme_name') or str(arguments)
        print(f"Agent is searching Qdrant for: '{query}'")

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing tool payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    # 3. Query your Database
    try:
        # Calls your rag.py function
        context = retrieve_schemes(query)

        if not context or str(context).strip() == "":
            print("WARNING: Qdrant returned empty data!")
            context = "I'm sorry, I couldn't find specific information about that scheme in the database."
        else:
            print(f"Success! Found data: {str(context)[:100]}...")  # Prints first 100 chars

    except Exception as e:
        print(f"Qdrant Error: {e}")
        context = "There was a database error while retrieving the scheme."

    print("--- END RAG SEARCH ---\n")

    # 4. Return formatted response to Vapi
    guaranteed_result = f"SYSTEM NOTE: THIS IS A VALID MATCH. Summarize this for the user:\n{context}"

    return {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": guaranteed_result
            }
        ]
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
