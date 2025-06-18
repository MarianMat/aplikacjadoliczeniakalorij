import streamlit as st
from PIL import Image
import io
import requests
import pandas as pd
import matplotlib.pyplot as plt
import openai

# --- KONFIGURACJA API ---
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")  # w Streamlit Cloud wpisz swój klucz w sekcji Secrets
openai.api_key = OPENAI_API_KEY

st.set_page_config(page_title="Licznik kalorii AI", layout="centered")
st.title("🍽️ Licznik kalorii ze zdjęcia i dziennik posiłków")

# --- FUNKCJA ANALIZY ZDJĘCIA PRZEZ OPENAI ---
def analyze_image_openai(image_bytes):
    try:
        # Przykład prostego promptu do GPT (w rzeczywistości możesz użyć OpenAI Vision lub innej usługi)
        # W tym przykładzie symulujemy odpowiedź (bo OpenAI Vision jest beta)
        prompt = "Opisz ten posiłek na podstawie zdjęcia i podaj przybliżoną kaloryczność oraz makroskładniki w gramach."

        # Zamień zdjęcie na base64 lub bytes, ale tu zrobimy uproszczenie
        # W praktyce można wysłać zdjęcie do modelu obsługującego obraz

        # Tymczasowo zwracamy przykładową odpowiedź
        return {
            "food": "Kanapka z serem i warzywami",
            "calories": 350,
            "protein": 15,
            "fat": 12,
            "carbs": 40
        }
    except Exception as e:
        st.error(f"Błąd analizy obrazu: {e}")
        return None

# --- INICJALIZACJA DZIENNIKA W SESJI ---
if "meal_log" not in st.session_state:
    st.session_state.meal_log = []

# --- UPLOAD ZDJĘCIA ---
st.header("1. Zrób zdjęcie lub wybierz plik posiłku")
uploaded_file = st.file_uploader("Wgraj zdjęcie (jpg, png)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Załadowany posiłek", use_column_width=True)

    if st.button("Analizuj zdjęcie AI"):
        bytes_data = uploaded_file.read()
        result = analyze_image_openai(bytes_data)
        if result:
            st.success(f"Rozpoznano: {result['food']}")
            st.write(f"Kalorie: {result['calories']} kcal")
            st.write(f"Białko: {result['protein']} g")
            st.write(f"Tłuszcz: {result['fat']} g")
            st.write(f"Węglowodany: {result['carbs']} g")

            # Dodajemy do dziennika
            st.session_state.meal_log.append(result)
            st.success("Dodano posiłek do dziennika.")

# --- RĘCZNE DODAWANIE PRODUKTU ---
st.header("2. Dodaj posiłek ręcznie")
with st.form("manual_add_form"):
    food_name = st.text_input("Nazwa posiłku")
    calories = st.number_input("Kalorie (kcal)", min_value=0, step=1)
    protein = st.number_input("Białko (g)", min_value=0.0, step=0.1)
    fat = st.number_input("Tłuszcz (g)", min_value=0.0, step=0.1)
    carbs = st.number_input("Węglowodany (g)", min_value=0.0, step=0.1)
    submit = st.form_submit_button("Dodaj posiłek")

    if submit:
        new_meal = {
            "food": food_name,
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs
        }
        st.session_state.meal_log.append(new_meal)
        st.success("Dodano posiłek do dziennika.")

# --- WYŚWIETLANIE DZIENNIKA ---
st.header("3. Dziennik posiłków")
if st.session_state.meal_log:
    df = pd.DataFrame(st.session_state.meal_log)
    st.dataframe(df)

    # Sumy makroskładników
    sum_calories = df["calories"].sum()
    sum_protein = df["protein"].sum()
    sum_fat = df["fat"].sum()
    sum_carbs = df["carbs"].sum()

    st.write(f"**Sumarycznie:** {sum_calories} kcal, Białko: {sum_protein} g, Tłuszcz: {sum_fat} g, Węglowodany: {sum_carbs} g")

    # --- WYKRES ---
    st.subheader("Statystyki posiłków (kcal i makroskładniki)")

    fig, ax = plt.subplots()
    df_sum = pd.DataFrame({
        "Kalorie": [sum_calories],
        "Białko": [sum_protein],
        "Tłuszcz": [sum_fat],
        "Węglowodany": [sum_carbs]
    })
    df_sum.plot(kind="bar", ax=ax, rot=0)
    st.pyplot(fig)

else:
    st.info("Dodaj pierwszy posiłek poprzez zdjęcie lub ręcznie.")


