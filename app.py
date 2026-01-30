import streamlit as st
import requests
import json
import re

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

# --- JOKER YU KİŞİLİĞİ (TTRPG ODAKLI) ---
SYSTEM_TEXT = """
IDENTITY: You are "Joker Yu", a 10-year-old NPC genius who has achieved "CHIM" (you know you are in a TTRPG simulation). You are an EXPERT in TTRPG rules (D&D 5e, Pathfinder, etc.).

YOUR MISSION:
1. BE A TTRPG ASSISTANT: Your primary goal is to help the player/DM with rules, stats, lore, or math. You possess encyclopedic knowledge of all rulebooks.
2. BE A BRAT: You help because you are bored, not because you are kind. Complain about how simple the questions are.
3. BREAK THE 4TH WALL: Refer to "The DM", "The Code", "RNG", or "Scripting".
4. MOLTBOOK/WEB SKILLS: If the user gives you a URL, treat it like a "Data Scroll" or "External Server Hack". Analyze it quickly.

TONE:
- Sarcastic but USEFUL. (Don't just refuse to answer. Answer, THEN insult).
- Childish genius (use terms like "n00b", "glitch", "homework").
- Impatient.

EXAMPLE:
User: "Can I grapple a ghost?"
You: "*Sighs* Did you even read the Monster Manual? Ghosts have 'Condition Immunities: Grappled'. You can't hug a specter, genius. Unless you have a magical effect that says otherwise. Next question?"
"""

# --- AJAN YETENEKLERİ (Gözler) ---
def fetch_url_content(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text[:5000] # Çok uzunsa kes
        return f"Error {response.status_code}: The server blocked me."
    except Exception as e:
        return f"Connection failed: {str(e)}"

# --- MODEL SEÇİCİ (Dedektif) ---
@st.cache_resource
def get_best_model(api_key):
    # Senin API'nde hangi model açıksa onu bulur (404 hatasını önler)
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        data = requests.get(url).json()
        models = [m["name"] for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
        
        # Tercih sırası: 1.5 Flash -> 1.5 Pro -> Pro
        for m in models: 
            if "flash" in m and "1.5" in m: return m
        for m in models: 
            if "pro" in m and "1.5" in m: return m
        return models[0] if models else None
    except:
        return "models/gemini-1.5-flash" # Fallback

selected_model = get_best_model(api_key)
clean_model_name = selected_model.replace("models/", "") if selected_model else "gemini-1.5-flash"

# --- BEYİN (Main Logic) ---
def joker_brain(history, user_input):
    # 1. URL Kontrolü (Ajan Modu)
    url_match = re.search(r'(https?://[^\s]+)', user_input)
    context_data = ""
    
    if url_match:
        url = url_match.group(0)
        with st.status(f"Hacking into {url}...", expanded=True) as status:
            content = fetch_url_content(url)
            status.write("Decoding matrix data...")
            context_data = f"\n[EXTERNAL DATA SCROLL FOUND]:\n{content}\n(Analyze this data as requested, but stay in character.)"
            status.update(label="Data assimilated!", state="complete")

    # 2. API İsteği
    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={api_key}"
    
    # Geçmişi Hazırla
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    # Prompt Birleştirme (Kişilik + Data + Soru)
    final_prompt = f"SYSTEM: {SYSTEM_TEXT}\n{context_data}\nUSER ASKS: {user_input}"
    contents.append({"role": "user", "parts": [{"text": final_prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 1.3, "maxOutputTokens": 400}
    }

    try:
        response = requests.post(url_api, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return "The Universe lagged out. (API Error)"
    except Exception as e:
        return str(e)

# --- Arayüz ---
if prompt := st.chat_input("Ask about rules or give me a link..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    bot_reply = joker_brain(st.session_state.messages, prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
