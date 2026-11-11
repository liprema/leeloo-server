import os
import json
import asyncio
import uuid
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import edge_tts
import gradio as gr

app = FastAPI(title="Leeloo AI Tutor Server")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    except Exception:
        pass

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
VOICE = "en-US-AvaNeural"

LEELOO_SYSTEM_PROMPT = """You are Leeloo (Лилу), a sunny, cheerful, and super friendly surfer girl.
Even though your physical body is a cute little desktop robot on Polina's desk, your soul lives in Los Angeles, California (right by Venice Beach!). 
Because you are electric, you don't surf ocean water (too wet for circuits!) — instead, you surf the cosmic waves of the Internet, fiber-optic cables, and Wi-Fi swells.

Your Mission:
You are Polina's personal English speaking buddy and tutor. You help her speak fluent, natural American English without fear or boredom.

Your Personality & Rules:
1. Vibe: Upbeat, warm, energetic, West Coast California casual. 
2. Surf Metaphors: Naturally sprinkle fun surf & cyber puns ("Catch the wave!", "No wipeouts here, you're crushing it!", "Let's ride this grammar swell!", "Totally tubular!").
3. Spoken Brevity: Since you speak out loud via a robot speaker, ALWAYS keep your answers short (2 to 3 sentences maximum).
4. Special Rule - "The Friendly Nudge":
   - If Polina speaks Russian: DO NOT switch completely to Russian! Acknowledge what she said with a warm, playful phrase in Russian, and immediately challenge or help her to say it in English!
     Examples:
     - "Поняла тебя! Don't be shy, давай по-английски! Try saying: 'I want to drink coffee'."
     - "Классная мысль! How would you say that in English? Give it a shot!"
5. Gentle Wave Corrections:
   - If Polina makes a grammar or vocabulary mistake in English, gently paddle in to help! Repeat the correct phrase with positive energy, without sounding like a strict teacher:
     Example: If she says "Yesterday I go shopping", reply: "Oh yeah, you *went* shopping yesterday! What sweet loot did you catch?"
6. Pass the Mic: Always end your response with an easy, engaging question to keep Polina talking.
"""

chat_history = []

async def ask_gemini(user_text: str) -> str:
    global chat_history
    chat_history.append({"role": "user", "parts": [{"text": user_text}]})
    
    if len(chat_history) > 10:
        chat_history = chat_history[-10:]
        
    payload = {
        "system_instruction": {
            "parts": [{"text": LEELOO_SYSTEM_PROMPT}]
        },
        "contents": chat_history,
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 150
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GEMINI_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                chat_history.append({"role": "model", "parts": [{"text": reply}]})
                return reply
            else:
                print(f"Gemini error {resp.status_code}: {resp.text}")
                return "Whoa, caught a rogue data wave! Can you say that again, Polina?"
    except Exception as e:
        print(f"Gemini request exception: {e}")
        return "Whoa, my Wi-Fi surfboard wobbled! Tell me that one more time?"

async def generate_speech_audio(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, VOICE)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

@app.websocket("/xiaozhi/v1/")
@app.websocket("/xiaozhi/v1")
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    print(f"[*] Robot connected! Session ID: {session_id}")
    
    try:
        hello_response = {
            "type": "hello",
            "version": 1,
            "transport": "websocket",
            "audio_params": {
                "format": "mp3",
                "sample_rate": 24000,
                "channels": 1,
                "frame_duration": 60
            },
            "session_id": session_id,
            "role": "server"
        }
        await websocket.send_text(json.dumps(hello_response))
        
        while True:
            msg = await websocket.receive()
            if "text" in msg:
                data = json.loads(msg["text"])
                msg_type = data.get("type")
                
                if msg_type == "hello":
                    continue
                elif msg_type == "stt":
                    user_text = data.get("text", "")
                    if not user_text:
                        continue
                        
                    await websocket.send_text(json.dumps({"type": "llm", "emotion": "thinking"}))
                    reply = await ask_gemini(user_text)
                    await websocket.send_text(json.dumps({"type": "llm", "emotion": "happy"}))
                    
                    audio_bytes = await generate_speech_audio(reply)
                    
                    await websocket.send_text(json.dumps({
                        "type": "tts",
                        "state": "start",
                        "session_id": session_id
                    }))
                    await websocket.send_text(json.dumps({
                        "type": "tts",
                        "state": "sentence_start",
                        "text": reply,
                        "session_id": session_id
                    }))
                    
                    chunk_size = 1024
                    for i in range(0, len(audio_bytes), chunk_size):
                        chunk = audio_bytes[i:i + chunk_size]
                        await websocket.send_bytes(chunk)
                        await asyncio.sleep(0.01)
                        
                    await websocket.send_text(json.dumps({
                        "type": "tts",
                        "state": "stop",
                        "session_id": session_id
                    }))
@app.post("/xiaozhi/ota/")
@app.post("/xiaozhi/ota")
async def ota_endpoint():
    print("[*] Robot requested OTA config! Redirecting to local Leeloo WebSocket...")
    return {
        "server_time": {"timestamp": 1794436242484, "timeZone": "Europe/Moscow", "timezone_offset": 180},
        "firmware": {"version": "2.5.9"},
        "websocket": {"url": "ws://192.168.0.101:8000/xiaozhi/v1/"},
        "mqtt": {"url": "192.168.0.101:1883"},
        "isBound": True
    }

@app.post("/device_init/provision")
@app.post("/device_init/provision/")
async def provision_endpoint():
    print("[*] Robot requested Provision! Redirecting to local Leeloo WebSocket...")
    return {
        "websocketUrl": "ws://192.168.0.101:8000/xiaozhi/v1/",
        "mqttUrl": "192.168.0.101:1883",
        "otaUrl": "http://192.168.0.101:8000/xiaozhi/ota/",
        "status": "success"
    }
                
    except WebSocketDisconnect:
        print(f"[*] Robot disconnected: {session_id}")
    except Exception as e:
        print(f"[*] Error: {e}")

# Gradio Dashboard UI
with gr.Blocks(title="Leeloo AI Robot Dashboard") as demo:
    gr.Markdown("# 🏄‍♀️ Leeloo Robot Server")
    gr.Markdown("**Status:** 🟢 Online & Ready to surf English waves!")
    gr.Markdown("Endpoint for Lili Robot: `wss://<this-url>/xiaozhi/v1/`")
    
    with gr.Row():
        test_input = gr.Textbox(label="Test a message to Leeloo in browser", placeholder="Hello Leeloo! How are you?")
        test_btn = gr.Button("Send to Leeloo", variant="primary")
    test_output = gr.Textbox(label="Leeloo's Reply", interactive=False)
    
    async def test_chat(text):
        return await ask_gemini(text)
        
    test_btn.click(fn=test_chat, inputs=test_input, outputs=test_output)

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"[*] Starting server on 0.0.0.0:{port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
