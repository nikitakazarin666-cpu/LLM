"""Универсальный движок симулятора бизнеса на основе JSON-сценария."""

import json
import random
from typing import Dict, Optional
from models import BusinessState, StepResult

class BusinessSimulator:
    def __init__(self, scenario_file: str = "scenario_coffee_pro.json", seed: Optional[int] = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        
        # Загружаем сценарий из JSON
        with open(scenario_file, 'r', encoding='utf-8') as f:
            self.scenario = json.load(f)
        
        self.phases = self.scenario["phases"]
        self.phase_order = list(self.phases.keys())
        
        self.current_state = BusinessState()
        self.current_phase_idx = 0
        self.used_actions = set()
        
    def reset(self, seed: Optional[int] = None) -> BusinessState:
        if seed is not None:
            self.seed = seed
            self.rng = random.Random(self.seed)
        
        self.current_state = BusinessState()
        
        # Применяем начальный бюджет из сценария
        if "initial_cash" in self.scenario:
            self.current_state.cash = self.scenario["initial_cash"]
        elif "budget" in self.scenario:
            self.current_state.cash = self.scenario["budget"]
        
        self.current_phase_idx = 0
        self.used_actions = set()
        return self.current_state
    
    def state(self) -> BusinessState:
        return self.current_state
    
    def get_current_phase(self) -> dict:
        phase_name = self.phase_order[self.current_phase_idx]
        return self.phases[phase_name]
    
    def get_available_actions(self) -> list:
        phase = self.get_current_phase()
        return [step for step in phase["steps"] if step["id"] not in self.used_actions]
    
    def step(self, action_id: str) -> dict:
        phase = self.get_current_phase()
        state = self.current_state
        
        # Находим выбранное действие
        action = None
        for step in phase["steps"]:
            if step["id"] == action_id:
                action = step
                break
        
        if action is None:
            return {"error": f"Действие '{action_id}' недоступно в фазе '{phase['name']}'"}
        
        if action_id in self.used_actions:
            return {"error": f"Действие '{action_id}' уже выбрано"}
        
        self.used_actions.add(action_id)
        
        # Применяем финансовые затраты
        for cost_field, cost_value in action.get("costs", {}).items():
            if hasattr(state, cost_field):
                current_value = getattr(state, cost_field)
                if cost_field == "cash":
                    setattr(state, cost_field, current_value + cost_value)
                else:
                    setattr(state, cost_field, cost_value)
        
        # Применяем эффекты
        for effect_field, effect_value in action.get("effects", {}).items():
            if hasattr(state, effect_field):
                if effect_field.endswith("_bonus"):
                    continue
                current = getattr(state, effect_field)
                if isinstance(current, (int, float)):
                    setattr(state, effect_field, current + effect_value)
                elif isinstance(current, list):
                    current.append(effect_value)
                else:
                    setattr(state, effect_field, effect_value)
        
        # Сохраняем эффекты для последующего расчёта
        if not hasattr(state, '_effects_cache'):
            state._effects_cache = {}
        state._effects_cache.update(action.get("effects", {}))
        
        # Применяем риски
        for risk_name, risk_prob in action.get("risks", {}).items():
            if self.rng.random() < risk_prob:
                self._apply_risk(state, risk_name, action)
        
        # Переход к следующей фазе
        self.current_phase_idx += 1
        if self.current_phase_idx >= len(self.phase_order):
            # Запускаем операционную деятельность
            state.is_open = True
            state.current_phase = "completed"
            self._calculate_operations(state)
        else:
            state.current_phase = self.phase_order[self.current_phase_idx]
        
        state.month += 1
        
        # Проверка на банкротство
        done = state.cash <= 0
        done_reason = "bankrupt" if done else None
        
        # Проверка на успех
        if state.is_open and hasattr(state, 'monthly_profit') and state.monthly_profit > 50000 and state.loyalty > 30:
            done = True
            done_reason = "success"
        
        return StepResult(
            state=state.model_dump(),
            reward=state.cash,
            done=done,
            done_reason=done_reason,
            info={
                "action": action_id,
                "phase": phase["name"],
                "description": action.get("description", ""),
                "effects_applied": action.get("effects", {}),
                "risks_triggered": getattr(state, '_last_risk', None)
            }
        ).model_dump()
    
    def _apply_risk(self, state: BusinessState, risk_name: str, action: dict):
        """Обработка рисков."""
        if risk_name == "breakdown_chance":
            state.equipment_condition = max(0.3, state.equipment_condition - 0.3)
            state.cash -= 20000
            state._last_risk = "Поломка оборудования! Срочный ремонт -20 000 ₽"
        elif risk_name == "no_show_risk":
            state.staff_morale = max(0.3, state.staff_morale - 0.2)
            state.daily_customers = max(0, state.daily_customers - 5)
            state._last_risk = "Сотрудник не вышел! Потеря клиентов."
        elif risk_name == "invisible":
            state.traffic = max(5, state.traffic - 10)
            state._last_risk = "Вас никто не видит. Трафик еще ниже."
        elif risk_name == "low_season":
            state.monthly_revenue *= 0.7
            state._last_risk = "Сезонное падение выручки на 30%."
        elif risk_name == "competition":
            state.daily_customers = max(0, state.daily_customers - 10)
            state._last_risk = "Рядом открылся конкурент! Отток клиентов."
        elif risk_name == "critical_breakdown":
            state.equipment_condition = 0.1
            state.cash -= 50000
            state._last_risk = "Критическая поломка кофемашины! Ремонт за 50 000 ₽ или покупка новой."
        elif risk_name == "partner_conflict":
            state.cash -= 100000
            state.staff_morale = max(0.2, state.staff_morale - 0.4)
            state._last_risk = "Конфликт с партнёром! Потеря 100 000 ₽."
        elif risk_name == "debt_trap":
            state.monthly_debt = getattr(state, 'monthly_debt', 0) + 30000
            state._last_risk = "Процентная ставка по кредиту выросла! +30 000 ₽ к ежемесячному платежу."
        elif risk_name == "sudden_eviction":
            state.cash -= 150000
            state.current_phase = "location"
            state._last_risk = "Вас выселяют из субаренды! Срочный переезд и потеря 150 000 ₽."
        else:
            state._last_risk = f"Сработал риск: {risk_name}"
    
    def _calculate_operations(self, state: BusinessState):
        """Расчёт месячной операционной деятельности."""
        effects = getattr(state, '_effects_cache', {})
        avg_check_bonus = sum(v for k, v in effects.items() if k.endswith('_bonus'))
        traffic_bonus = effects.get('traffic_bonus', 0)
        revenue_base = effects.get('monthly_revenue_base', 150000)
        
        # Базовый трафик
        traffic = effects.get('traffic', 30)
        state.daily_customers = int(traffic * 0.3 + traffic_bonus)
        
        # Выручка
        state.avg_check = 350 + avg_check_bonus
        state.monthly_revenue = state.daily_customers * state.avg_check * 30
        
        # Расходы
        total_costs = (getattr(state, 'monthly_rent', 0) + 
                      getattr(state, 'monthly_salary', 0) + 
                      getattr(state, 'monthly_utilities', 0) +
                      getattr(state, 'monthly_inventory', 0) +
                      getattr(state, 'monthly_debt', 0) +
                      getattr(state, 'monthly_equipment_rent', 0) +
                      getattr(state, 'monthly_equipment_lease', 0) +
                      getattr(state, 'monthly_legal', 0) +
                      getattr(state, 'monthly_ops_cost', 0) +
                      getattr(state, 'monthly_salary_extra', 0) +
                      getattr(state, 'monthly_royalty', 0) +
                      state.inventory * 100)
        
        state.monthly_profit = state.monthly_revenue - total_costs
        state.cash += state.monthly_profit
        
        # Износ оборудования
        if state.equipment_condition < 0.7:
            state.equipment_condition = max(0.3, state.equipment_condition - 0.05)
            if self.rng.random() < (1 - state.equipment_condition):
                repair_cost = 15000
                state.cash -= repair_cost
                state.equipment_condition = 0.6
