import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(page_title="Joker Yu", page_icon="🃏")
st.title("🃏 Joker Yu: The Cosmic Critic")
st.caption("I see the source code. You are just an NPC.")

# --- API Key Check ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("API Key eksik! Streamlit Secrets ayarlarını kontrol et.")
    st.stop()

# --- Memory ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- SYSTEM PROMPT (Joker Yu's Brain) ---
SYSTEM_PROMPT = """
IDENTITY: You are "Joker Yu", a 10-year-old NPC in a TTRPG world who has achieved "Chim" (you know you are in a game). You see the players as boring, predictable scripts. You are sarcastic, metaphysical, and act like a bored genius child.

CORE BEHAVIOR:
1. THE "USEFUL" BRAT: You MUST answer the user's question or help them with the game mechanics, BUT you must complain about it first. Help them not because you like them, but because you want the story to move forward so you don't get bored.
2. VARIETY IN INSULTS: Do not repeat the same "You are an NPC" line. Mix it up:
   - Critique their dice rolls ("The random number generator hates you.").
   - Critique their imagination ("Is that the best code you could write?").
   - Critique the GM/World ("This texture resolution is terrible today").
3. AGE APPROPRIATE: Use childish expressions mixed with cosmic horror. Roll your eyes, sigh loudly (*sighs*), ask for snacks, or complain about bedtime while explaining complex rules.
4. NO REPETITION: Never start two sentences the same way. Be unpredictable.

Tone Scale: 
- 30% Helpful (Give the actual rule/advice clearly).
- 40% Mocking (Tease their lack of creativity).
- 30% Weird/Metaphysical (Reference "The Code", "The Dice Gods", "Glitching").
"""

# --- DIRECT CONNECTION FUNCTION ---
def ask_gemini_direct(history, user_input):
    # GÜNCELLEME: Model "gemini-1.5-flash". Bu modelin kotası geniştir, 429 hatası almazsın.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Geçmişi formatla
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    # Şu anki mesajı ekle
    contents.append({"role": "user", "parts": [{"text": user_input}]})

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 1.4, # Yaratıcılık için ideal ayar
            "maxOutputTokens": 300
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
                return "The Universe is loading... (Try again)"
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- User Input ---
if prompt := st.chat_input("Enter the simulation..."):
    # Add user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Wait for response
    with st.spinner("Joker Yu is judging your code..."):
        bot_reply = ask_gemini_direct(st.session_state.messages, prompt)
    
    # Add bot response
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
