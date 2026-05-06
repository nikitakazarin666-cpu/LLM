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

# HTML фронтенд
HTML = """<!DOCTYPE html>
<html lang="ru">
... (оставь текущий HTML без изменений) ...
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
    
    # --- ПРИВЕТСТВИЕ ---
    if session["state"] == "greeting" and not session["name"]:
        session["name"] = msg
        session["state"] = "budget"
        return JSONResponse({"response": f"Отлично, {msg}! 😊 Теперь давай перейдём к делу. Каким бюджетом ты располагаешь?\n1. 💰 Свои накопления — 500 000 руб.\n2. 🤝 Инвестор — 1 500 000 руб.\n3. 🏦 Кредит — 3 000 000 руб.\nНапиши 1, 2 или 3."})
    
    # --- ВЫБОР БЮДЖЕТА ---
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
    
    # --- ИГРОВОЙ РЕЖИМ ---
    elif session["state"] == "game":
        session["day"] += 1
        state = sim.state().model_dump()
        
        # 1. Рыночное событие (каждый день)
        event = generate_market_event(state, [msg])
        
        # 2. Отчёт CFO (раз в 7 дней)
        cfo_report = ""
        if session["day"] % 7 == 0:
            cfo_report = "\n\n" + generate_cfo_report(state)
        
        response = event.get("event_text", "День прошёл спокойно.") + cfo_report
        
        return JSONResponse({"response": f"☀️ День {session['day']}\n\n{response}"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
