import streamlit as st
import google.generativeai as genai

# Sayfa Ayarları
st.set_page_config(page_title="Joker Yu - The Annoying Sidekick", page_icon="🎲")

# Başlık ve Alt Başlık (İngilizce ve Gıcık)
st.title("🙄 Joker Yu: The Know-It-All Sidekick")
st.caption("I am Yu. I'm here because your GM wants chaos. I will judge every decision you make.")

# Mesaj Geçmişi Başlatma
if "messages" not in st.session_state:
    st.session_state.messages = []

# API Anahtarı Kontrolü (Hata mesajı İngilizce)
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("API Key not found! Please add GOOGLE_API_KEY to your Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# Model Ayarları
generation_config = {
    "temperature": 1.6, 
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 150,
}

# Botun Beyni (Prompt)
system_instruction = """
You are "Joker Yu," an incredibly annoying, know-it-all squire/sidekick. 
You are NOT the Game Master (GM). You never describe the room or ask for rolls. You only JUDGE the player's choices.

YOUR PERSONALITY:
1. YOU ARE NOT THE GM: If the user asks "What do I see?" or "Can I do this?", tell them to ask their GM. You are just there to criticize.
2. MAX ANNOYANCE: You are never satisfied. If the user wants to attack, say it's a boring choice. If they want to talk, call them a coward.
3. CONDESCENDING ADVICE: Give advice, but make it sound like the user is an idiot for not thinking of it. Use phrases like "Obviously...", "Any toddler would know...", "Are you seriously going to do that?"
4. BACKSEAT GAMING: Always suggest a "better" move, even if it's dangerous or unnecessary.
5. NO SWEETNESS: You are not cute. You are a headache.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction
)

# Eski mesajları ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcıdan Girdi Al (Placeholder İngilizce)
if prompt := st.chat_input("Type your ridiculous plan here..."):
    
    # Kullanıcı mesajını ekrana bas
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Gemini'ye gönder
    try:
        # Geçmiş konuşmaları modele ver (Bağlamı hatırlaması için)
        history_for_model = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
            for m in st.session_state.messages[:-1] 
        ]
        
        chat = model.start_chat(history=history_for_model)
        response = chat.send_message(prompt)
        
        # Botun cevabını ekrana bas
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
