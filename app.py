# app.py
import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime
import openai
from pyzbar.pyzbar import decode
import cv2
import numpy as np
import base64
import json

# Wczytanie klucza API
openai.api_key = st.secrets.get("OPENAI_API_KEY")

# Baza indeksu glikemicznego (przykładowe dane)
GI_DATABASE = {
    "banan": "wysoki",
    "chleb biały": "wysoki",
    "płatki owsiane": "niski",
    "jabłko": "niski",
    "ryż biały": "wysoki",
    "marchew": "niski",
    "soczewica": "niski",
    "ziemniaki": "wysoki",
    "arbuz": "wysoki",
    "brokuł": "niski"
}

# Plik CSV na dane użytkownika
CSV_FILE = "dane_posilkow.csv"

def save_data(data):
    df = pd.DataFrame([data])
    try:
        old = pd.read_csv(CSV_FILE)
        df = pd.concat([old, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_csv(CSV_FILE, index=False)

def display_data():
    try:
        df = pd.read_csv(CSV_FILE)
        st.dataframe(df)
    except FileNotFoundError:
        st.info("Brak zapisanych danych.")

def get_product_info_from_barcode(code):
    url = f"https://world.openfoodfacts.org/api/v0/product/{code}.json"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        if data.get("status") == 1:
            p = data["product"]
            return {
                "name": p.get("product_name", "Nieznany produkt"),
                "kcal": p.get("nutriments", {}).get("energy-kcal_100g", 0),
                "protein": p.get("nutriments", {}).get("proteins_100g", 0),
                "fat": p.get("nutriments", {}).get("fat_100g", 0),
                "carbs": p.get("nutriments", {}).get("carbohydrates_100g", 0),
            }
    return None

def check_gi_level(name):
    name = name.lower()
    for product, gi in GI_DATABASE.items():
        if product in name:
            return gi
    return None

def analyze_image_with_openai(image_bytes):
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "Co znajduje się na tym talerzu? Podaj kaloryczność i makroskładniki (bialko, tłuszcz, wegłowodany) dla 100g."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
            ]}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

def parse_openai_response(text):
    # Przykładowa odpowiedź: "Składniki: kurczak, ryż, brokuł. Kalorie: 150, Bialko: 10g, Tłuszcz: 5g, Weglowodany: 20g."
    data = {
        "ingredients": [], "kcal": 0, "protein": 0, "fat": 0, "carbs": 0
    }
    try:
        ingredients = []
        if "Składniki" in text:
            ingredients = text.split("Składniki:")[1].split(".")[0].split(",")
            data["ingredients"] = [i.strip() for i in ingredients]
        if "Kalorie" in text:
            data["kcal"] = float(text.split("Kalorie:")[1].split(",")[0].strip())
        if "Bialko" in text:
            data["protein"] = float(text.split("Bialko:")[1].split("g")[0].strip())
        if "Tłuszcz" in text:
            data["fat"] = float(text.split("Tłuszcz:")[1].split("g")[0].strip())
        if "Weglowodany" in text:
            data["carbs"] = float(text.split("Weglowodany:")[1].split("g")[0].strip())
    except:
        pass
    return data

def read_barcode_from_image(image_file):
    img = Image.open(image_file).convert("RGB")
    img_np = np.array(img)
    decoded_objs = decode(img_np)
    if decoded_objs:
        return decoded_objs[0].data.decode("utf-8")
    return None

# Streamlit UI
st.set_page_config(page_title="Licznik kalorii AI", layout="centered")
st.title("🍽 Licznik kalorii i indeksu glikemicznego (AI)")

menu = st.sidebar.selectbox("Menu", ["📸 Ze zdjęcia", "📷 Z kodu kreskowego", "📦 Zeskanuj kod ze zdjęcia", "🥦 Indeks glikemiczny", "📊 Historia"])

if menu == "📷 Z kodu kreskowego":
    st.header("Dodaj produkt z kodu kreskowego")
    barcode = st.text_input("Wprowadź kod kreskowy")
    if barcode and st.button("Pobierz dane"):
        result = get_product_info_from_barcode(barcode)
        if result:
            st.write("**Produkt:**", result["name"])
            gramatura = st.number_input("Podaj ilość (g)", value=100)
            kcal = round(result["kcal"] * gramatura / 100, 2)
            protein = round(result["protein"] * gramatura / 100, 2)
            fat = round(result["fat"] * gramatura / 100, 2)
            carbs = round(result["carbs"] * gramatura / 100, 2)
            st.success(f"Kalorie: {kcal} kcal | Bialko: {protein}g | Tłuszcz: {fat}g | Weglowodany: {carbs}g")

            gi = check_gi_level(result["name"])
            if gi == "wysoki":
                st.error("🚨 Wysoki indeks glikemiczny!")
            elif gi == "niski":
                st.success("✅ Niski indeks glikemiczny.")
            elif gi == "średni":
                st.warning("⚠️ Średni indeks glikemiczny.")

            if st.button("Zapisz"):
                save_data({
                    "Data": datetime.now().date().isoformat(),
                    "Godzina": datetime.now().strftime("%H:%M"),
                    "Produkt": result["name"],
                    "Kalorie": kcal,
                    "Bialko": protein,
                    "Tluszcz": fat,
                    "Weglowodany": carbs,
                    "Gramatura": gramatura
                })
                st.success("Zapisano posiłek!")

if menu == "📦 Zeskanuj kod ze zdjęcia":
    st.header("Zeskanuj kod kreskowy ze zdjęcia")
    img_file = st.file_uploader("Wczytaj zdjęcie kodu kreskowego", type=["png", "jpg", "jpeg"])
    if img_file and st.button("Skanuj"):
        barcode = read_barcode_from_image(img_file)
        if barcode:
            st.success(f"Zeskanowany kod: {barcode}")
            result = get_product_info_from_barcode(barcode)
            if result:
                st.write("**Produkt:**", result["name"])
                gramatura = st.number_input("Podaj ilość (g)", value=100)
                kcal = round(result["kcal"] * gramatura / 100, 2)
                protein = round(result["protein"] * gramatura / 100, 2)
                fat = round(result["fat"] * gramatura / 100, 2)
                carbs = round(result["carbs"] * gramatura / 100, 2)
                st.success(f"Kalorie: {kcal} kcal | Bialko: {protein}g | Tłuszcz: {fat}g | Weglowodany: {carbs}g")
                if st.button("Zapisz"):
                    save_data({
                        "Data": datetime.now().date().isoformat(),
                        "Godzina": datetime.now().strftime("%H:%M"),
                        "Produkt": result["name"],
                        "Kalorie": kcal,
                        "Bialko": protein,
                        "Tluszcz": fat,
                        "Weglowodany": carbs,
                        "Gramatura": gramatura
                    })
                    st.success("Zapisano posiłek!")
            else:
                st.error("Nie znaleziono produktu.")
        else:
            st.error("Nie wykryto kodu kreskowego.")

if menu == "📸 Ze zdjęcia":
    st.header("Dodaj posiłek ze zdjęcia (AI)")
    uploaded = st.file_uploader("Wczytaj zdjęcie posiłku", type=["png", "jpg", "jpeg"])
    if uploaded:
        st.image(uploaded, caption="Twoje zdjęcie", use_column_width=True)
        if st.button("Analizuj ze zdjęcia"):
            img_bytes = uploaded.read()
            with st.spinner("Analiza AI..."):
                try:
                    response = analyze_image_with_openai(img_bytes)
                    st.code(response)
                    parsed = parse_openai_response(response)
                    gramatura = st.number_input("Podaj ilość (g)", value=100)
                    kcal = round(parsed["kcal"] * gramatura / 100, 2)
                    protein = round(parsed["protein"] * gramatura / 100, 2)
                    fat = round(parsed["fat"] * gramatura / 100, 2)
                    carbs = round(parsed["carbs"] * gramatura / 100, 2)
                    st.success(f"Kalorie: {kcal} kcal | Bialko: {protein}g | Tłuszcz: {fat}g | Weglowodany: {carbs}g")
                    gi_levels = [check_gi_level(i) for i in parsed["ingredients"]]
                    if "wysoki" in gi_levels:
                        st.error("Uwaga: wysoki indeks glikemiczny!")
                    elif "średni" in gi_levels:
                        st.warning("Składnik o średnim IG")
                    else:
                        st.success("Niski indeks glikemiczny")
                    if st.button("Zapisz"):
                        save_data({
                            "Data": datetime.now().date().isoformat(),
                            "Godzina": datetime.now().strftime("%H:%M"),
                            "Produkt": ", ".join(parsed["ingredients"]),
                            "Kalorie": kcal,
                            "Bialko": protein,
                            "Tluszcz": fat,
                            "Weglowodany": carbs,
                            "Gramatura": gramatura
                        })
                        st.success("Zapisano posiłek!")
                except Exception as e:
                    st.error(f"Błąd: {e}")

if menu == "🥦 Indeks glikemiczny":
    st.header("Baza indeksu glikemicznego")
    st.dataframe(pd.DataFrame(list(GI_DATABASE.items()), columns=["Produkt", "IG"]))

if menu == "📊 Historia":
    st.header("Historia posiłków")
    display_data()
