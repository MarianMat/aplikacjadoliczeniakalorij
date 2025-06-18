import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
import openai

# -------------------
# KONFIGURACJA API OpenAI
# -------------------
openai.api_key = st.secrets["OPENAI_API_KEY"]

DATA_FILE = "meals.csv"

# Baza indeksów glikemicznych (prosta przykładowa)
GI_DATABASE = {
    "biały chleb": "wysoki",
    "ryż biały": "wysoki",
    "banan": "średni",
    "jabłko": "niski",
    "płatki owsiane": "niski",
    "słodycze": "wysoki",
    "marchewka surowa": "niski",
    "ziemniaki": "wysoki",
    "soczewica": "niski",
    "makaron pełnoziarnisty": "średni",
    "arbuz": "wysoki",
    "jogurt naturalny": "niski",
    "miód": "wysoki"
}

# -------------------
# FUNKCJE
# -------------------

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Data", "Godzina", "Produkt", "Kalorie", "Bialko", "Tluszcz", "Weglowodany", "Gramatura"])

def save_data(entry):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

def display_data():
    df = load_data()
    st.subheader("📊 Historia posiłków")
    st.dataframe(df.sort_values(by=["Data", "Godzina"], ascending=False))

def check_gi_level(product_name):
    for name, level in GI_DATABASE.items():
        if name.lower() in product_name.lower():
            return level
    return None

@st.cache_data(show_spinner=False)
def get_product_info(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        if data["status"] == 1:
            p = data["product"]
            return {
                "name": p.get("product_name", "Nieznany produkt"),
                "kcal": p.get("nutriments", {}).get("energy-kcal_100g", 0),
                "protein": p.get("nutriments", {}).get("proteins_100g", 0),
                "fat": p.get("nutriments", {}).get("fat_100g", 0),
                "carbs": p.get("nutriments", {}).get("carbohydrates_100g", 0)
            }
    return None

def analyze_image_with_openai(image_bytes):
    """
    Wysyła zdjęcie do OpenAI GPT-4 Vision (model GPT-4 z możliwością analizy obrazów)
    i prosi o rozpoznanie składników oraz podanie kalorii i makroskładników.
    """

    messages = [
        {"role": "system", "content": "Jesteś pomocnym asystentem, który analizuje zdjęcia posiłków i podaje listę składników oraz kalorie i makroskładniki."},
        {"role": "user", "content": "Oceń ten posiłek. Podaj listę składników, kalorie, białko, tłuszcz i węglowodany w gramach."}
    ]

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        files=[{
            "filename": "meal.jpg",
            "contents": image_bytes
        }]
    )

    # Odpowiedź powinna zawierać tekst z rozpoznaniem
    return response.choices[0].message.content

def parse_openai_response(text):
    """
    Przetwarza odpowiedź GPT, aby wyciągnąć składniki i wartości odżywcze.
    Zakładamy prosty format (np. JSON lub listę), ale jeśli GPT zwróci tekst, trzeba będzie to dostosować.
    Dla uproszczenia zrobimy parser tekstowy.
    """

    # Prosty parser - zakładamy, że w tekście jest coś takiego:
    # Składniki: jabłko, banan
    # Kalorie: 150
    # Białko: 2g
    # Tłuszcz: 1g
    # Węglowodany: 30g

    lines = text.split("\n")
    data = {
        "ingredients": [],
        "kcal": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0
    }

    for line in lines:
        line = line.strip().lower()
        if line.startswith("składniki") or line.startswith("ingredients"):
            parts = line.split(":")
            if len(parts) > 1:
                ingr = parts[1].split(",")
                data["ingredients"] = [i.strip() for i in ingr]
        elif line.startswith("kalorie") or line.startswith("calories"):
            parts = line.split(":")
            if len(parts) > 1:
                try:
                    data["kcal"] = float(parts[1].strip().replace("kcal", ""))
                except:
                    pass
        elif line.startswith("białko") or line.startswith("protein"):
            parts = line.split(":")
            if len(parts) > 1:
                try:
                    data["protein"] = float(parts[1].strip().replace("g", ""))
                except:
                    pass
        elif line.startswith("tłuszcz") or line.startswith("fat"):
            parts = line.split(":")
            if len(parts) > 1:
                try:
                    data["fat"] = float(parts[1].strip().replace("g", ""))
                except:
                    pass
        elif line.startswith("węglowodany") or line.startswith("carbohydrates") or line.startswith("carbs"):
            parts = line.split(":")
            if len(parts) > 1:
                try:
                    data["carbs"] = float(parts[1].strip().replace("g", ""))
                except:
                    pass

    return data

# -------------------
# INTERFEJS Streamlit
# -------------------

st.set_page_config(page_title="Licznik kalorii AI", layout="centered")
st.title("🥗 Licznik kalorii z AI - zdjęcie + kod kreskowy + IG")

menu = st.sidebar.selectbox("Wybierz opcję", [
    "➕ Dodaj posiłek ręcznie",
    "📷 Dodaj z kodu kreskowego",
    "📸 Dodaj ze zdjęcia (AI)",
    "🥦 Indeks glikemiczny",
    "📊 Historia posiłków"
])

if menu == "➕ Dodaj posiłek ręcznie":
    st.subheader("Dodaj posiłek ręcznie")
    produkt = st.text_input("Nazwa produktu")
    gramatura = st.number_input("Ilość (w gramach)", min_value=1, value=100)
    kcal = st.number_input("Kalorie na 100g", min_value=0.0)
    bialko = st.number_input("Białko na 100g", min_value=0.0)
    tluszcz = st.number_input("Tłuszcz na 100g", min_value=0.0)
    weglo = st.number_input("Węglowodany na 100g", min_value=0.0)

    if st.button("Zapisz posiłek"):
        przel_kcal = round(kcal * gramatura / 100, 2)
        przel_bialko = round(bialko * gramatura / 100, 2)
        przel_tluszcz = round(tluszcz * gramatura / 100, 2)
        przel_weglo = round(weglo * gramatura / 100, 2)

        gi = check_gi_level(produkt)
        if gi == "wysoki":
            st.error("🚨 Uwaga: produkt ma wysoki indeks glikemiczny!")
        elif gi == "niski":
            st.success("✅ Świetnie! Produkt ma niski indeks glikemiczny.")
        elif gi == "średni":
            st.warning("ℹ️ Produkt ma średni indeks glikemiczny.")

        save_data({
            "Data": datetime.now().date().isoformat(),
            "Godzina": datetime.now().strftime("%H:%M"),
            "Produkt": produkt,
            "Kalorie": przel_kcal,
            "Bialko": przel_bialko,
            "Tluszcz": przel_tluszcz,
            "Weglowodany": przel_weglo,
            "Gramatura": gramatura
        })
        st.success("✅ Zapisano posiłek!")

elif menu == "📷 Dodaj z kodu kreskowego":
    st.subheader("Dodaj produkt z kodu kreskowego")
    barcode = st.text_input("Wpisz kod kreskowy")
    if st.button("Wyszukaj produkt"):
        result = get_product_info(barcode)
        if result:
            st.write(f"**Znaleziono:** {result['name']}")
            gramatura = st.number_input("Ilość (w gramach)", min_value=1, value=100)

            przel_kcal = round(result["kcal"] * gramatura / 100, 2)
            przel_bialko = round(result["protein"] * gramatura / 100, 2)
            przel_tluszcz = round(result["fat"] * gramatura / 100, 2)
            przel_weglo = round(result["carbs"] * gramatura / 100, 2)

            gi = check_gi_level(result['name'])
            if gi == "wysoki":
                st.error("🚨 Uwaga: produkt ma wysoki indeks glikemiczny!")
            elif gi == "niski":
                st.success("✅ Świetnie! Produkt ma niski indeks
