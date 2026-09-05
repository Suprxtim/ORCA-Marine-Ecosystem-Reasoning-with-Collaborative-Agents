from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel
from src.agents.orchestrator import create_supervisor_graph
from typing import Optional
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ORCA AI API", description="Marine Ecosystem Reasoning with Collaborative Agents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the LangGraph Orchestrator
graph = create_supervisor_graph()

class ChatRequest(BaseModel):
    query: str
    target_language: Optional[str] = "English"

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable not set. Please set it in a .env file or your terminal.")
        
    try:
        # Pass the human query into the state graph
        result = await graph.ainvoke({
            "messages": [HumanMessage(content=request.query)],
            "target_language": request.target_language
        })
        
        # The graph executes, and we want the final meaningful output
        final_message = ""
        for msg in reversed(result["messages"]):
            if getattr(msg, "type", "") == "ai" or getattr(msg, "type", "") == "AIMessageChunk":
                content = msg.content
                if isinstance(content, list):
                    text_blocks = [block.get("text", "") for block in content if isinstance(block, dict) and "text" in block]
                    content = "".join(text_blocks)
                
                content = str(content).strip()
                if content and content != "[]":
                    final_message = content
                    break
                    
        if not final_message:
            final_message = "No clear response provided by the agents."
            
        return ChatResponse(response=final_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing agent graph: {str(e)}")

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable not set. Please set it in a .env file or your terminal.")
        
    async def event_generator():
        try:
            async for event in graph.astream_events({
                "messages": [HumanMessage(content=request.query)],
                "target_language": request.target_language
            }, version="v1"):
                kind = event["event"]
                name = event["name"]
                
                # We yield SSE events. Format: "data: <json>\n\n"
                data_payload = {
                    "event": kind,
                    "name": name,
                    "content": ""
                }
                
                if kind == "on_chat_model_stream":
                    tags = event.get("tags", [])
                    if "visualization_llm" not in tags and "geospatial_llm" not in tags:
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content"):
                            if isinstance(chunk.content, str):
                                data_payload["content"] = chunk.content
                            elif isinstance(chunk.content, list):
                                text_blocks = [b.get("text", "") for b in chunk.content if isinstance(b, dict) and "text" in b]
                                data_payload["content"] = "".join(text_blocks)
                                
                        yield f"data: {json.dumps(data_payload)}\n\n"
                
                if kind == "on_tool_end":
                    tool_output = event.get("data", {}).get("output", "")
                    data_payload["output"] = tool_output
                    yield f"data: {json.dumps(data_payload)}\n\n"
                
                # Intercept the visualization node output to stream layers
                if kind == "on_chain_end" and name == "vis_node_wrapper":
                    output = event["data"].get("output", {})
                    if "layers" in output:
                        layers_payload = {
                            "event": "on_layers_ready",
                            "layers": output["layers"]
                        }
                        yield f"data: {json.dumps(layers_payload)}\n\n"
                        
                # Add formatting newlines between major agents
                if kind == "on_chain_end" and name in ["marine_node", "weather_node"]:
                    yield f"data: {json.dumps({'event': 'on_chat_model_stream', 'content': '\n\n---\n\n'})}\n\n"
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_payload = {"error": f"Error executing agent graph: {str(e)}"}
            yield f"data: {json.dumps(error_payload)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "ORCA API"}
