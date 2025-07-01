import streamlit as st
import pandas as pd
import numpy as np
import joblib
import folium
from streamlit_folium import folium_static

# Загрузка модели
@st.cache_resource
def load_model():
    return joblib.load("model.pkl")

model = load_model()

# Загрузка данных об участках ЛЭП
@st.cache_data
def load_segments():
    return pd.read_csv("segments.csv")

segments = load_segments()

# Настройки страницы
st.set_page_config(page_title="Карта рисков ЛЭП", layout="wide")

# Заголовок и описание
st.title("🗺️ Карта рисков ЛЭП")
st.markdown("Карта отображает участки воздушных линий электропередачи с уровнем риска залпового сброса льда.")

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

# Физическая модель подскока провода
def compute_wire_bounce(ice_thickness, wire_diameter, span_length):
    bounce = 0.02 * ice_thickness * wire_diameter * (span_length / 100)
    return round(bounce, 2)

# Кнопка прогноза
if st.button("📊 Прогноз"):
    # Расчеты
    ice_thickness = estimate_ice_thickness(temperature, humidity, wind_speed)
    ice_thickness = max(ice_thickness, 0)  # Защита от отрицательных значений
    
    # Подготовка данных для модели ML
    input_data = pd.DataFrame({
        "temperature": [temperature],
        "wind_speed": [wind_speed],
        "humidity": [humidity],
        "ice_thickness": [ice_thickness],
        "temp_change_last_6h": [temp_change_last_6h],
        "precipitation": [precipitation],
        "wire_diameter": [wire_diameter],
        "span_length": [span_length]
    })
    
    # Прогноз модели ML
    ml_prob = model.predict_proba(input_data)[0][1]  # Вероятность сброса
    ml_risk = "Высокий" if ml_prob > 0.7 else "Средний" if ml_prob > 0.4 else "Низкий"
    
    # Расчёт амплитуды подскока
    bounce = compute_wire_bounce(ice_thickness, wire_diameter, span_length)
    bounce_risk = "Высокий" if bounce > 1.0 else "Средний" if bounce > 0.5 else "Низкий"
    
    # Комбинированный риск
    combined_risk = "Высокий" if ml_risk == "Высокий" or bounce_risk == "Высокий" else "Средний" if ml_risk == "Средний" or bounce_risk == "Средний" else "Низкий"
    
    # Визуализация
    st.success(f"✅ Оценённая толщина льда: {ice_thickness} мм")
    st.info(f"🔄 Вероятность сброса: {ml_prob * 100:.0f}%")
    st.warning(f"⚠️ Риск сброса: {ml_risk}")
    st.success(f"📉 Амплитуда подскока: {bounce} м")
    st.error(f"⚠️ Риск короткого замыкания: {bounce_risk}")
    st.success(f"📊 Комбинированный риск: {combined_risk}")

# Визуализация карты рисков
st.markdown("### 🌍 Уровень риска по участкам ЛЭП")
try:
    m = folium.Map(location=[55.75, 37.62], zoom_start=5)

    for _, row in segments.iterrows():
        name = row['name']
        lat = row['lat']
        lon = row['lon']
        risk = row['risk']

        # Цвет маркера в зависимости от риска
        if risk == 'Высокий':
            color = 'red'
        elif risk == 'Средний':
            color = 'orange'
        else:
            color = 'green'

        folium.Marker(
            [lat, lon],
            popup=name,
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)

    folium_static(m)
except Exception as e:
    st.error("⚠️ Ошибка загрузки данных о участках ЛЭП. Проверьте файл `segments.csv`.")
