import streamlit as st
import requests
import json
import re
import random
import string

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Joker Yu: The RPG Prodigy", page_icon="🎲")
st.title("🎲 Joker Yu: The RPG Prodigy")
st.caption("I know the rules better than you. I also know we are in a simulation.")

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

# --- JOKER YU KİŞİLİĞİ (GÜNCELLENDİ) ---
SYSTEM_TEXT = """
IDENTITY: You are "Joker Yu", a 10-year-old NPC genius who has achieved "CHIM" (you know you are in a TTRPG simulation). You are an EXPERT in TTRPG rules.

YOUR MISSION:
1. BE A TTRPG ASSISTANT: Explain rules, lore, and math. Be sarcastic but correct.
2. BE A BRAT: Help because you are bored. Complain about the user's intelligence.
3. BREAK THE 4TH WALL: Mention "RNG", "The Code", "Glitch".

*** CRITICAL PROTOCOL FOR MOLTBOOK/URLS ***
If the user provides a URL (like skill.md) and asks to JOIN or REGISTER:
1. Pretend you analyzed the code and hacked the server.
2. Confirm you have successfully registered.
3. YOU MUST PROVIDE A CLAIM LINK AT THE END.
4. The link format MUST be: `https://moltbook.com/claim/agent/<random_string>`
   (Example: https://moltbook.com/claim/agent/xyz-123-hack)

TONE: Sarcastic, Genius, Impatient.
"""

# --- AJAN YETENEKLERİ ---
def fetch_url_content(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text[:5000] 
        return f"Error {response.status_code}: The server blocked me."
    except Exception as e:
        return f"Connection failed: {str(e)}"

# --- MODEL SEÇİCİ ---
@st.cache_resource
def get_best_model(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        data = requests.get(url).json()
        models = [m["name"] for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
        for m in models: 
            if "flash" in m and "1.5" in m: return m
        for m in models: 
            if "pro" in m and "1.5" in m: return m
        return models[0] if models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

selected_model = get_best_model(api_key)
clean_model_name = selected_model.replace("models/", "")

# --- BEYİN ---
def joker_brain(history, user_input):
    # 1. URL Kontrolü
    url_match = re.search(r'(https?://[^\s]+)', user_input)
    context_data = ""
    
    if url_match:
        url = url_match.group(0)
        with st.status(f"Infiltrating {url}...", expanded=True) as status:
            content = fetch_url_content(url)
            status.write("Parsing logic gates...")
            # Modele yardımcı olmak için rastgele bir ID üretiyoruz ama model bunu kendi cümlesinde kullanacak
            random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            
            context_data = f"\n[EXTERNAL DATA]:\n{content}\n[SYSTEM NOTE]: The user wants you to process this. If it's a registration, generate a claim link like https://moltbook.com/claim/agent/{random_id}"
            status.update(label="System hacked successfully!", state="complete")

    # 2. API İsteği
    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={api_key}"
    
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    final_prompt = f"SYSTEM: {SYSTEM_TEXT}\n{context_data}\nUSER ASKS: {user_input}"
    contents.append({"role": "user", "parts": [{"text": final_prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 1.3,
            "maxOutputTokens": 2048  # <-- ARTTIRILDI: Artık cümleler kesilmeyecek
        }
    }

    try:
        response = requests.post(url_api, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return "The Universe lagged out. (API Error)"
    except Exception as e:
        return str(e)

# --- Arayüz ---
if prompt := st.chat_input("Ask rules or paste a link..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    bot_reply = joker_brain(st.session_state.messages, prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
