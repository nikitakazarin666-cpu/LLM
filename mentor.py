import os
import uuid
import requests
import urllib3

# Отключаем предупреждения о небезопасном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- НАСТРОЙКИ GIGACHAT ---
AUTH_KEY = os.environ.get('MDE5ZGI0YmItNDU0NC03ODM2LTk3NDctYWI4MGExNzhmNTllOjdlNGYwMTdkLWZiMWYtNGFiZC05M2IwLWE0ZDM4Mjk5YmI2MA==', '').strip()
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
SCOPE = "GIGACHAT_API_PERS"

# --- БАЗА ЗНАНИЙ ---
KNOWLEDGE_BASE_CONCEPT = """
Факты о кофейне в Москве:
- To Go (Кофе с собой): бюджет 250-500 тыс. руб., аренда 15-20 тыс./мес., чек 250-300 руб., прибыль 80-150 тыс./мес., окупаемость 4-8 месяцев, риск - ошибка с локацией.
- Классическая кофейня: бюджет 3-5 млн руб., аренда 80-180 тыс./мес., чек 350-450 руб., прибыль 200-450 тыс./мес., окупаемость 10-18 месяцев, риск - перекос в интерьер в ущерб маркетингу.
- Франшиза: бюджет от 3.8 млн руб., роялти 3-8% от выручки, риск - скрытые платежи и жёсткие стандарты.
"""

def _get_access_token() -> str | None:
    """Получает временный Access Token GigaChat."""
    if not AUTH_KEY:
        print("[MENTOR] GIGACHAT_AUTH_KEY не найден или пуст")
        return None

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {AUTH_KEY}'
    }

    try:
        response = requests.post(
            AUTH_URL,
            headers=headers,
            data=f'scope={SCOPE}',
            timeout=10,
            verify=False  # ← отключаем проверку SSL, как rejectUnauthorized: false
        )
        print(f"[MENTOR] Статус получения токена: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            print(f"[MENTOR] Токен получен, expires_at: {token_data.get('expires_at')}")
            return token_data['access_token']
        else:
            print(f"[MENTOR] Ошибка: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"[MENTOR] Исключение: {e}")
        return None

def get_mentor_advice(state: dict, phase_name: str, available_actions: list) -> str:
    """Даёт совет на основе GigaChat или офлайн-базы."""
    cash = state.get('cash', 0)

    actions_text = ""
    for action in available_actions:
        actions_text += f"- **{action['label']}**: {action['description']}\n"

    prompt = f"""
Ты — опытный и участливый бизнес-ментор. Ты помогаешь человеку, который впервые открывает свою кофейню в Москве. Твоя цель — дать совет, основанный на цифрах и логике.
Твоя база знаний:
{KNOWLEDGE_BASE_CONCEPT}
Сейчас мы на этапе: {phase_name}.
Состояние кофейни:
- Бюджет (остаток на счету): {cash:,.0f} руб.
- Месяц: {state.get('month', 0)}
Варианты действий, которые рассматривает твой подопечный:
{actions_text}
Дай ему совет, основываясь на цифрах и логике. Назови конкретную сумму из бюджета, сравни варианты, укажи на главный риск. Твой ответ должен быть тёплым, но честным, на русском языке, на 3-6 предложений. Обратись к игроку по имени — Алексей."""

    # Получаем токен
    token = _get_access_token()
    if not token:
        return f"❌ **Ментор:** Не удалось получить токен GigaChat. Проверьте ключ в Secret'ах. Мой офлайн-совет: при бюджете {cash:,.0f} руб. начать с To Go."

    # Запрос к GigaChat
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30,
            verify=False  # ← отключаем проверку SSL
        )
        print(f"[MENTOR] Статус ответа GigaChat: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            advice = data['choices'][0]['message']['content'].strip()
            return f"🧙‍♂️ **Ментор (GigaChat):** {advice}"
        else:
            print(f"[MENTOR] Ошибка GigaChat: {response.text}")
            return f"❌ **Ментор:** Ошибка API GigaChat ({response.status_code}). Мой офлайн-совет: начните с To Go."
    except Exception as e:
        print(f"[MENTOR] Исключение: {e}")
        return f"❌ **Ментор:** Сетевая ошибка. Мой офлайн-совет: при бюджете {cash:,.0f} руб. — начните с формата To Go."
