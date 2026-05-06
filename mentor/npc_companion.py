"""
NPC-Собеседник (NPC Companion).
Отыгрывает персонажей в диалогах с игроком.
"""

import os
import uuid
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH_KEY = os.environ.get('GIGACHAT_AUTH_KEY', '').strip()
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

NPC_TYPES = {
    "landlord": {
        "system_prompt": "Ты — арендодатель коммерческой недвижимости в Москве. У тебя есть помещение 25 м² в спальном районе. Твоя цель — сдать его за 80 000 руб./мес., но ты готов торговаться до 65 000. Ты деловой, но справедливый.",
    },
    "barista_candidate": {
        "system_prompt": "Ты — кандидат на должность бариста. Тебе 22 года, опыт работы 1 год в сетевой кофейне. Ты хочешь зарплату 45 000 руб./мес. Ты энергичный, но немного неопытный. Отвечай на вопросы честно, но старайся показать себя с лучшей стороны.",
    },
    "angry_customer": {
        "system_prompt": "Ты — недовольный клиент. Ты заказал капучино, но он был холодным и невкусным. Ты требуешь возврат денег и угрожаешь написать плохой отзыв. Ты эмоциональный, но отходчивый, если к тебе отнестись с уважением.",
    }
}

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

def start_npc_dialogue(npc_type: str, state: dict = None) -> str:
    """
    Начинает диалог с NPC.
    Возвращает первую реплику персонажа.
    """
    if npc_type not in NPC_TYPES:
        return "Персонаж не найден."
    
    token = _get_token()
    if not token:
        return "Персонаж временно недоступен (GigaChat offline)."
    
    system_prompt = NPC_TYPES[npc_type]["system_prompt"]
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Начни диалог. Представься и обозначь свою позицию."}
        ],
        "max_tokens": 150,
        "temperature": 0.8
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30, verify=False)
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content']
            return content.strip()
    except:
        pass
    
    return "Здравствуйте. Я вас слушаю."

def continue_npc_dialogue(npc_type: str, player_message: str, dialogue_history: list = None) -> str:
    """
    Продолжает диалог с NPC, оценивая ответ игрока.
    Возвращает реплику персонажа.
    """
    if npc_type not in NPC_TYPES:
        return "Персонаж не найден."
    
    token = _get_token()
    if not token:
        return "Персонаж временно недоступен."
    
    system_prompt = NPC_TYPES[npc_type]["system_prompt"]
    
    messages = [{"role": "system", "content": system_prompt}]
    if dialogue_history:
        messages.extend(dialogue_history)
    messages.append({"role": "user", "content": player_message})
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        "model": "GigaChat",
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.8
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=30, verify=False)
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content']
            return content.strip()
    except:
        pass
    
    return "Хорошо, я вас понял."
