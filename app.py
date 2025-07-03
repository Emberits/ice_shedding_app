import streamlit as st
import pandas as pd
import numpy as np
import joblib
import folium
import streamlit_folium as st_folium  # Обновленный импорт
import requests

# Загрузка модели
@st.cache_resource
def load_model():
    return joblib.load("model.pkl")

model = load_model()

# Функция получения метеоданных
def get_weather_data(city, api_key):
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        data = response.json()
        
        temperature = data["main"]["temp"] - 273.15  # Кельвины → °C
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        cloudiness = data.get("clouds", {}).get("all", 0)
        precipitation = data.get("rain", {}).get("1h", 0)
        
        return {
            "temperature": round(temperature, 2),
            "humidity": humidity,
            "wind_speed": wind_speed,
            "precipitation": precipitation,
            "cloudiness": cloudiness
        }
    except Exception as e:
        st.error(f"⚠️ Не удалось получить данные: {e}")
        return None

# Функция оценки толщины льда
def estimate_ice_thickness(temp, humidity, wind_speed, cloudiness):
    es = 610.78 * np.exp((21.87 * temp) / (temp + 265.5))  # Давление пара над льдом
    ea = 610.78 * np.exp((21.87 * (temp + 2)) / (temp + 265.5)) * humidity / 100  # Давление пара в воздухе
    cp = 1005  # Удельная теплоёмкость воздуха
    pa = 101325  # Атмосферное давление
    h = 0.024 * 10  # Упрощённый коэффициент теплообмена
    I = h * (es - ea) * 0.62 / (cp * pa)  # Скорость образования льда
    ice_thickness = max(I * 3600, 0)  # За 1 час
    return round(ice_thickness, 2)

# Функция расчёта подскока провода
def compute_wire_bounce(ice_thickness, wire_diameter, span_length):
    bounce = 0.02 * ice_thickness * wire_diameter * (span_length / 100)
    bounce -= wind_speed * 0.05  # Демпфирование
    return max(round(bounce, 2), 0)

# Настройки страницы
st.set_page_config(page_title="Прогноз подскока провода", layout="centered")
st.title("🔮 Прогноз подскока провода при залповом сбросе льда")

# Поля ввода
city = st.text_input("🏙️ Город", value="Moscow")
api_key = st.text_input("🔑 OpenWeatherMap API Key", type="password")
wire_diameter = st.number_input("📏 Диаметр провода (мм)", value=12.7, step=0.1)
span_length = st.number_input("📐 Длина пролёта (м)", value=300, step=1)

if st.button("🔄 Получить метеоданные"):
    if not api_key:
        st.error("⚠️ Введите API-ключ")
    else:
        weather = get_weather_data(city, api_key)
        if weather:
            # Сохранение данных в сессию
            st.session_state.weather = weather
            st.success("✅ Данные получены")
            st.json(weather)

if "weather" in st.session_state:
    weather = st.session_state.weather
    temperature = weather["temperature"]
    wind_speed = weather["wind_speed"]
    humidity = weather["humidity"]
    precipitation = weather["precipitation"]
    cloudiness = weather["cloudiness"]
    
    # Расчёт толщины льда
    ice_thickness = estimate_ice_thickness(temperature, humidity, wind_speed, cloudiness)
    progress_value = min(max(int(ice_thickness * 5), 0), 100)
    st.success(f"✅ Оценённая толщина льда: {ice_thickness} мм")
    st.progress(progress_value)
    
    # Подготовка данных для ML
    input_data = pd.DataFrame({
        "temperature": [temperature],
        "wind_speed": [wind_speed],
        "humidity": [humidity],
        "ice_thickness": [ice_thickness],
        "precipitation": [precipitation],
        "cloudiness": [cloudiness],
        "wire_diameter": [wire_diameter],
        "span_length": [span_length]
    })
    
    # Прогноз модели ML
    try:
        ml_prob = model.predict_proba(input_data)[0][1]
        ml_risk = "Высокий" if ml_prob > 0.7 else "Средний" if ml_prob > 0.4 else "Низкий"
    except Exception:
        ml_prob = 0.0
        ml_risk = "Неизвестно"
    
    # Расчёт подскока провода
    bounce = compute_wire_bounce(ice_thickness, wire_diameter, span_length)
    bounce_risk = "Высокий" if bounce > 1.0 else "Средний" if bounce > 0.5 else "Низкий"
    
    # Комбинированный риск
    combined_risk = "Высокий" if ml_risk == "Высокий" or bounce_risk == "Высокий" else "Средний" if ml_risk == "Средний" or bounce_risk == "Средний" else "Низкий"
    
    # Визуализация
    st.info(f"🔄 Вероятность сброса: {ml_prob * 100:.0f}%")
    st.warning(f"⚠️ Риск сброса: {ml_risk}")
    st.success(f"📉 Амплитуда подскока: {bounce} м")
    st.error(f"⚠️ Риск короткого замыкания: {bounce_risk}")
    st.success(f"📊 Комбинированный риск: {combined_risk}")

# Визуализация карты рисков
st.markdown("### 🌍 Уровень риска по участкам ЛЭП")
try:
    segments = pd.read_csv("segments.csv")
    m = folium.Map(location=[55.75, 37.62], zoom_start=5)

    for _, row in segments.iterrows():
        name = row['name']
        lat = row['lat']
        lon = row['lon']
        risk = row['risk']

        color = 'red' if risk == 'Высокий' else 'orange' if risk == 'Средний' else 'green'
        folium.Marker([lat, lon], popup=name, icon=folium.Icon(color=color)).add_to(m)

    st_folium.folium_static(m)  # Использование st_folium
except Exception as e:
    st.error("⚠️ Ошибка загрузки данных о участках ЛЭП. Проверьте файл `segments.csv`.")
