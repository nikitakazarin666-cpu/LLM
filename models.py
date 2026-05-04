"""Финансовая модель для симулятора бизнеса."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class BusinessState(BaseModel):
    """Текущее состояние бизнеса."""
    # Финансы
    cash: float = Field(default=500000.0, description="Остаток денежных средств")
    monthly_rent: float = Field(default=0.0, description="Ежемесячная аренда")
    monthly_salary: float = Field(default=0.0, description="ФОТ в месяц")
    monthly_utilities: float = Field(default=0.0, description="Коммунальные платежи")
    
    # Активы
    equipment_condition: float = Field(default=1.0, ge=0.0, le=1.0, description="Состояние оборудования")
    interior_quality: float = Field(default=0.0, ge=0.0, le=1.0, description="Качество ремонта")
    inventory: float = Field(default=0.0, description="Запасы сырья")
    
    # Маркетинг и трафик
    traffic: int = Field(default=0, ge=0, description="Проходимость (чел/день)")
    brand_awareness: float = Field(default=0.0, ge=0.0, le=100.0, description="Узнаваемость бренда")
    loyalty: float = Field(default=0.0, ge=0.0, le=100.0, description="Лояльность клиентов")
    
    # Персонал
    staff_count: int = Field(default=0, ge=0, description="Количество сотрудников")
    staff_morale: float = Field(default=0.5, ge=0.0, le=1.0, description="Мораль персонала")
    staff_skill: float = Field(default=0.5, ge=0.0, le=1.0, description="Квалификация персонала")
    
    # Операционные показатели
    daily_customers: int = Field(default=0, ge=0, description="Покупателей в день")
    avg_check: float = Field(default=350.0, description="Средний чек")
    monthly_revenue: float = Field(default=0.0, description="Месячная выручка")
    monthly_profit: float = Field(default=0.0, description="Чистая прибыль")
    month: int = Field(default=0, ge=0, description="Текущий месяц")
    
    # Статус
    is_open: bool = Field(default=False, description="Открыта ли кофейня")
    current_phase: str = Field(default="rent", description="Текущая фаза симуляции")
    phase_step: int = Field(default=0, ge=0, description="Шаг внутри фазы")

class StepRequest(BaseModel):
    action: str

class ResetRequest(BaseModel):
    seed: Optional[int] = None

class StepResult(BaseModel):
    state: dict
    reward: float
    done: bool
    done_reason: Optional[str] = None
    info: dict = Field(default_factory=dict)
