import streamlit as st
import google.generativeai as genai
import os
import tempfile

# 1. KONFIGURACE STRÁNKY
st.set_page_config(page_title="Zkouškovač AI (Gemini)", page_icon="📚")

# --- ZDE VLOŽ SVŮJ GOOGLE GEMINI API KLÍČ ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
# -------------------------------------------

genai.configure(api_key=GEMINI_API_KEY)

# Použijeme model gemini-1.5-flash (je extrémně rychlý a zdarma/levný)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📚 Pomocník k ústním zkouškám (Gemini Edition)")
st.markdown("Nahrávej své okruhy, zkontroluj si, zda jsi na všechno zapomněla.")

# Sidebar
st.sidebar.header("Nastavení")
okruh_nazev = st.sidebar.text_input("Název okruhu", "Okruh 1")

# --- KROK 1: MATERIÁL (Klíč) ---
st.header("1. Studijní materiál")
tab1, tab2 = st.tabs(["Textový vstup", "Fotka poznámek"])

reference_text = ""

with tab1:
    reference_text = st.text_area("Vlož sem text svého okruhu:", height=200)

with tab2:
    uploaded_image = st.file_uploader("Nahraj fotku poznámek", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image)
        with st.spinner("Gemini právě čte tvůj rukopis..."):
            try:
                # Gemini zpracuje obrázek přímo
                response = model.generate_content([
                    "Přepiš prosím přesně text z této fotky poznámek. Piš jen text, nic nepřidávej.", 
                    uploaded_image
                ])
                reference_text = response.text
                st.success("Text z fotky byl úspěšně převeden!")
                st.info(f"Rozpoznaný text: {reference_text}")
            except Exception as e:
                st.error(f"Chyba při čtení fotky: {e}")

# --- KROK 2: AUDIO PŘEDNES ---
st.header("2. Tvůj přednes")
audio_file = st.file_uploader("Nahraj svou nahrávku (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

if st.button("Analyzuj můj přednes ✨"):
    if not reference_text:
        st.error("Nejdříve musíš zadat studijní materiál!")
    elif not audio_file:
        st.error("Prosím, nahraj audio soubor.")
    else:
        with st.spinner("Gemini poslouchá a porovnává..."):
            try:
                # Gemini vyžaduje, aby audio soubor byl nahrán do jejich systému nebo předán jako bajty
                # Pro jednoduchost v Streamlitu vytvoříme dočasný soubor
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file.write(audio_file.getbuffer())
                    tmp_path = tmp_file.name

                # Nahraní souboru do Google API
                uploaded_audio = genai.upload_file(path=tmp_path)

                # Prompt pro analýzu
                prompt = f"""
                Jsi přísný, ale konstruktivní zkoušející. 
                Mám před sebou studijní materiál (Klíč) a nahrávku toho, co studentka řekla nahlas (Přednes).
                
                Klíč: {reference_text}
                
                Tvůj úkol:
                1. Nejdříve vypiš krátký přepis (transcript) toho, co studentka v nahrávce řekla.
                2. Poté vypiš přesně, které konkrétní body z Klíče studentka vynechala.
                3. Upozorni na případné faktické chyby v Přednesu.
                4. Na závěr dej celkové hodnocení (např. 'Zvládla 80 % materiálu').
                
                Piš v bodech, stručně a přehledně v češtině.
                """

                # Generování odpovědi (posíláme textový prompt + audio soubor)
                response = model.generate_content([prompt, uploaded_audio])
                
                # Smazání dočasného souboru
                os.remove(tmp_path)

                # --- VÝSLEDEK ---
                st.success("Analýza hotová!")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Došlo k chybě: {e}")
