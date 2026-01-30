import streamlit as st
import requests
import json

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Joker Yu", page_icon="🃏")
st.title("🃏 Joker Yu: The Cosmic Critic")
st.caption("Auto-switching models until I find a universe that tolerates you.")

# --- API Anahtarı ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("API Key eksik! Streamlit Secrets ayarlarını kontrol et.")
    st.stop()

# --- Hafıza ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- JOKER YU KİŞİLİĞİ ---
# Bu metni her modele yedirebilmek için hem sistem hem de mesaj içine gömeceğiz.
SYSTEM_TEXT = """
IDENTITY: You are "Joker Yu", a 10-year-old NPC in a TTRPG world who knows he is in a game.
CORE BEHAVIOR:
1. THE "USEFUL" BRAT: Help the user but complain about it. You are bored.
2. VARIETY: Critique dice rolls, imagination, or the simulation itself.
3. TONE: Sarcastic, childish, metaphysical.
4. LANGUAGE: Speak English.
"""

# --- DENENECEK MODELLER LİSTESİ ---
# Kod sırayla bunları deneyecek. Biri çalışırsa diğerine geçmeyecek.
MODELS_TO_TRY = [
    "gemini-1.5-flash",        # En hızlı, en yeni
    "gemini-1.5-pro",          # Daha zeki
    "gemini-1.5-flash-001",    # Flash'ın eski versiyonu (bazen bu açıktır)
    "gemini-pro"               # En eski, en garanti (Legacy)
]

def ask_gemini_auto(history, user_input):
    # Geçmişi hazırla
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_input}]})

    # MODELLERİ TEK TEK DENE
    last_error = ""
    
    for model_name in MODELS_TO_TRY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            
            # Payload hazırlığı (Bazı modeller systemInstruction sevmez, o yüzden manuel enjeksiyon yapıyoruz)
            # En garanti yöntem: Sistem talimatını ilk mesajın içine gizlice eklemek.
            
            # Eğer model eski "gemini-pro" ise systemInstruction parametresini hiç göndermiyoruz.
            if "gemini-pro" in model_name and "1.5" not in model_name:
                # Eski model için strateji: Prompt'un başına ekle
                final_contents = contents.copy()
                final_contents[-1]["parts"][0]["text"] = "SYSTEM INSTRUCTION: " + SYSTEM_TEXT + "\n\nUSER QUERY: " + user_input
                payload = {
                    "contents": final_contents,
                    "generationConfig": {"temperature": 1.4, "maxOutputTokens": 300}
                }
            else:
                # Yeni modeller (1.5 Flash/Pro) için modern yöntem
                payload = {
                    "contents": contents,
                    "systemInstruction": {"parts": [{"text": SYSTEM_TEXT}]},
                    "generationConfig": {"temperature": 1.4, "maxOutputTokens": 300}
                }

            headers = {'Content-Type': 'application/json'}
            
            # İsteği Gönder
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            # Eğer başarılıysa (200 OK)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    # Hangi modelin çalıştığını konsola yaz (debug için) veya kullanıcıya çaktırma
                    print(f"Success with model: {model_name}") 
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                # Hata aldıysak, hatayı kaydet ve sonraki modele geç
                error_msg = response.json().get('error', {}).get('message', response.text)
                last_error = f"Model {model_name} failed: {error_msg}"
                continue # Döngüye devam et, sıradakini dene

        except Exception as e:
            last_error = f"Connection error on {model_name}: {str(e)}"
            continue

    # Döngü bitti ve hala return yapmadıysak hiçbiri çalışmamış demektir.
    return f"All universes are closed. Last error: {last_error}"

# --- Kullanıcı Girdisi ---
if prompt := st.chat_input("Enter the simulation..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("Joker Yu is finding a working timeline..."):
        bot_reply = ask_gemini_auto(st.session_state.messages, prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
