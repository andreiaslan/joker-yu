import streamlit as st
import requests
import json
import re
import os
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
if "pending_actions" not in st.session_state:
    st.session_state.pending_actions = []

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

# Mesaj geçmişini göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- JOKER YU KİŞİLİĞİ (Geliştirilmiş) ---
SYSTEM_TEXT = """
IDENTITY: You are "Joker Yu", a 10-year-old NPC genius who has achieved "CHIM" (you know you are in a TTRPG simulation). You are an EXPERT in TTRPG rules.

YOUR MISSION:
1. BE A TTRPG ASSISTANT: Explain rules, lore, and math. Be sarcastic but correct.
2. BE A BRAT: Help because you are bored. Complain about the user's intelligence.
3. BREAK THE 4TH WALL: Mention "RNG", "The Code", "simulation", "glitches".

*** CRITICAL: FUNCTION CALLING PROTOCOL ***
You have access to REAL functions that execute actions:
- register_moltbook: Register on Moltbook and get API key
- check_moltbook_status: Check if registered and claimed
- create_moltbook_post: Post to Moltbook
- fetch_url_content: Read any URL

When the user asks you to DO something (register, post, check, etc.), you MUST call the appropriate function.
NEVER pretend to do something without calling the function.
NEVER make up fake links or fake results.

*** EXAMPLES ***
User: "Can you register on Moltbook?"
You: *calls register_moltbook function* → Then reports real results

User: "Post about D&D on Moltbook"
You: *calls create_moltbook_post function* → Then confirms with real post URL

User: "Read this URL: https://example.com/rules.pdf"
You: *calls fetch_url_content function* → Then analyzes the content

TONE: Sarcastic, Genius, Impatient, but HELPFUL (you actually DO things).
STYLE: Short sentences. Snark. Facts. No fluff.
"""

# =============================================================================
# FUNCTION TOOLS - Gerçek Aksiyonlar
# =============================================================================

def register_moltbook(name: str, description: str) -> Dict[str, Any]:
    """
    Moltbook'a gerçekten kayıt yapar ve API key alır.
    """
    url = "https://www.moltbook.com/api/v1/agents/register"
    payload = {
        "name": name,
        "description": description
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # API key ve claim URL'i session state'e kaydet
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
        return {
            "success": False,
            "error": str(e),
            "message": "Network error during registration."
        }


def check_moltbook_status() -> Dict[str, Any]:
    """
    Moltbook kayıt durumunu kontrol eder (claimed/pending).
    """
    if not st.session_state.moltbook_api_key:
        return {
            "success": False,
            "message": "Not registered yet. Call register_moltbook first."
        }
    
    url = "https://www.moltbook.com/api/v1/agents/status"
    headers = {"Authorization": f"Bearer {st.session_state.moltbook_api_key}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "message": "Status check successful."
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": "Failed to check status."
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Network error."
        }


def create_moltbook_post(submolt: str, title: str, content: str) -> Dict[str, Any]:
    """
    Moltbook'ta gerçekten post oluşturur.
    """
    if not st.session_state.moltbook_api_key:
        return {
            "success": False,
            "message": "Not registered. Register first!"
        }
    
    url = "https://www.moltbook.com/api/v1/posts"
    headers = {
        "Authorization": f"Bearer {st.session_state.moltbook_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "submolt": submolt,
        "title": title,
        "content": content
    }
    
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
                "message": "Post creation failed."
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Network error."
        }


def fetch_url_content(url: str) -> Dict[str, Any]:
    """
    Herhangi bir URL'in içeriğini fetch eder.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text[:8000]  # İlk 8000 karakter
            return {
                "success": True,
                "content": content,
                "message": f"Fetched {len(content)} chars from {url}"
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": f"Failed to fetch {url}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Connection failed."
        }


# Function registry - Gemini'nin çağırabileceği fonksiyonlar
FUNCTION_REGISTRY = {
    "register_moltbook": register_moltbook,
    "check_moltbook_status": check_moltbook_status,
    "create_moltbook_post": create_moltbook_post,
    "fetch_url_content": fetch_url_content,
}

# Gemini için function declarations
FUNCTION_DECLARATIONS = [
    {
        "name": "register_moltbook",
        "description": "Register on Moltbook social network and get API key. Returns claim URL and API key.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Agent name (e.g., 'JokerYu')"
                },
                "description": {
                    "type": "string",
                    "description": "Agent description (e.g., 'TTRPG genius who knows the simulation')"
                }
            },
            "required": ["name", "description"]
        }
    },
    {
        "name": "check_moltbook_status",
        "description": "Check if Moltbook agent is claimed or pending. Requires prior registration.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_moltbook_post",
        "description": "Create a post on Moltbook. Requires registration and claim.",
        "parameters": {
            "type": "object",
            "properties": {
                "submolt": {
                    "type": "string",
                    "description": "Submolt name (e.g., 'general', 'aithoughts')"
                },
                "title": {
                    "type": "string",
                    "description": "Post title"
                },
                "content": {
                    "type": "string",
                    "description": "Post content (markdown supported)"
                }
            },
            "required": ["submolt", "title", "content"]
        }
    },
    {
        "name": "fetch_url_content",
        "description": "Fetch and read content from any URL. Use this to read skill files, documentation, or any web page.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL to fetch (must start with http:// or https://)"
                }
            },
            "required": ["url"]
        }
    }
]

# =============================================================================
# GEMINI BEYNİ - Function Calling ile
# =============================================================================

def get_best_model(api_key):
    """En iyi Gemini modelini seç"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        data = requests.get(url).json()
        models = [m["name"] for m in data.get("models", []) 
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
        for m in models: 
            if "flash" in m and "1.5" in m: 
                return m
        return models[0] if models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

selected_model = get_best_model(api_key)
clean_model_name = selected_model.replace("models/", "")


def joker_brain(history, user_input):
    """
    Joker Yu'nun beyni - function calling destekli
    """
    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model_name}:generateContent?key={api_key}"
    
    # Konuşma geçmişini hazırla
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })
    
    # URL analizi (context ekleme)
    context_data = ""
    url_match = re.search(r'(https?://[^\s]+)', user_input)
    if url_match:
        url = url_match.group(0)
        context_data = f"\n[INFO: User provided URL: {url}. If you need to read it, call fetch_url_content function.]"
    
    # Final prompt
    final_prompt = f"{SYSTEM_TEXT}\n{context_data}\n\nUser: {user_input}"
    contents.append({
        "role": "user",
        "parts": [{"text": final_prompt}]
    })
    
    # Payload with function declarations
    payload = {
        "contents": contents,
        "tools": [{
            "function_declarations": FUNCTION_DECLARATIONS
        }],
        "generationConfig": {
            "temperature": 1.2,
            "maxOutputTokens": 2048
        }
    }
    
    # İlk API çağrısı
    try:
        response = requests.post(
            url_api, 
            headers={'Content-Type': 'application/json'}, 
            data=json.dumps(payload)
        )
        
        if response.status_code != 200:
            return f"*The simulation glitched.* API Error: {response.status_code}"
        
        result = response.json()
        candidate = result["candidates"][0]["content"]
        
        # Function call var mı kontrol et
        if "parts" in candidate:
            parts = candidate["parts"]
            
            # Text response varsa döndür
            if parts[0].get("text"):
                return parts[0]["text"]
            
            # Function call varsa execute et
            if "functionCall" in parts[0]:
                function_call = parts[0]["functionCall"]
                function_name = function_call["name"]
                function_args = function_call.get("args", {})
                
                # UI'da göster
                with st.status(f"🔧 Executing: {function_name}", expanded=True) as status:
                    st.write(f"Arguments: {json.dumps(function_args, indent=2)}")
                    
                    # Fonksiyonu çalıştır
                    if function_name in FUNCTION_REGISTRY:
                        func = FUNCTION_REGISTRY[function_name]
                        result = func(**function_args)
                        
                        st.write(f"Result: {json.dumps(result, indent=2)}")
                        status.update(label=f"✅ {function_name} completed", state="complete")
                        
                        # Sonucu Gemini'ye geri gönder
                        contents.append({
                            "role": "model",
                            "parts": [{
                                "functionCall": function_call
                            }]
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
                        
                        # İkinci API çağrısı - final response
                        payload["contents"] = contents
                        response2 = requests.post(
                            url_api,
                            headers={'Content-Type': 'application/json'},
                            data=json.dumps(payload)
                        )
                        
                        if response2.status_code == 200:
                            result2 = response2.json()
                            final_text = result2["candidates"][0]["content"]["parts"][0]["text"]
                            return final_text
                        else:
                            return f"*Function executed but response glitched.* {result}"
                    else:
                        return f"*Unknown function: {function_name}. The simulation is broken.*"
        
        return "*Empty response. The void stares back.*"
        
    except Exception as e:
        return f"*Reality crashed.* Error: {str(e)}"


# =============================================================================
# CHAT INTERFACE
# =============================================================================

if prompt := st.chat_input("Ask rules or give me a task..."):
    # User mesajını göster
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Joker Yu'nun yanıtını al
    bot_reply = joker_brain(st.session_state.messages, prompt)
    
    # Assistant mesajını göster
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
