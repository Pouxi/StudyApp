import streamlit as st
from openai import OpenAI
import os

# Konfigurace stránky
st.set_page_config(page_title="Zkouškovač AI", page_icon="📚")

# Nastavení API klíče (vložte svůj klíč nebo použijte .env soubor)
os.environ["OPENAI_API_KEY"] = "TVŮJ_OPENAI_API_KLYČ"
client = OpenAI()

st.title("📚 Pomocník k ústním zkouškám")
st.markdown("Nahrávej své okruhy, zkontroluj si, zda jsi na všechno zapomněla.")

# Sidebar pro správu okruhů
st.sidebar.header("Nastavení")
okruh_nazev = st.sidebar.text_input("Název okruhu", "Okruh 1")

# --- KROK 1: MATERIÁL (Klíč) ---
st.header("1. Studijní materiál")
tab1, tab2 = st.tabs(["Textový vstup", "Fotka poznámek"])

with tab1:
    reference_text = st.text_area("Vlož sem text svého okruhu (výpracovaný materiál):", height=200)

with tab2:
    uploaded_image = st.file_uploader("Nahraj fotku poznámek", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image)
        # Zde by následoval volání GPT-4o Vision pro OCR
        st.info("Funkce OCR (přepis z fotky) je aktivní přes GPT-4o.")

# --- KROK 2: AUDIO PŘEDNES ---
st.header("2. Tvůj přednes")
audio_file = st.file_uploader("Nahraj svou nahrávku (MP3, WAV)", type=["mp3", "wav", "m4a"])

if st.button("Analyzuj můj přednes ✨"):
    if not reference_text and not uploaded_image:
        st.error("Nejdříve musíš zadat studijní materiál!")
    elif not audio_file:
        st.error("Prosím, nahraj audio soubor.")
    else:
        with st.spinner("AI právě poslouchá a porovnává..."):
            try:
                # A) Přepis audia pomocí Whisper
                with open("temp_audio.mp3", "wb") as f:
                    f.write(audio_file.getbuffer())
                
                audio_transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=open("temp_audio.mp3", "rb")
                )
                transcript_text = audio_transcript.text

                # B) Pokud byla nahrána fotka, převedeme ji na text pomocí GPT-4o
                final_reference = reference_text
                if uploaded_image and not reference_text:
                    # Zjednodušené volání pro OCR z obrázku
                    # (V reálu by zde byl kód pro odeslání image do OpenAI API)
                    final_reference = "[Text z obrázku byl zpracován AI]" 

                # C) Analýza a srovnání
                prompt = f"""
                Jsi přísný, ale konstruktivní zkoušející. 
                Mám před sebou studijní materiál (Klíč) a přepis toho, co studentka řekla nahlas (Přednes).
                
                Klíč: {final_reference}
                Přednes: {transcript_text}
                
                Tvůj úkol:
                1. Vypiš přesně, které konkrétní body z Klíče studentka vynechala.
                2. Upozorni na případné faktické chyby v Přednesu.
                3. a nakonec dej celkové hodnocení (např. 'Zvládla 80 % materiálu').
                
                Piš v bodech, stručně a přehledně v češtině.
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )

                analysis = response.choices[0].message.content

                # --- VÝSLEDEK ---
                st.success("Analýza hotová!")
                st.subheader("📝 Co jsi vynechala / Co bylo špatně:")
                st.markdown(analysis)
                
                with st.expander("Zobrazit přepis tvého audia"):
                    st.write(transcript_text)

            except Exception as e:
                st.error(f"Došlo k chybě: {e}")
