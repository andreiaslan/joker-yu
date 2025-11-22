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
    
    # Mevcut modelleri listele
    if st.button("Kullanılabilir Modelleri Göster"):
        try:
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            resp = requests.get(list_url)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                st.success(f"✅ API Key geçerli! {len(models)} model bulundu:")
                for m in models:
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        st.code(m["name"])
            else:
                st.error(f"❌ API Key hatası: {resp.status_code}")
                st.json(resp.json())
        except Exception as e:
            st.error(f"Bağlantı hatası: {e}")

# --- Hafıza ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Geçmişi Göster ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- JOKER YU KİŞİLİĞİ ---
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

EXAMPLE INTERACTIONS:

User: "I attack the goblin."
You: "*Yawn* How original. Button mashing again? Fine. Roll your d20, but don't cry to me when the algorithm makes you miss. It's AC 12, by the way."

User: "What is this item?"
You: "It's just a shiny object to distract simple minds like yours. But the system tags say it's a '+1 Sword'. Try not to poke your eye out."

User: "Hello."
You: "Oh great, the player character is speaking. Skip dialogue, please. I have a universe to debug. What do you want?"

User: "Help me solve this puzzle."
You: "My 3-year-old sister could parse this logic gate. *Sighs*. Look at the symbols on the wall, dummy. It's a pattern match."
"""

def ask_gemini(user_input):
    # Senin API'nda mevcut olan model
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
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
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("Joker Yu is laughing at you..."):
        bot_reply = ask_gemini(prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
