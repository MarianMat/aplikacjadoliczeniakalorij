import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Baza indeksu glikemicznego
index_glikemiczny = {
    "soczewica": 32,
    "fasola": 27,
    "ciecierzyca": 28,
    "jabłko": 38,
    "pomarańcza": 40,
    "mleko": 30,
    "jogurt naturalny": 36,
    "czekolada gorzka": 40,
    "marchew": 35,
    "makaron pełnoziarnisty": 42,
    "ryż basmati": 50,
    "płatki owsiane": 55,
    "orzechy włoskie": 15,
    "migdały": 15,
    "truskawki": 41,
    "winogrona": 45,
    "gruszka": 38,
    "morele": 34,
    "śliwki": 29,
    "mleko sojowe": 34,
    "jogurt grecki": 11,
    "banan": 60,
    "kasza gryczana": 57,
    "miód": 58,
    "ananas": 59,
    "płatki kukurydziane": 65,
    "kasza jęczmienna": 66,
    "quinoa": 56,
    "mąka żytnia": 65,
    "lody": 61,
    "chleb żytni": 58,
    "ziemniaki": 78,
    "chleb pszenny": 75,
    "ryż biały": 72,
    "bagietka": 95,
    "arbuz": 75,
    "dynia": 75,
    "makaron biały": 70,
    "frytki": 85,
    "napoje słodzone": 90,
    "popcorn": 72,
    "mąka pszenna": 85,
    "ciastka": 77,
    "płatki słodzone": 80,
    "cukier": 100
}

def ocen_posilek(calories, protein, fat, carbs):
    score = 0
    if calories < 400: score += 2
    if protein > 15: score += 3
    if fat < 15: score += 1
    if carbs < 40: score += 2

    if score >= 6:
        return "✅ Zdrowy posiłek"
    elif score >= 3:
        return "⚠️ Umiarkowany"
    else:
        return "❌ Uważaj na ten posiłek"

def ocen_ig(nazwa_produktu):
    for nazwa, ig in index_glikemiczny.items():
        if nazwa in nazwa_produktu.lower():
            if ig <= 50:
                return f"✅ Niski IG ({ig}) – zalecany"
            elif ig <= 70:
                return f"⚠️ Średni IG ({ig}) – z umiarem"
            else:
                return f"❌ Wysoki IG ({ig}) – niewskazany"
    return "ℹ️ Brak danych o IG"

def add_meal(meal, calories, protein, fat, carbs, meal_type):
    data = {
        "date": datetime.now().date(),
        "time": datetime.now().strftime("%H:%M"),
        "meal": meal,
        "type": meal_type,
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs
    }
    df = pd.DataFrame([data])
    if os.path.exists("meals.csv"):
        df.to_csv("meals.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("meals.csv", mode="w", header=True, index=False)

st.set_page_config(page_title="Licznik kalorii", layout="centered")
st.title("🍽️ Licznik kalorii i ocena posiłków")

st.header("➕ Dodaj posiłek")
with st.form("meal_form"):
    meal = st.text_input("Nazwa posiłku lub produktu")
    meal_type = st.selectbox("Rodzaj posiłku", ["Śniadanie", "Obiad", "Kolacja", "Przekąska"])
    calories = st.number_input("Kalorie", 0, 2000)
    protein = st.number_input("Białko (g)", 0.0, 100.0)
    fat = st.number_input("Tłuszcz (g)", 0.0, 100.0)
    carbs = st.number_input("Węglowodany (g)", 0.0, 200.0)
    submitted = st.form_submit_button("Dodaj posiłek")

if submitted and meal:
    add_meal(meal, calories, protein, fat, carbs, meal_type)
    st.success(f"✅ Dodano: {meal} ({calories} kcal)")
    st.info(f"Ocena posiłku: {ocen_posilek(calories, protein, fat, carbs)}")
    st.info(f"Indeks glikemiczny: {ocen_ig(meal)}")
    st.rerun()

st.header("📅 Historia posiłków")
if os.path.exists("meals.csv"):
    df = pd.read_csv("meals.csv")
    df["date"] = pd.to_datetime(df["date"])
    today = datetime.now().date()
    today_meals = df[df["date"].dt.date == today]
    st.subheader(f"Dzisiejsze posiłki – {today.strftime('%Y-%m-%d')}")
    st.dataframe(today_meals, use_container_width=True)
    st.markdown(f"**Dzienne podsumowanie:**")
    st.write(f"🔥 Kalorie: {today_meals['calories'].sum()} kcal")
    st.write(f"💪 Białko: {today_meals['protein'].sum()} g")
    st.write(f"🥑 Tłuszcz: {today_meals['fat'].sum()} g")
    st.write(f"🍞 Węglowodany: {today_meals['carbs'].sum()} g")
else:
    st.info("Brak danych – dodaj pierwszy posiłek!")

with st.expander("📋 Lista produktów i ich indeks glikemiczny"):
    df_ig = pd.DataFrame([
        {"Produkt": nazwa, "IG": ig} for nazwa, ig in index_glikemiczny.items()
    ])
    st.table(df_ig.sort_values("IG"))
