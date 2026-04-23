import streamlit as st
import requests
from datetime import datetime
import json

st.set_page_config(page_title="Chat Assistant", layout="wide")

# Internal defaults (not editable in UI)
DEFAULT_WEBHOOK_URL = "https://swapnilbanduke.app.n8n.cloud/webhook/ea07e88b-7ad0-45b6-93ea-1313afcb312f"
DEFAULT_TIMEOUT = 500

# --- Sidebar / Settings -------------------------------------------------
with st.sidebar:
    st.header("Settings")
    st.info("Webhook is configured internally and not editable here.")
    max_messages = st.number_input("Max messages to keep", min_value=5, max_value=500, value=200)
    compact_view = st.checkbox("Compact view (less spacing)", value=False)
    show_timestamps = st.checkbox("Show timestamps", value=True)
    if st.button("Clear conversation"):
        st.session_state.messages = []
    # Export button directly available (no extra click required)
    data = json.dumps(st.session_state.get("messages", []), indent=2)
    st.download_button("Export conversation", data, file_name="conversation.json", mime="application/json")

# --- Session state init -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Page header --------------------------------------------------------
col1, col2 = st.columns([8, 2])
with col1:
    st.write("")
with col2:
    st.write("")

st.markdown("---")

# Simple header (no custom CSS)
st.title("💬 Chat Assistant")
st.caption("A lightweight Streamlit chat client that posts messages to your webhook and shows replies.")

# --- Helper to render a message -----------------------------------------
def render_message(msg):
    role = msg.get("role", "user")
    content = msg.get("content", "")
    ts = msg.get("ts")
    ts_str = None
    if show_timestamps and ts:
        if isinstance(ts, (int, float)):
            ts_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = str(ts)

    # Use Streamlit chat components (pure Python)
    try:
        with st.chat_message(role):
            st.write(content)
            if ts_str:
                st.caption(ts_str)
    except Exception:
        # fallback for older Streamlit versions
        label = role.title()
        st.write(f"**{label}**: {content}")
        if ts_str:
            st.write(ts_str)


# --- Display existing messages ------------------------------------------
chat_placeholder = st.container()
with chat_placeholder:
    for message in st.session_state.messages:
        render_message(message)

# (No raw HTML wrappers used)

# --- Input and send -----------------------------------------------
prompt = st.chat_input("Type your message and press Enter")
if prompt:
    user_msg = {"role": "user", "content": prompt, "ts": datetime.now().timestamp()}
    st.session_state.messages.append(user_msg)

    # Optimistic render of user's message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call webhook (using internal defaults)
    with st.spinner("Thinking..."):
        try:
            response = requests.post(DEFAULT_WEBHOOK_URL, json={"message": prompt}, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except Exception as e:
            ai_response = f"Error contacting webhook: {e}"
            st.session_state.messages.append({"role": "assistant", "content": ai_response, "ts": datetime.now().timestamp()})
            with st.chat_message("assistant"):
                st.markdown(ai_response)
        else:
            # Support a few payload shapes that previous app handled
            if isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict) and "output" in payload[0]:
                ai_response = payload[0]["output"]
            elif isinstance(payload, dict) and "output" in payload:
                ai_response = payload["output"]
            else:
                # If payload is plain text or other shapes, pretty print it
                if isinstance(payload, (str, int, float)):
                    ai_response = str(payload)
                else:
                    ai_response = json.dumps(payload, indent=2)

            st.session_state.messages.append({"role": "assistant", "content": ai_response, "ts": datetime.now().timestamp()})
            with st.chat_message("assistant"):
                st.markdown(ai_response)

    # Trim conversation history to last N messages if needed
    if len(st.session_state.messages) > max_messages:
        st.session_state.messages = st.session_state.messages[-max_messages:]

# --- Footer / small help -----------------------------------------------
st.markdown("---")
st.caption("Tip: webhook is configured internally. Use Export to save conversations.")
