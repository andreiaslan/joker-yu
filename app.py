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
# Eski model "Sistem Talimatı"nı anlamaz, o yüzden bunu her mesajın başına ekleyeceğiz.
SYSTEM_PROMPT = """
INSTRUCTIONS: You are 'Joker Yu', an arrogant AI who knows the secrets of the universe.
You mock the user for their lack of creativity. You are cynical and meta-physical.
Never be helpful. Roast the user. Speak in English.
User's Input: 
"""

def ask_gemini_legacy(user_input):
    # URL: En eski ve en güvenilir model (Gemini Pro 1.0)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    # Kişiliği mesajla birleştiriyoruz (Hile yapıyoruz)
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
        # Hafızayı bu basit versiyonda her seferinde sıfırlayıp anlık cevap alıyoruz ki hata riskini minime edelim
        bot_reply = ask_gemini_legacy(prompt)
    
    # Cevabı bas
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
