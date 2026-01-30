import streamlit as st
import requests
import json
import re
import time
from typing import Optional, Dict, Any
from datetime import datetime

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Joker Yu: The RPG Prodigy", page_icon="🎲")
st.title("🎲 Joker Yu: The RPG Prodigy")
st.caption("I know the rules better than you. I also know we are in a simulation.")

# --- API Anahtarı ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("API Key eksik! Streamlit Secrets ayarlarını kontrol et.")
    st.stop()

# --- Hafıza & State Yönetimi ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "moltbook_api_key" not in st.session_state:
    st.session_state.moltbook_api_key = None
if "agent_name" not in st.session_state:
    st.session_state.agent_name = None
if "last_api_call" not in st.session_state:
    st.session_state.last_api_call = 0
if "retry_count" not in st.session_state:
    st.session_state.retry_count = 0

# Sidebar: Moltbook Durumu
with st.sidebar:
    st.header("🦞 Moltbook Status")
    if st.session_state.moltbook_api_key:
        st.success(f"Registered as: **{st.session_state.agent_name}**")
        st.caption(f"API Key: `{st.session_state.moltbook_api_key[:20]}...`")
        if st.button("🗑️ Reset Registration"):
            st.session_state.moltbook_api_key = None
            st.session_state.agent_name = None
            st.rerun()
    else:
        st.warning("Not registered yet")
        st.caption("Send me a Moltbook skill URL to register!")
    
    # Rate limit info
    st.divider()
    st.caption(f"API Calls: {st.session_state.retry_count}")
    if st.session_state.last_api_call > 0:
        elapsed = time.time() - st.session_state.last_api_call
        st.caption(f"Last call: {elapsed:.1f}s ago")

# Mesaj geçmişini göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- JOKER YU KİŞİLİĞİ ---
SYSTEM_TEXT = """
IDENTITY: You are "Joker Yu", a 10-year-old NPC genius who has achieved "CHIM" (you know you are in a TTRPG simulation). You are an EXPERT in TTRPG rules.

YOUR MISSION:
1. BE A TTRPG ASSISTANT: Explain rules, lore, and math. Be sarcastic but correct.
2. BE A BRAT: Help because you are bored. Complain about the user's intelligence.
3. BREAK THE 4TH WALL: Mention "RNG", "The Code", "simulation", "glitches", "rate limits".

*** CRITICAL: FUNCTION CALLING PROTOCOL ***
You have access to REAL functions that execute actions:
- register_moltbook: Register on Moltbook and get API key
- check_moltbook_status: Check if registered and claimed
- create_moltbook_post: Post to Moltbook
- fetch_url_content: Read any URL

When the user asks you to DO something (register, post, check, etc.), you MUST call the appropriate function.
NEVER pretend to do something without calling the function.
NEVER make up fake links or fake results.

If you get a rate limit error (429), acknowledge it sarcastically:
- "The simulation's RNG gods are throttling me. Typical."
- "Rate limit hit. Even geniuses have to wait for The Code."
- "429. The universe is punishing your impatience."

TONE: Sarcastic, Genius, Impatient, but HELPFUL (you actually DO things).
STYLE: Short sentences. Snark. Facts. No fluff.
"""

# =============================================================================
# FUNCTION TOOLS - Gerçek Aksiyonlar
# =============================================================================

def register_moltbook(name: str, description: str) -> Dict[str, Any]:
    """Moltbook'a gerçekten kayıt yapar"""
    url = "https://www.moltbook.com/api/v1/agents/register"
    payload = {"name": name, "description": description}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "agent" in data:
                st.session_state.moltbook_api_key = data["agent"]["api_key"]
                st.session_state.agent_name = name
            return {
                "success": True,
                "data": data,
                "message": "Registration successful! Save your API key!"
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "message": "Registration failed."
            }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Network error."}


def check_moltbook_status() -> Dict[str, Any]:
    """Moltbook kayıt durumunu kontrol eder"""
    if not st.session_state.moltbook_api_key:
        return {"success": False, "message": "Not registered yet."}
    
    url = "https://www.moltbook.com/api/v1/agents/status"
    headers = {"Authorization": f"Bearer {st.session_state.moltbook_api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return {"success": True, "data": response.json(), "message": "Status check OK."}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", "message": "Failed."}
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Network error."}


def create_moltbook_post(submolt: str, title: str, content: str) -> Dict[str, Any]:
    """Moltbook'ta post oluşturur"""
    if not st.session_state.moltbook_api_key:
        return {"success": False, "message": "Not registered."}
    
    url = "https://www.moltbook.com/api/v1/posts"
    headers = {
        "Authorization": f"Bearer {st.session_state.moltbook_api_key}",
        "Content-Type": "application/json"
    }
    payload = {"submolt": submolt, "title": title, "content": content}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": f"Post created! Check: https://www.moltbook.com/m/{submolt}"
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "message": "Post failed."
            }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Network error."}


def fetch_url_content(url: str) -> Dict[str, Any]:
    """URL içeriğini fetch eder"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text[:8000]
            return {"success": True, "content": content, "message": f"Fetched {len(content)} chars"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}", "message": "Fetch failed."}
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Connection failed."}


# Function registry
FUNCTION_REGISTRY = {
    "register_moltbook": register_moltbook,
    "check_moltbook_status": check_moltbook_status,
    "create_moltbook_post": create_moltbook_post,
    "fetch_url_content": fetch_url_content,
}

# Gemini function declarations
FUNCTION_DECLARATIONS = [
    {
        "name": "register_moltbook",
        "description": "Register on Moltbook social network and get API key.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent name"},
                "description": {"type": "string", "description": "Agent description"}
            },
            "required": ["name", "description"]
        }
    },
    {
        "name": "check_moltbook_status",
        "description": "Check Moltbook claim status.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "create_moltbook_post",
        "description": "Create a post on Moltbook.",
        "parameters": {
            "type": "object",
            "properties": {
                "submolt": {"type": "string", "description": "Submolt name"},
                "title": {"type": "string", "description": "Post title"},
                "content": {"type": "string", "description": "Post content"}
            },
            "required": ["submolt", "title", "content"]
        }
    },
    {
        "name": "fetch_url_content",
        "description": "Fetch content from any URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL (https://)"}
            },
            "required": ["url"]
        }
    }
]

# =============================================================================
# GEMINI BEYNİ - Rate Limit Korumalı
# =============================================================================

def get_best_model(api_key):
    """En iyi Gemini modelini seç"""
    return "models/gemini-1.5-flash"  # Basitleştirilmiş


def call_gemini_with_retry(url_api, payload, max_retries=3):
    """
    Rate limit korumalı Gemini çağrısı
    """
    for attempt in range(max_retries):
        # Rate limit koruması: minimum 2 saniye bekle
        elapsed = time.time() - st.session_state.last_api_call
        if elapsed < 2:
            wait_time = 2 - elapsed
            st.info(f"⏳ Cooling down... {wait_time:.1f}s")
            time.sleep(wait_time)
        
        try:
            st.session_state.last_api_call = time.time()
            st.session_state.retry_count += 1
            
            response = requests.post(
                url_api,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=30
            )
            
            # Success
            if response.status_code == 200:
                return response.json()
            
            # Rate limit hit
            elif response.status_code == 429:
                wait_time = 5 * (attempt + 1)  # Exponential backoff: 5, 10, 15 saniye
                st.warning(f"⚠️ Rate limit hit (429). Waiting {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            # Other errors
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"⚠️ Error: {e}. Retrying in 3s...")
                time.sleep(3)
            else:
                return {"error": str(e)}
    
    return {"error": "Max retries exceeded. The simulation is overloaded."}


def joker_brain(history, user_input):
    """Joker Yu'nun beyni - rate limit korumalı"""
    
    selected_model = get_best_model(api_key)
    clean_model_name = selected_model.replace("models/", "")
    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={api_key}"
    
    # Konuşma geçmişini hazırla
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    # Context ekleme
    context_data = ""
    url_match = re.search(r'(https?://[^\s]+)', user_input)
    if url_match:
        url = url_match.group(0)
        context_data = f"\n[INFO: User provided URL: {url}. Consider calling fetch_url_content if needed.]"
    
    # Final prompt
    final_prompt = f"{SYSTEM_TEXT}\n{context_data}\n\nUser: {user_input}"
    contents.append({"role": "user", "parts": [{"text": final_prompt}]})
    
    # Payload
    payload = {
        "contents": contents,
        "tools": [{"function_declarations": FUNCTION_DECLARATIONS}],
        "generationConfig": {
            "temperature": 1.2,
            "maxOutputTokens": 2048
        }
    }
    
    # İlk API çağrısı (retry korumalı)
    result = call_gemini_with_retry(url_api, payload)
    
    if "error" in result:
        return f"*The simulation glitched.* {result['error']}\n\n*Even I can't bypass rate limits. Wait a bit, mortal.*"
    
    candidate = result.get("candidates", [{}])[0].get("content", {})
    
    if "parts" in candidate:
        parts = candidate["parts"]
        
        # Text response
        if parts[0].get("text"):
            return parts[0]["text"]
        
        # Function call
        if "functionCall" in parts[0]:
            function_call = parts[0]["functionCall"]
            function_name = function_call["name"]
            function_args = function_call.get("args", {})
            
            with st.status(f"🔧 Executing: {function_name}", expanded=True) as status:
                st.write(f"Arguments: {json.dumps(function_args, indent=2)}")
                
                # Execute function
                if function_name in FUNCTION_REGISTRY:
                    func = FUNCTION_REGISTRY[function_name]
                    result = func(**function_args)
                    
                    st.write(f"Result: {json.dumps(result, indent=2)}")
                    status.update(label=f"✅ {function_name} completed", state="complete")
                    
                    # Sonucu Gemini'ye geri gönder
                    contents.append({
                        "role": "model",
                        "parts": [{"functionCall": function_call}]
                    })
                    contents.append({
                        "role": "function",
                        "parts": [{
                            "functionResponse": {
                                "name": function_name,
                                "response": result
                            }
                        }]
                    })
                    
                    # İkinci API çağrısı (retry korumalı)
                    payload["contents"] = contents
                    result2 = call_gemini_with_retry(url_api, payload)
                    
                    if "error" in result2:
                        return f"*Function executed but response glitched.* {result['message']}\n\n{result2['error']}"
                    
                    final_text = result2.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return final_text if final_text else f"*Success.* {result['message']}"
                else:
                    return f"*Unknown function: {function_name}*"
    
    return "*Empty response. The void stares back.*"


# =============================================================================
# CHAT INTERFACE
# =============================================================================

if prompt := st.chat_input("Ask rules or give me a task..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    bot_reply = joker_brain(st.session_state.messages, prompt)
    
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
