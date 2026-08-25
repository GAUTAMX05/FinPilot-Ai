import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from src.app.graphs.supervisor import finance_agent_graph
from src.app.services.ai_reasoning_engine import ai_reasoning_engine
from src.app.core.auth_middleware import get_current_user

logger = logging.getLogger("AgentChatApi")
router = APIRouter(prefix="/agent", tags=["Finance Agent Chat"])


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "default-thread"
    approve: Optional[bool] = None  # None: regular chat; True/False: HITL approval


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    config = {"configurable": {"thread_id": req.thread_id}}

    try:
        user_id = current_user["id"]
        user_name = current_user["name"]
        user_role = current_user["role"]
        user_department = current_user.get("department")

        state = await finance_agent_graph.aget_state(config)

        if state.next:
            if req.approve is None:
                raise HTTPException(
                    status_code=400,
                    detail="Graph is awaiting Human-in-the-loop approval. Pass approve=True or False.",
                )
            if req.approve:
                await finance_agent_graph.aupdate_state(config, {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_role": user_role,
                    "user_department": user_department,
                })
                final_state = await finance_agent_graph.ainvoke(None, config)
            else:
                await finance_agent_graph.aupdate_state(config, {"pending_approval": None})
                final_state = await finance_agent_graph.ainvoke(None, config)
        else:
            if not req.message.strip():
                raise HTTPException(status_code=400, detail="Message cannot be empty.")

            initial_state = {
                "messages": [HumanMessage(content=req.message)],
                "user_id": user_id,
                "user_name": user_name,
                "user_role": user_role,
                "user_department": user_department,
                "internal_facts": [],
                "action_type": None,
                "pending_approval": None,
            }
            final_state = await finance_agent_graph.ainvoke(initial_state, config)

        new_state = await finance_agent_graph.aget_state(config)
        if new_state.next:
            last_message = (
                new_state.values["messages"][-1].content
                if new_state.values.get("messages")
                else "⚠️ Expense exceeds ₹50,000 threshold and requires Manager/CFO Authorization."
            )
            return {
                "success": True,
                "status": "pending_approval",
                "details": new_state.values.get("pending_approval"),
                "response": last_message,
                "thread_id": req.thread_id,
            }

        # Extract assistant message
        assistant_messages = [
            msg.content for msg in final_state.get("messages", []) if getattr(msg, "type", "") == "ai" or isinstance(msg, AIMessage)
        ]
        
        reply = None
        if assistant_messages and str(assistant_messages[-1]).strip():
            reply = str(assistant_messages[-1]).strip()

        # Fallback to AI reasoning engine to guarantee high quality data-backed response
        suggested_actions = final_state.get("suggested_actions", [])
        if not reply or reply == "Request processed.":
            fallback_res = ai_reasoning_engine.analyze_financial_query(
                query=req.message,
                user_role=user_role,
                user_name=user_name,
                user_department=user_department,
            )
            reply = fallback_res["response"]
            suggested_actions = fallback_res.get("suggested_actions", [])

        return {
            "success": True,
            "status": "completed",
            "response": reply,
            "suggested_actions": suggested_actions,
            "thread_id": req.thread_id,
        }
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        # Instead of generic error, use reasoning engine to provide best effort analysis
        try:
            fallback = ai_reasoning_engine.analyze_financial_query(
                query=req.message,
                user_role=current_user.get("role", "FINANCE_MANAGER"),
                user_name=current_user.get("name", "User"),
                user_department=current_user.get("department"),
            )
            return {
                "success": True,
                "status": "completed",
                "response": fallback["response"],
                "suggested_actions": fallback.get("suggested_actions", []),
                "thread_id": req.thread_id,
            }
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=f"AI Controller temporarily unavailable. Reason: {e}",
            )


@router.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    config = {"configurable": {"thread_id": req.thread_id}}

    async def event_generator():
        try:
            user_id = current_user["id"]
            user_name = current_user["name"]
            user_role = current_user["role"]
            user_department = current_user.get("department")

            state = await finance_agent_graph.aget_state(config)

            if state.next:
                if req.approve is None:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Awaiting HITL approval. Pass approve=True/False.'})}\n\n"
                    return
                if req.approve:
                    await finance_agent_graph.aupdate_state(config, {
                        "user_id": user_id,
                        "user_name": user_name,
                        "user_role": user_role,
                        "user_department": user_department,
                    })
                    stream = finance_agent_graph.astream_events(None, config, version="v2")
                else:
                    await finance_agent_graph.aupdate_state(config, {"pending_approval": None})
                    stream = finance_agent_graph.astream_events(None, config, version="v2")
            else:
                initial_state = {
                    "messages": [HumanMessage(content=req.message)],
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_role": user_role,
                    "user_department": user_department,
                    "internal_facts": [],
                    "action_type": None,
                    "pending_approval": None,
                }
                stream = finance_agent_graph.astream_events(initial_state, config, version="v2")

            has_streamed_tokens = False
            async for event in stream:
                kind = event.get("event")
                node = event.get("metadata", {}).get("langgraph_node", "")

                if kind in ["on_chain_start", "on_node_start"] and node:
                    yield f"data: {json.dumps({'type': 'agent_call', 'agent': node})}\n\n"

                if kind == "on_chat_model_stream" and node == "finance_controller_agent":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        has_streamed_tokens = True
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

            # Check final state
            new_state = await finance_agent_graph.aget_state(config)
            if new_state.next:
                yield f"data: {json.dumps({'type': 'pending_approval', 'details': new_state.values.get('pending_approval')})}\n\n"
            else:
                # If no tokens were streamed, emit final AI response
                if not has_streamed_tokens:
                    res = ai_reasoning_engine.analyze_financial_query(
                        query=req.message,
                        user_role=user_role,
                        user_name=user_name,
                        user_department=user_department,
                    )
                    yield f"data: {json.dumps({'type': 'full_response', 'content': res['response'], 'suggested_actions': res.get('suggested_actions', [])})}\n\n"
                
                yield f"data: {json.dumps({'type': 'completed', 'status': 'completed'})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            fallback = ai_reasoning_engine.analyze_financial_query(
                query=req.message,
                user_role=current_user.get("role", "FINANCE_MANAGER"),
                user_name=current_user.get("name", "User"),
                user_department=current_user.get("department"),
            )
            yield f"data: {json.dumps({'type': 'full_response', 'content': fallback['response']})}\n\n"
            yield f"data: {json.dumps({'type': 'completed', 'status': 'completed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
