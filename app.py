import streamlit as st
import pandas as pd
import requests
from PIL import Image
import numpy as np
from io import BytesIO
import json

st.set_page_config(page_title="Licznik kalorii ze zdjęcia / kodu", layout="centered")
st.title("🍽️ Licznik kalorii ze zdjęcia i kodu kreskowego")

st.markdown("""
### 📸 Zrób lub wybierz zdjęcie posiłku
Wybierz zdjęcie posiłku, które chcesz przesłać do analizy kalorycznej:
""")

uploaded_image = st.file_uploader("Zrób lub wybierz zdjęcie posiłku", type=["jpg", "jpeg", "png"])

if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Załadowany posiłek", use_column_width=True)
    st.success("📷 Zdjęcie zostało załadowane. Możesz teraz uruchomić analizę kalorii (funkcja AI lub OCR)")

# Tutaj można dodać dalsze przetwarzanie obrazu przez AI lub OCR (np. OpenAI lub custom model)

st.markdown("""
### 🔍 Lub dodaj produkt przez kod kreskowy
Wpisz lub zeskanuj kod kreskowy produktu, aby pobrać dane z OpenFoodFacts:
""")

barcode_input = st.text_input("📦 Kod kreskowy")

if barcode_input:
    response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode_input}.json")
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == 1:
            product = data["product"]
            st.success(f"🔍 Znaleziono produkt: {product.get('product_name', 'Brak nazwy')}")

            # Wyświetl dane odżywcze na 100g
            nutriments = product.get("nutriments", {})
            st.write("**Wartości odżywcze (na 100g):**")
            calories = nutriments.get("energy-kcal_100g", 0)
            proteins = nutriments.get("proteins_100g", 0)
            fat = nutriments.get("fat_100g", 0)
            carbs = nutriments.get("carbohydrates_100g", 0)

            st.write(f"- Kalorie: {calories} kcal")
            st.write(f"- Białko: {proteins} g")
            st.write(f"- Tłuszcz: {fat} g")
            st.write(f"- Węglowodany: {carbs} g")

            # Ilość spożyta (w gramach)
            grams = st.number_input("Podaj ilość w gramach", min_value=1, value=100)

            st.write("**📊 Przeliczone wartości odżywcze:**")
            st.write(f"- Kalorie: {round(calories * grams / 100, 2)} kcal")
            st.write(f"- Białko: {round(proteins * grams / 100, 2)} g")
            st.write(f"- Tłuszcz: {round(fat * grams / 100, 2)} g")
            st.write(f"- Węglowodany: {round(carbs * grams / 100, 2)} g")

            # Indeks glikemiczny (jeśli dostępny)
            ig_data = product.get("glycemic_index")
            if ig_data:
                st.info(f"Indeks glikemiczny: {ig_data}")
                if ig_data >= 70:
                    st.error("🚨 Wysoki indeks glikemiczny – spożywaj z umiarem")
                elif ig_data <= 55:
                    st.success("✅ Niski indeks glikemiczny – dobry wybór")
                else:
                    st.warning("⚠️ Średni indeks glikemiczny")
            else:
                st.info("ℹ️ Brak danych o indeksie glikemicznym")
        else:
            st.error("❌ Nie znaleziono produktu w bazie OpenFoodFacts")
    else:
        st.error("Błąd podczas pobierania danych z OpenFoodFacts")
