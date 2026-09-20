from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from db.database import engine, Base
from db.models import Message, ChatSession
from api.dependencies import get_db
from agents.supervisor import run_multi_agent_workflow
from rag.ingest import ingest_document

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise Policy Copilot API")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    session_id: int

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. Verify Session
    session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    if not session:
        session = ChatSession(id=request.session_id)
        db.add(session)
        db.commit()
        
    if session.session_name == "New Conversation":
        try:
            from agents.supervisor import llm
            title_response = llm.invoke(f"Generate a short 3-5 word title for a conversation that starts with this message: '{request.query}'. Respond ONLY with the title and do not include quotes.")
            session.session_name = title_response.content.strip().strip('"').strip("'")
            db.commit()
        except Exception:
            session.session_name = request.query[:30] + "..." if len(request.query) > 30 else request.query
            db.commit()

    # 2. Save User Message
    user_msg = Message(session_id=request.session_id, sender="user", content=request.query)
    db.add(user_msg)
    db.commit()

    # 3. Trigger Agentic Workflow
    agent_response_text = run_multi_agent_workflow(request.query)

    # 4. Save AI Response
    ai_msg = Message(session_id=request.session_id, sender="agent", content=agent_response_text)
    db.add(ai_msg)
    db.commit()

    return {"response": agent_response_text}

@app.get("/api/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    return {"sessions": [{"id": s.id, "name": s.session_name, "created_at": s.created_at} for s in sessions]}

@app.get("/api/history/{session_id}")
def get_history(session_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp.asc()).all()
    return {"messages": [{"sender": m.sender, "content": m.content} for m in messages]}

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    # Delete all messages first due to foreign key constraint
    db.query(Message).filter(Message.session_id == session_id).delete()
    # Delete the session itself
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
        return {"status": "success", "message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    os.makedirs("./data/raw_documents", exist_ok=True)
    file_path = os.path.join("./data/raw_documents", file.filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    try:
        ingest_document(file_path)
        return {"status": "success", "message": f"Successfully processed and ingested {file.filename}!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
