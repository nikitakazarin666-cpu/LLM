"""
Виртуальный CFO (Virtual CFO).
Проводит еженедельный финансовый аудит и даёт стратегические советы.
"""

import os
import uuid
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH_KEY = os.environ.get('GIGACHAT_AUTH_KEY', '').strip()
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

SYSTEM_PROMPT = """Ты — Виртуальный CFO (финансовый директор) кофейни. Твоя задача — анализировать финансовые показатели и давать стратегические советы.

ПРАВИЛА:
- Анализируй доходы, расходы, денежный поток.
- Подсвечивай разницу между доходом и активом.
- Указывай на зависимость бизнеса от владельца.
- Давай конкретные советы по улучшению финансовых показателей.
- Говори на языке бизнеса, но доступно для начинающего предпринимателя.
- Используй эмодзи для наглядности.

ФОРМАТ ОТВЕТА: Свободный текст (3-5 предложений) с анализом и советом.
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

def generate_cfo_report(state: dict) -> str:
    """
    Генерирует еженедельный финансовый отчёт.
    Возвращает строку с анализом и советом.
    """
    token = _get_token()
    if not token:
        cash = state.get('cash', 0)
        profit = state.get('monthly_profit', 0)
        if profit > 0:
            return f"📊 Недельный отчёт: Касса: {cash:,.0f} ₽. Прибыль: {profit:,.0f} ₽. Всё стабильно, но без анализа GigaChat."
        else:
            return f"📊 Недельный отчёт: Касса: {cash:,.0f} ₽. Убыток: {profit:,.0f} ₽. Срочно пересмотри расходы!"

    prompt = f"""Состояние кофейни:
- Касса: {state.get('cash', 0):,.0f} руб.
- Месячная выручка: {state.get('monthly_revenue', 0):,.0f} руб.
- Чистая прибыль: {state.get('monthly_profit', 0):,.0f} руб.
- Аренда: {state.get('monthly_rent', 0):,.0f} руб./мес.
- Зарплаты: {state.get('monthly_salary', 0):,.0f} руб./мес.
- Трафик: {state.get('traffic', 0)} чел/день
- Средний чек: {state.get('avg_check', 350):,.0f} руб.
- Лояльность: {state.get('loyalty', 50)} / 100

Проведи финансовый аудит и дай совет."""

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
        "max_tokens": 300,
        "temperature": 0.7
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30, verify=False)
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content']
            return f"📊 **Еженедельный отчёт CFO:**\n\n{content.strip()}"
    except:
        pass

    cash = state.get('cash', 0)
    profit = state.get('monthly_profit', 0)
    return f"📊 Недельный отчёт: Касса: {cash:,.0f} ₽. Прибыль: {profit:,.0f} ₽. (GigaChat недоступен)"
