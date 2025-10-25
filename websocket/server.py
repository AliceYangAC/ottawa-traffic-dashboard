from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

app = FastAPI()
clients = []

# Explicitly load the .env file from this folder
BASE_DIR = os.path.dirname(__file__)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

PORT = int(os.getenv("PORT"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        clients.remove(websocket)

@app.post("/broadcast")
async def broadcast(request: Request):
    data = await request.json()
    events = data.get("events")
    print(f"Received broadcast with {len(events)} events")
    if not isinstance(events, list):
        return JSONResponse(status_code=422, content={"error": "Expected 'events' to be a list"})
    
    for client in clients:
        await client.send_json({"events": events})
    
    return {"status": "sent", "clients": len(clients)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
