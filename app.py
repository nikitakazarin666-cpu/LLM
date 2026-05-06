"""FastAPI-сервер для чат-симулятора кофейни."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from mentor import get_mentor_advice
from env import BusinessSimulator
import os

app = FastAPI(title="PRO Кофе: Чат с Ментором")

sim = BusinessSimulator(scenario_file="scenario_coffee_shop.json", seed=42)
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("chat.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message.strip()
    
    if session_id not in sessions:
        sessions[session_id] = {"state": "greeting", "name": None, "budget": None}
    
    session = sessions[session_id]
    
    # Логика чата — те же этапы, что были в Gradio
    if session["state"] == "greeting" and not session["name"]:
        session["name"] = user_message
        session["state"] = "budget"
        return JSONResponse({"response": f"Отлично, {user_message}! 😊 Теперь давай перейдём к делу. Каким бюджетом ты располагаешь?\n1. 💰 Свои накопления — 500 000 руб.\n2. 🤝 Инвестор — 1 500 000 руб.\n3. 🏦 Кредит — 3 000 000 руб.\nНапиши 1, 2 или 3."})
    
    elif session["state"] == "budget":
        # Используем GigaChat для анализа выбора бюджета
        sim.reset()
        if "1" in user_message or "накопления" in user_message.lower():
            sim.current_state.cash = 500000
            response = "Ты выбрал накопления — 500 000 руб. 💪 Оптимальный формат: Кофе с собой (To Go). Согласен?"
        elif "2" in user_message or "инвестор" in user_message.lower():
            sim.current_state.cash = 1500000
            response = "Ты выбрал инвестора — 1 500 000 руб. Я стану твоим партнёром. 🤝 Можешь открыть мини-кофейню."
        elif "3" in user_message or "кредит" in user_message.lower():
            sim.current_state.cash = 3000000
            response = "Ты взял кредит — 3 000 000 руб. ⚠️ Помни о платежах 80 000 руб./мес."
        else:
            response = "Пожалуйста, выбери 1, 2 или 3."
        
        return JSONResponse({"response": response})
    
    else:
        # Общий ответ — используем GigaChat
        state = sim.state()
        phase = sim.get_current_phase()
        actions = sim.get_available_actions()
        advice = get_mentor_advice(state.model_dump(), phase['name'], actions)
        return JSONResponse({"response": advice})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
