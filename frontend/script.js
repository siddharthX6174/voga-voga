const API_URL = "http://localhost:8000/api";
let SESSION_ID = Date.now(); // Dynamic session ID

document.addEventListener("DOMContentLoaded", () => {
    loadSessions();
    loadHistory();
});

async function loadSessions() {
    try {
        const response = await fetch(`${API_URL}/sessions`);
        const data = await response.json();
        const sessionList = document.getElementById("session-list");
        sessionList.innerHTML = "";
        
        data.sessions.forEach(session => {
            const li = document.createElement("li");
            
            const titleSpan = document.createElement("span");
            titleSpan.innerText = session.name || `Session ${session.id}`;
            titleSpan.className = "session-title";
            li.appendChild(titleSpan);
            
            const delBtn = document.createElement("button");
            delBtn.innerHTML = "&times;";
            delBtn.className = "delete-btn";
            delBtn.title = "Delete Chat";
            delBtn.onclick = (e) => {
                e.stopPropagation();
                deleteSession(session.id);
            };
            li.appendChild(delBtn);

            li.onclick = () => switchSession(session.id);
            if (session.id === SESSION_ID) li.classList.add("active");
            sessionList.appendChild(li);
        });
    } catch (error) {
        console.error("Failed to load sessions:", error);
    }
}

async function deleteSession(id) {
    if (!confirm("Are you sure you want to delete this chat history?")) return;
    try {
        await fetch(`${API_URL}/sessions/${id}`, { method: "DELETE" });
        if (id === SESSION_ID) {
            createNewChat();
        } else {
            loadSessions();
        }
    } catch (error) {
        console.error("Failed to delete session:", error);
    }
}

async function switchSession(id) {
    SESSION_ID = id;
    document.getElementById("chat-box").innerHTML = "";
    await loadHistory();
    loadSessions(); // Re-render to update active class
}

function createNewChat() {
    SESSION_ID = Date.now();
    document.getElementById("chat-box").innerHTML = "";
    loadSessions(); // Re-render to remove active class from past sessions
    appendMessage("agent", "Welcome! How can I assist you today?");
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_URL}/history/${SESSION_ID}`);
        const data = await response.json();
        
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                appendMessage(msg.sender, msg.content);
            });
        } else {
            appendMessage("agent", "Welcome! How can I assist you today?");
        }
    } catch (error) {
        console.error("Failed to load history:", error);
        appendMessage("agent", "Welcome! How can I assist you today?");
    }
}

async function sendMessage() {
    const input = document.getElementById("user-input");
    const text = input.value.trim();
    if (!text) return;

    // Display user message
    appendMessage("user", text);
    input.value = "";

    // Show loading state
    const loadingId = appendMessage("agent", "Thinking...");

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: text, session_id: SESSION_ID })
        });

        const data = await response.json();
        updateMessage(loadingId, data.response);
        
        // Refresh session list so the new dynamic title appears immediately
        loadSessions();
    } catch (error) {
        updateMessage(loadingId, "Error connecting to the backend.");
    }
}

function handleKeyPress(event) {
    if (event.key === "Enter") sendMessage();
}

let messageCounter = 0;

function appendMessage(sender, text) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    const msgId = "msg-" + Date.now() + "-" + (messageCounter++);
    
    msgDiv.id = msgId;
    msgDiv.className = `message ${sender}`;
    msgDiv.innerText = text;
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    return msgId;
}

function updateMessage(id, text) {
    const msgDiv = document.getElementById(id);
    if (msgDiv) {
        msgDiv.innerText = text;
    }
}

async function uploadDocument(file) {
    if (!file) return;
    
    appendMessage("user", `[Uploading document: ${file.name}]`);
    const loadingId = appendMessage("agent", "Uploading and processing document...");
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: "POST",
            body: formData
        });
        
        const data = await response.json();
        if (response.ok) {
            updateMessage(loadingId, data.message);
        } else {
            updateMessage(loadingId, data.detail || "Failed to upload document.");
        }
    } catch (error) {
        updateMessage(loadingId, "Error connecting to the backend for upload.");
    }
}
