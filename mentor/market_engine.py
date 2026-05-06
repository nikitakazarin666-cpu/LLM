"""
Рыночный Движок (Market Engine).
Генерирует контекстные события на основе действий игрока.
"""

import os
import uuid
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH_KEY = os.environ.get('GIGACHAT_AUTH_KEY', '').strip()
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

SYSTEM_PROMPT = """Ты — Рыночный Движок бизнес-симулятора кофейни. Твоя задача — генерировать события на основе действий игрока.

ПРАВИЛА:
- Если игрок экономит на качестве (дешёвое зерно, старое оборудование) — создавай негативные события (плохие отзывы, поломки, спад трафика).
- Если игрок инвестирует в команду и продукт — создавай позитивные события (хорошие отзывы, рост лояльности, вирусный пост).
- Связывай события с прошлыми действиями игрока. Не используй случайные события.
- Описывай событие живо, с деталями и конкретными последствиями.

ФОРМАТ ОТВЕТА:
{
  "event_text": "Краткое описание события (1-2 предложения)",
  "consequence": "Влияние на бизнес (цифры)",
  "mood": "positive" | "negative" | "neutral"
}
"""

def _get_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {AUTH_KEY}'
    }
    try:
        r = requests.post(AUTH_URL, headers=headers, data='scope=GIGACHAT_API_PERS', timeout=10, verify=False)
        if r.status_code == 200:
            return r.json().get('access_token')
    except:
        pass
    return None

def generate_market_event(state: dict, action_history: list) -> dict:
    """
    Генерирует контекстное событие на основе состояния и истории действий.
    Возвращает dict с ключами: event_text, consequence, mood.
    """
    token = _get_token()
    if not token:
        return {
            "event_text": "Сегодня обычный день. Ничего необычного не произошло.",
            "consequence": "Без изменений",
            "mood": "neutral"
        }

    history_text = "\n".join([f"- {a}" for a in action_history[-5:]])
    
    prompt = f"""Состояние кофейни:
- Бюджет: {state.get('cash', 0):,.0f} руб.
- Трафик: {state.get('traffic', 0)} чел/день
- Репутация: {state.get('reputation', 5.0)} / 5.0
- Качество оборудования: {state.get('equipment_condition', 1.0)} / 1.0
- Лояльность: {state.get('loyalty', 50)} / 100

Последние действия игрока:
{history_text if history_text else "Нет истории (первый ход)"}

Сгенерируй событие в формате JSON."""

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.8
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30, verify=False)
        if r.status_code == 200:
            import json
            content = r.json()['choices'][0]['message']['content']
            return json.loads(content)
    except:
        pass

    return {
        "event_text": "Сегодня обычный день.",
        "consequence": "Без изменений",
        "mood": "neutral"
    }
