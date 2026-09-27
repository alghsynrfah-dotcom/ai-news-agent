from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.services.research_service import run_research
from backend.services.guardrails import validate_research_topic
from backend.memory.session_memory import (
    create_session,
    get_session,
    update_session,
)

app = FastAPI(title="AI News Research Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str
    thread_id: str | None = None
    

class ResearchResponse(BaseModel):
    thread_id: str
    topic: str
    answer: str
    sources: list[dict]
    tools_used: list[str]
    execution_time: float



class FeedbackRequest(BaseModel):
    thread_id: str
    feedback: str
    
@app.get("/")
def root():
    return {"message": "AI News Agent API is running"}


@app.post("/session")
def create_new_session():
    thread_id = create_session()

    return {
        "thread_id": thread_id
    }
@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):

    thread_id = request.thread_id
    feedback = request.feedback.strip().lower()

    # Make sure the session exists
    session = get_session(thread_id)

    if not session:
        return {
            "success": False,
            "message": "Session not found.",
        }

    # Validate feedback value
    if feedback not in {"positive", "negative"}:
        return {
            "success": False,
            "message": "Feedback must be positive or negative.",
        }

    # Save feedback to the session
    update_session(
        thread_id,
        {
            "feedback": feedback,
        },
    )

    return {
        "success": True,
        "thread_id": thread_id,
        "feedback": feedback,
    }

@app.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest):

    topic = request.topic.strip()

    # -----------------------------
    # Guardrail validation
    # -----------------------------

    is_valid, error_message = validate_research_topic(topic)

    if not is_valid:
        return {
            "thread_id": request.thread_id or "",
            "topic": topic,
            "answer": error_message,
            "sources": [],
            "tools_used": [],
            "execution_time": 0,
        }

    # -----------------------------
    # Session / Thread
    # -----------------------------

    thread_id = request.thread_id

    if not thread_id or not get_session(thread_id):
        thread_id = create_session()

    try:

        # -----------------------------
        # Get conversation history
        # -----------------------------

        session = get_session(thread_id)

        history = session["messages"] if session else []

        # -----------------------------
        # Run Agent
        # -----------------------------

        result = run_research(
            topic=topic,
            conversation_history=history,
            thread_id=thread_id,
        )

        # -----------------------------
        # Update session memory
        # -----------------------------

        update_session(
            thread_id,
            {
                "messages": history
                + [
                    {
                        "role": "user",
                        "content": topic,
                    },
                    {
                        "role": "assistant",
                        "content": result["answer"],
                    },
                ],
                "sources": result["sources"],
                "tools_used": result["tools_used"],
            },
        )

        # -----------------------------
        # Return response
        # -----------------------------

        return {
            "thread_id": thread_id,
            "topic": topic,
            "answer": result["answer"],
            "sources": result["sources"],
            "tools_used": result["tools_used"],
            "execution_time": result["execution_time"],
        }

    except Exception as error:

        return {
            "thread_id": thread_id,
            "topic": topic,
            "answer": f"Research error: {str(error)}",
            "sources": [],
            "tools_used": [],
            "execution_time": 0,
        }