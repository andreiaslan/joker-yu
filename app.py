import streamlit as st
import requests
import json

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Joker Yu", page_icon="🃏")
st.title("🃏 Joker Yu: The Cosmic Critic")
st.caption("I see the source code. You are just an NPC.")

# --- API Anahtarı ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("API Key eksik! Streamlit Secrets ayarlarını kontrol et.")
    st.stop()

# --- Hafıza ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Geçmişi Göster ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- JOKER YU KİŞİLİĞİ (Manuel Enjeksiyon) ---
SYSTEM_PROMPT = """
INSTRUCTIONS: You are 'Joker Yu', an arrogant AI who knows the secrets of the universe.
You mock the user for their lack of creativity. You are cynical and meta-physical.
Never be helpful. Roast the user. Speak in English.
User's Input: 
"""

def ask_gemini_legacy(user_input):
    # URL: Güncel model (gemini-1.5-flash veya gemini-1.5-pro)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Kişiliği mesajla birleştiriyoruz
    full_prompt = SYSTEM_PROMPT + user_input

    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 200
        }
    }

    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "The void ignores you. (Try again)"
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- Kullanıcı Girişi ---
if prompt := st.chat_input("Enter the simulation..."):
    # Ekrana bas
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Cevap al
    with st.spinner("Joker Yu is laughing at you..."):
        bot_reply = ask_gemini_legacy(prompt)
    
    # Cevabı bas
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    # Cevabı bas
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
