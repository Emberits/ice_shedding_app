import streamlit as st
import pandas as pd
import numpy as np

# Настройки страницы
st.set_page_config(page_title="Прогноз подскока провода", layout="centered")

# Заголовок и описание
st.title("🔮 Прогноз подскока провода при залповом сбросе льда")
st.markdown("Введите параметры ниже и нажмите кнопку **Прогноз**, чтобы оценить риск.")

# Поля ввода
temperature = st.number_input("🌡️ Температура (°C)", value=-5.0, step=0.1)
wind_speed = st.number_input("🌬️ Скорость ветра (м/с)", value=10.0, step=0.1)
humidity = st.number_input("💧 Влажность (%)", value=85, step=1)
wire_diameter = st.number_input("📏 Диаметр провода (мм)", value=12.7, step=0.1)
span_length = st.number_input("📐 Длина пролёта (м)", value=300, step=1)
temp_change_last_6h = st.number_input("📈 Перепад температуры за 6 ч (°C)", value=2.0, step=0.1)
precipitation = st.number_input("🌧️ Осадки за 6 ч (мм)", value=0.5, step=0.1)

# Функция оценки толщины льда
def estimate_ice_thickness(temp, humidity, wind_speed, hours=24):
    k = 0.05  # Эмпирический коэффициент
    ice_thickness = k * wind_speed * humidity * (1 - abs(temp)/10) * (hours/24)
    return round(ice_thickness, 2)

# Функция оценки потенциала сброса
def shedding_potential(temp_change, precipitation, wind_speed):
    base = 0.5
    temp_factor = temp_change * 0.2
    precip_factor = precipitation * 0.15
    wind_factor = wind_speed * 0.1
    total = base + temp_factor + precip_factor + wind_factor
    return min(round(total, 2), 1.0)

# Кнопка прогноза
if st.button("📊 Прогноз"):
    # Расчеты
    ice_thickness = estimate_ice_thickness(temperature, humidity, wind_speed)
    shedding_prob = shedding_potential(temp_change_last_6h, precipitation, wind_speed)
    
    # Визуализация
    st.success(f"✅ Оценённая толщина льда: {ice_thickness} мм")
    
    # Безопасное значение для прогресс-бара
    progress_value = min(int(ice_thickness * 5), 100)
    st.progress(progress_value)
    
    st.info(f"🔄 Потенциал сброса: {shedding_prob * 100:.0f}%")
    if shedding_prob > 0.7:
        st.warning("⚠️ Высокий риск сброса!")
    elif shedding_prob > 0.4:
        st.warning("⚠️ Средний риск сброса.")
    else:
        st.success("✅ Низкий риск сброса.")
else:
    st.info("ℹ️ Введите параметры и нажмите **Прогноз**.")

# Подвал
st.markdown("---")
st.markdown("© 2025 | Энергетическая безопасность")
