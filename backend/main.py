from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.services.research_service import run_research
from backend.services.guardrails import validate_research_topic

from backend.memory.session_memory import (
    create_session,
    get_session,
    update_session,
    get_pending_email,
    clear_pending_email,
)

from backend.tools.email_tool import send_email
from langgraph.types import interrupt

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


# --------------------------------------------------
# Request / Response Models
# --------------------------------------------------

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


class EmailApprovalRequest(BaseModel):
    thread_id: str
    approved: bool


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AI News Agent API is running"
    }


# --------------------------------------------------
# Session
# --------------------------------------------------

@app.post("/session")
def create_new_session():
    thread_id = create_session()

    return {
        "thread_id": thread_id
    }


# --------------------------------------------------
# Feedback
# --------------------------------------------------

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    thread_id = request.thread_id
    feedback = request.feedback.strip().lower()

    session = get_session(thread_id)

    if not session:
        return {
            "success": False,
            "message": "Session not found.",
        }

    if feedback not in {"positive", "negative"}:
        return {
            "success": False,
            "message": "Feedback must be positive or negative.",
        }

    update_session(
        thread_id,
        {
            "feedback": feedback
        },
    )

    return {
        "success": True,
        "thread_id": thread_id,
        "feedback": feedback,
    }


# --------------------------------------------------
# Email Approval
# --------------------------------------------------

@app.post("/email/approval")
def email_approval(request: EmailApprovalRequest):
    thread_id = request.thread_id

    pending_email = get_pending_email(thread_id)

    if not pending_email:
        return {
            "success": False,
            "message": "No pending email request found.",
        }

    # User rejected the email
    if not request.approved:
        clear_pending_email(thread_id)

        return {
            "success": True,
            "message": "Email sending was rejected.",
        }
@app.get("/email/pending/{thread_id}")
def get_pending_email_request(thread_id: str):
    pending_email = get_pending_email(thread_id)

    if not pending_email:
        return {
            "pending": False,
            "email": None,
        }

    return {
        "pending": True,
        "email": pending_email,
    }
    # User approved the email
    result = send_email.invoke(
        {
            "recipient": pending_email["recipient"],
            "subject": pending_email["subject"],
            "body": pending_email["body"],
        }
    )

    clear_pending_email(thread_id)

    if result.startswith("Error:"):
        return {
            "success": False,
            "message": result,
        }

    return {
        "success": True,
        "message": result,
    }


# --------------------------------------------------
# Research
# --------------------------------------------------

@app.post(
    "/research",
    response_model=ResearchResponse,
)
def research(request: ResearchRequest):
    topic = request.topic.strip()

    is_valid, error_message = validate_research_topic(
        topic
    )

    if not is_valid:
        return {
            "thread_id": request.thread_id or "",
            "topic": topic,
            "answer": error_message,
            "sources": [],
            "tools_used": [],
            "execution_time": 0,
        }

    thread_id = request.thread_id

    if not thread_id or not get_session(thread_id):
        thread_id = create_session()

    try:
        session = get_session(thread_id)

        history = (
            session["messages"]
            if session
            else []
        )

        result = run_research(
            topic=topic,
            conversation_history=history,
            thread_id=thread_id,
        )

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