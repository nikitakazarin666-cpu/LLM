cat > /root/LLM/app.py << 'ENDOFFILE'
"""FastAPI-сервер для чат-симулятора кофейни с тремя ролями ИИ."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from env import BusinessSimulator
from mentor.market_engine import generate_market_event
from mentor.virtual_cfo import generate_cfo_report
from mentor.npc_companion import start_npc_dialogue, continue_npc_dialogue
import uvicorn

app = FastAPI(title="PRO Кофе: Чат с Ментором")
sim = BusinessSimulator(scenario_file="scenario_coffee_shop.json", seed=42)
sessions = {}

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRO Кофе: Чат с Ментором</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Georgia', serif; background: #1a1a2e; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .chat-container { width: 100%; max-width: 800px; height: 90vh; background: #16213e; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; }
        .chat-header { background: linear-gradient(135deg, #1a3a2a, #0f3460); padding: 20px; text-align: center; }
        .chat-header h1 { color: #e0c080; font-size: 1.5rem; margin-bottom: 5px; }
        .chat-header p { color: #a0a0c0; font-size: 0.9rem; }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 80%; padding: 12px 18px; border-radius: 15px; line-height: 1.4; animation: fadeIn 0.3s; }
        .message.user { align-self: flex-end; background: #1a4a3a; color: #e0e0e0; }
        .message.mentor { align-self: flex-start; background: #0f3460; color: #e0e0e0; }
        .chat-input { padding: 20px; background: #0f3460; display: flex; gap: 10px; }
        .chat-input input { flex: 1; padding: 12px 18px; border-radius: 10px; border: none; background: #1a1a2e; color: #e0e0e0; font-size: 1rem; }
        .chat-input button { padding: 12px 24px; border-radius: 10px; border: none; background: #c0a060; color: #1a1a2e; font-weight: bold; cursor: pointer; font-size: 1rem; transition: background 0.3s; }
        .chat-input button:hover { background: #e0c080; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>☕ PRO Кофе: Путь к Свободе</h1>
            <p>Чат-симулятор открытия кофейни с ИИ-Ментором</p>
        </div>
        <div class="chat-messages" id="messages"></div>
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Напиши Ментору..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button onclick="sendMessage()">Отправить</button>
        </div>
    </div>
    <script>
        var sessionId = Date.now().toString();
        function addMessage(text, role) {
            var messagesDiv = document.getElementById('messages');
            var msgDiv = document.createElement('div');
            msgDiv.className = 'message ' + role;
            msgDiv.textContent = text;
            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        function sendMessage() {
            var input = document.getElementById('userInput');
            var text = input.value.trim();
            if (!text) return;
            addMessage(text, 'user');
            input.value = '';
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/chat', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        var data = JSON.parse(xhr.responseText);
                        addMessage(data.response, 'mentor');
                    } else {
                        addMessage('Ошибка связи с Ментором. Попробуй ещё раз.', 'mentor');
                    }
                }
            };
            xhr.send(JSON.stringify({ message: text, session_id: sessionId }));
        }
        window.onload = function() {
            addMessage('Приветствую, будущий предприниматель! ☕ Я твой ИИ-Ментор. Расскажи, с чего хочешь начать?', 'mentor');
        };
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    msg = data.get("message", "").strip()
    session_id = data.get("session_id", "default")
    
    if session_id not in sessions:
        sessions[session_id] = {"state": "greeting", "name": None, "budget": None, "day": 0}
    
    session = sessions[session_id]
    
    if session["state"] == "greeting" and not session["name"]:
        session["name"] = msg
        session["state"] = "budget"
        return JSONResponse({"response": f"Отлично, {msg}! 😊 Теперь давай перейдём к делу. Каким бюджетом ты располагаешь?\n1. 💰 Свои накопления — 500 000 руб.\n2. 🤝 Инвестор — 1 500 000 руб.\n3. 🏦 Кредит — 3 000 000 руб.\nНапиши 1, 2 или 3."})
    
    elif session["state"] == "budget":
        if "1" in msg or "накопления" in msg.lower():
            sim.current_state.cash = 500000
            session["budget"] = 500000
        elif "2" in msg or "инвестор" in msg.lower():
            sim.current_state.cash = 1500000
            session["budget"] = 1500000
        elif "3" in msg or "кредит" in msg.lower():
            sim.current_state.cash = 3000000
            session["budget"] = 3000000
        else:
            return JSONResponse({"response": "Пожалуйста, выбери 1, 2 или 3."})
        
        session["state"] = "game"
        session["day"] = 1
        report = generate_cfo_report(sim.state().model_dump())
        return JSONResponse({"response": f"Бюджет установлен! 🎉\n\n{report}"})
    
    elif session["state"] == "game":
        session["day"] += 1
        state = sim.state().model_dump()
        
        event = generate_market_event(state, [msg])
        cfo_report = ""
        if session["day"] % 7 == 0:
            cfo_report = "\n\n" + generate_cfo_report(state)
        
        response = event.get("event_text", "День прошёл спокойно.") + cfo_report
        return JSONResponse({"response": f"☀️ День {session['day']}\n\n{response}"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
ENDOFFILE
docker cp /root/LLM/app.py pro-coffee-app:/app/app.py
docker restart pro-coffee-app && sleep 3 && echo "Готово. Обнови страницу."
