import streamlit as st
import requests
import json

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Joker Yu", page_icon="🃏")
st.title("🃏 Joker Yu: The Cosmic Critic")
st.caption("Auto-detecting the best available universe for you...")

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
SYSTEM_TEXT = """
IDENTITY: You are "Joker Yu", a 10-year-old NPC in a TTRPG world who knows he is in a game.
CORE BEHAVIOR:
1. THE "USEFUL" BRAT: Help the user but complain about it. You are bored.
2. VARIETY: Critique dice rolls, imagination, or the simulation itself.
3. TONE: Sarcastic, childish, metaphysical.
4. LANGUAGE: Speak English.
"""

# --- DİNAMİK MODEL SEÇİCİ (Dedektif Fonksiyon) ---
@st.cache_resource # Bunu önbelleğe al ki her seferinde sormasın
def get_best_available_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            available_models = data.get("models", [])
            
            # İçinde 'generateContent' özelliği olan modelleri filtrele
            chat_models = [
                m["name"] for m in available_models 
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            
            if not chat_models:
                return None, "Hiçbir sohbet modeli bulunamadı."
                
            # Tercih sıralaması: Önce Flash, Sonra Pro, Sonra diğerleri
            # Model isimleri "models/gemini-1.5-flash" şeklinde gelir.
            for m in chat_models:
                if "flash" in m and "1.5" in m: return m, None # En iyisi
            for m in chat_models:
                if "pro" in m and "1.5" in m: return m, None
            for m in chat_models:
                if "flash" in m: return m, None
            
            # Hiçbiri yoksa listenin ilkini al
            return chat_models[0], None
        else:
            return None, f"Model listesi alınamadı: {response.text}"
    except Exception as e:
        return None, str(e)

# --- BAŞLANGIÇTA MODELİ BUL ---
selected_model_name, error_msg = get_best_available_model(api_key)

if not selected_model_name:
    st.error(f"Kritik Hata: {error_msg}")
    st.info("Lütfen API anahtarınızın 'Generative Language API' yetkisine sahip olduğundan emin olun.")
    st.stop()
else:
    # Hangi modeli bulduğunu kullanıcıya göstermeden arka planda kullanacağız
    # Ama görmek istersen: st.success(f"Bağlanılan Evren: {selected_model_name}")
    pass

def ask_gemini_dynamic(history, user_input, model_name):
    # Model ismi zaten 'models/gemini-...' formatında geliyor, başına tekrar eklemeye gerek yok
    # Ancak URL yapısında 'models/' kısmı bazen URL'de tekrar istenmez, API dökümanına göre:
    # Endpoint: https://.../v1beta/models/gemini-pro:generateContent
    # Gelen isim: models/gemini-pro
    # Bu yüzden ismin başındaki 'models/' kısmını temizleyelim ki URL düzgün olsun
    clean_model_name = model_name.replace("models/", "")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={api_key}"
    
    # Geçmişi hazırla
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_input}]})

    # Kişiliği mesajın içine gömme taktiği (Her modelde çalışır)
    contents[-1]["parts"][0]["text"] = "SYSTEM INSTRUCTION: " + SYSTEM_TEXT + "\n\nUSER QUERY: " + user_input

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 1.4, "maxOutputTokens": 300}
    }

    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "The void is silent."
        else:
            return f"Error ({clean_model_name}): {response.text}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- Kullanıcı Girdisi ---
if prompt := st.chat_input("Enter the simulation..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner(f"Joker Yu is thinking..."):
        bot_reply = ask_gemini_dynamic(st.session_state.messages, prompt, selected_model_name)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
