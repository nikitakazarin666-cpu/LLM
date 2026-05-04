"""Веб-интерфейс для симулятора кофейни на Gradio."""

import gradio as gr
from env import BusinessSimulator
from mentor import get_mentor_advice

# Создаём симулятор
sim = BusinessSimulator(scenario_file="scenario_coffee_shop.json", seed=42)

def start_game():
    """Начать новую игру."""
    state = sim.reset()
    phase = sim.get_current_phase()
    actions = sim.get_available_actions()
    
    status_text = f"💰 Бюджет: {state.cash:,.0f} ₽\n"
    status_text += f"📅 Месяц: {state.month}\n"
    status_text += f"📊 Фаза: {phase['name']}\n\n"
    status_text += f"📝 {phase['description']}"
    
    # Создаём кнопки для действий
    buttons = []
    labels = []
    for action in actions:
        labels.append(f"{action['label']} — {action['description'][:80]}...")
    
    return status_text, gr.update(choices=labels, value=None)

def make_choice(choice_text):
    """Обработка выбора пользователя."""
    if not choice_text:
        return "Пожалуйста, выберите действие.", gr.update(), ""

def ask_mentor():
    """Получает совет от ИИ-Ментора на основе текущего состояния."""
    state = sim.state()
    phase = sim.get_current_phase()
    actions = sim.get_available_actions()

    if not actions:
        return "Ментор: Все важные решения в этой фазе уже приняты. Двигаемся дальше!"

    # Вызываем наш модуль mentor.py
    advice = get_mentor_advice(
        state.model_dump(),
        phase['name'],
        actions
    )

    return f"🧙‍♂️ **Ментор:** {advice}"
    
    phase = sim.get_current_phase()
    actions = sim.get_available_actions()
    
    # Находим ID действия по тексту
    action_id = None
    for action in actions:
        if action['label'] in choice_text:
            action_id = action['id']
            break
    
    if not action_id:
        return "Ошибка: действие не найдено.", gr.update(), ""
    
    # Выполняем шаг
    result = sim.step(action_id)
    
    if "error" in result:
        return f"❌ {result['error']}", gr.update(), ""
    
    state = sim.state()
    
    # Формируем отчёт
    report = f"### Вы выбрали: {choice_text}\n\n"
    report += f"**Эффект:** {result['info'].get('description', '')}\n\n"
    
    # Риски
    if result['info'].get('risks_triggered'):
        report += f"⚠️ **{result['info']['risks_triggered']}**\n\n"
    
    # Состояние
    report += f"💰 **Остаток:** {state.cash:,.0f} ₽\n"
    report += f"📅 **Месяц:** {state.month}\n"
    
    # Проверка на завершение
    if result['done']:
        if result.get('done_reason') == 'bankrupt':
            report += "\n## 💀 ВЫ БАНКРОТ!\nУ вас закончились деньги. Попробуйте ещё раз с другими решениями."
        elif result.get('done_reason') == 'success':
            report += "\n## 🎉 ПОЗДРАВЛЯЕМ!\nВаша кофейня успешна и приносит прибыль!"
        
        return report, gr.update(choices=[], value=None), ""
    
    # Следующая фаза
    if state.is_open:
        # Операционная деятельность
        report += f"\n### ☕ Кофейня открыта!\n"
        report += f"👥 Посетителей в день: **{state.daily_customers}**\n"
        report += f"💵 Средний чек: **{state.avg_check:,.0f} ₽**\n"
        report += f"📈 Выручка за месяц: **{state.monthly_revenue:,.0f} ₽**\n"
        report += f"📉 Расходы за месяц: **{state.monthly_rent + state.monthly_salary + state.monthly_utilities:,.0f} ₽**\n"
        profit = state.monthly_profit
        if profit > 0:
            report += f"✅ Чистая прибыль: **{profit:,.0f} ₽**"
        else:
            report += f"🔴 Убыток: **{profit:,.0f} ₽**"
        
        return report, gr.update(choices=[], value=None), ""
    
    # Следующая фаза
    next_phase = sim.get_current_phase()
    next_actions = sim.get_available_actions()
    
    new_labels = []
    for action in next_actions:
        new_labels.append(f"{action['label']} — {action['description'][:80]}...")
    
    phase_desc = f"### 📋 {next_phase['name']}\n{next_phase['description']}"
    
    return report + "\n" + phase_desc, gr.update(choices=new_labels, value=None), ""

# Создаём интерфейс
with gr.Blocks(title="Симулятор кофейни", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ☕ Симулятор открытия кофейни")
    gr.Markdown("Пройдите путь от выбора помещения до прибыльного бизнеса. Бюджет: **5 000 000 ₽**")
    
    with gr.Row():
        with gr.Column(scale=2):
            output_text = gr.Markdown("Нажмите **Начать игру**, чтобы стартовать.", label="Статус")
        
        with gr.Column(scale=1):
            phase_info = gr.Markdown("")
    
    action_radio = gr.Radio(
        choices=[],
        label="Выберите действие",
        interactive=True
    )
    
    submit_btn = gr.Button("✅ Принять решение", variant="primary", size="lg")
    start_btn = gr.Button("🔄 Начать игру", variant="secondary")
    
    submit_btn.click(
        fn=make_choice,
        inputs=[action_radio],
        outputs=[output_text, action_radio, phase_info]
    )
    
    start_btn.click(
        fn=start_game,
        inputs=[],
        outputs=[output_text, action_radio]
    )

    # НОВЫЙ БЛОК С МЕНТОРОМ — ВОТ ОН, ВНУТРИ with gr.Blocks:
    with gr.Row():
        mentor_btn = gr.Button("🧙‍♂️ Спросить совета у Ментора", variant="secondary", size="lg")
        mentor_output = gr.Markdown("")
    
    mentor_btn.click(
        fn=ask_mentor,
        inputs=[],
        outputs=[mentor_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
