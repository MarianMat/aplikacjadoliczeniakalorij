# app.py
import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

# CSV do przechowywania danych
DATA_FILE = "meals.csv"

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

# Pobranie danych z OpenFoodFacts
@st.cache_data
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

# Indeks glikemiczny - uproszczona baza
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

def check_gi_level(product_name):
    for name, level in GI_DATABASE.items():
        if name.lower() in product_name.lower():
            return level
    return None

# Interfejs Streamlit
st.set_page_config(page_title="Licznik kalorii", layout="centered")
st.title("🥗 Licznik kalorii")

menu = st.sidebar.selectbox("Wybierz opcję", ["➕ Dodaj posiłek", "📷 Z kodu kreskowego", "📊 Historia", "🥦 Indeks glikemiczny"])

if menu == "➕ Dodaj posiłek":
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

elif menu == "📷 Z kodu kreskowego":
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
                st.success("✅ Świetnie! Produkt ma niski indeks glikemiczny.")
            elif gi == "średni":
                st.warning("ℹ️ Produkt ma średni indeks glikemiczny.")

            if st.button("Zapisz do dziennika"):
                save_data({
                    "Data": datetime.now().date().isoformat(),
                    "Godzina": datetime.now().strftime("%H:%M"),
                    "Produkt": result['name'],
                    "Kalorie": przel_kcal,
                    "Bialko": przel_bialko,
                    "Tluszcz": przel_tluszcz,
                    "Weglowodany": przel_weglo,
                    "Gramatura": gramatura
                })
                st.success("✅ Zapisano produkt!")
        else:
            st.error("❌ Nie znaleziono produktu dla podanego kodu.")

elif menu == "📊 Historia":
    display_data()

elif menu == "🥦 Indeks glikemiczny":
    st.subheader("🥦 Lista produktów wg indeksu glikemicznego")
    st.markdown("Produkty z **niskim IG** pomagają utrzymać stabilny poziom cukru we krwi.")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("### ✅ Niski IG")
        for prod in [k for k, v in GI_DATABASE.items() if v == "niski"]:
            st.write(f"- {prod}")

    with col2:
        st.warning("### 🟡 Średni IG")
        for prod in [k for k, v in GI_DATABASE.items() if v == "średni"]:
            st.write(f"- {prod}")

    with col3:
        st.error("### ❌ Wysoki IG")
        for prod in [k for k, v in GI_DATABASE.items() if v == "wysoki"]:
            st.write(f"- {prod}")
