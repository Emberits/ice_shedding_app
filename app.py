import streamlit as st
import pandas as pd

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

# Кнопка прогноза
if st.button("📊 Прогноз"):
    # Заглушка для вывода
    st.success("✅ Риск: Средний")
    st.info("ℹ️ Подробный анализ будет добавлен на следующих этапах.")
else:
    st.info("ℹ️ Введите параметры и нажмите **Прогноз**.")

# Подвал
st.markdown("---")
st.markdown("© 2025 | Энергетическая безопасность")
