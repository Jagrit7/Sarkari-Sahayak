import json
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from rag import retrieve_schemes

app = FastAPI(title="SarkariSahayak Router & RAG API")


@app.post("/route_call")
async def route_call(request: Request):
    """
    Triggered by the Vapi Greeter Agent when a DTMF key is pressed or a language is spoken.
    Transfers the call to the corresponding language agent.
    """
    payload = await request.json()

    # 1. Ignore background status updates from Vapi
    msg_type = payload.get("message", {}).get("type", "unknown")
    if msg_type != "tool-calls":
        return {"status": "ignored", "reason": f"Message type was {msg_type}"}

    try:
        # Parse Vapi's webhook structure
        tool_call = payload['message']['toolCalls'][0]
        tool_call_id = tool_call['id']

        # Safely handle 'arguments' whether Vapi sends it as a string or a dict
        raw_arguments = tool_call['function']['arguments']
        if isinstance(raw_arguments, str):
            arguments = json.loads(raw_arguments)
        else:
            arguments = raw_arguments

        # Force it to string so it perfectly matches the routing_map keys
        digit = str(arguments.get('digit'))

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing routing payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid Vapi payload format")

    # 2. Map your DTMF inputs to your specific Vapi Assistant IDs
    routing_map = {
        "1": "0abbff07-4576-484d-b70e-3c3df5a3bbb3",  # English
        "2": "4c8d183d-6d59-49a4-b3fe-c389554dc7ec",  # Hinglish
        "3": "0fcab1df-8a1d-417a-91b6-fba0cb11d74a",  # Tamil
        "4": "71ed0a65-9c01-40cc-a3fc-409f8ede1557",  # Gujarati
        "5": "79830d78-82c4-44bc-9668-468508c61d03",  # Punjabi
        "6": "407b8b69-9fda-4258-9b82-be5f0fd451dd",  # Malayalam
        "7": "54914439-9080-47d6-bf77-0c479de31071",  # Telugu
    }

    destination_agent = routing_map.get(digit)

    if not destination_agent:
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": f"Error: Invalid language selection. Received digit: {digit}"
            }]
        }

    # 3. Execute the internal Vapi transfer
    return {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": "Transferring call now.",
                "forwardingCommand": {
                    "destination": {
                        "type": "assistant",
                        "assistantId": destination_agent  # Ensure this is the correct UUID
                    }
                }
            }
        ]
    }


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
    # Runs the server on localhost port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)