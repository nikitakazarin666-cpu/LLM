"""Центральный модуль ИИ-Ментора. Перенаправляет запросы к нужному движку."""

from mentor.market_engine import generate_market_event
from mentor.virtual_cfo import generate_cfo_report
from mentor.npc_companion import start_npc_dialogue, continue_npc_dialogue

def get_mentor_advice(state: dict, phase_name: str, available_actions: list = None) -> str:
    """Универсальная функция для получения совета (оставлена для обратной совместимости)."""
    return generate_cfo_report(state)
