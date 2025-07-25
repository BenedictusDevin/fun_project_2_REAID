import streamlit as st
import requests
import json
import PyPDF2
import re

# --- PAGE CONFIG ---
st.set_page_config("🎧 AI Copilot", layout="wide")

# --- SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.name = ""
    st.session_state.age = ""
    st.session_state.api_key = ""
    st.session_state.history = {}

# --- FUNGSI UNTUK API CHAT ---
def get_ai_response(messages_payload, model_name, api_key):
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            data=json.dumps({
                "model": model_name,
                "messages": messages_payload,
            })
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
        return None

# --- HALAMAN LOGIN ---
if not st.session_state.authenticated:
    st.title("🚀 Selamat Datang di AI Copilot")
    with st.form("login_form"):
        nama = st.text_input("Nama Lengkap")
        umur = st.text_input("Umur")
        api_key = st.text_input("OpenRouter API Key", type="password")
        submit = st.form_submit_button("Mulai Copilot")

    if submit:
        if not nama or not umur or not api_key:
            st.warning("❗ Semua kolom wajib diisi.")
        elif not nama.replace(" ", "").isalpha():
            st.error("❗ Nama hanya boleh terdiri dari huruf dan spasi.")
        elif not umur.isdigit() or int(umur) <= 0:
            st.error("❗ Umur harus berupa angka positif.")
        elif not re.match(r"^sk-or-v1-[a-f0-9]{64}$", api_key.strip()):
            st.error("❗ Format API Key tidak valid. Harus seperti: sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        else:
            st.session_state.authenticated = True
            st.session_state.name = nama.strip()
            st.session_state.age = umur.strip()
            st.session_state.api_key = api_key.strip()
            st.success("✅ Login berhasil! Selamat datang, " + nama)

else:
    # --- HALAMAN UTAMA ---
    st.sidebar.title("👤 Selamat Datang MyBrodies!")
    st.sidebar.markdown(f"**🧑 Nama:** {st.session_state.name}")
    st.sidebar.markdown(f"**🎂 Umur:** {st.session_state.age}")
    st.sidebar.image("https://api.dicebear.com/7.x/fun-emoji/svg?seed=" + st.session_state.name, width=80)
    st.sidebar.markdown("---")
    st.sidebar.markdown("<span style='font-size:10px;'>🛠️ Made in Kalimalang by Devin</span>", unsafe_allow_html=True)

    MODEL_LIST = {
        "Mistral 7B (Free)": "mistralai/mistral-7b-instruct:free",
        "Llama 3 8B (Free)": "meta-llama/llama-3-8b-instruct:free",
        "Claude 3.5 Sonnet": "anthropic/claude-3.5-sonnet",
        "Google Gemini Pro": "google/gemini-pro"
    }
    model_name = st.sidebar.selectbox("🔍 Pilih Model AI", options=list(MODEL_LIST.keys()))
    model_id = MODEL_LIST[model_name]

    tab1, tab2, tab3 = st.tabs(["💬 NeoChat", "📁 InsightFile", "📜 Riwayat Chat"])

    # --- TAB 1: CHAT ---
    with tab1:
        st.header("💬 NeoChat - Asisten AI Kamu")
        if st.session_state.name not in st.session_state.history:
            st.session_state.history[st.session_state.name] = []

        for msg in st.session_state.history[st.session_state.name]:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])

        if prompt := st.chat_input("Tulis pertanyaanmu di sini..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.history[st.session_state.name].append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner("Sedang menjawab..."):
                    response = get_ai_response(
                        messages_payload=st.session_state.history[st.session_state.name],
                        model_name=model_id,
                        api_key=st.session_state.api_key
                    )
                    if response:
                        st.markdown(response)
                        st.session_state.history[st.session_state.name].append({"role": "assistant", "content": response})

    # --- TAB 2: FILE ANALYZER ---
    with tab2:
        st.header("📁 InsightFile - Analis Dokumen")
        uploaded_file = st.file_uploader("Unggah dokumen (.txt atau .pdf)", type=["pdf", "txt"])

        if uploaded_file:
            file_text = ""

            # --- Baca PDF ---
            if uploaded_file.type == "application/pdf":
                try:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text:
                            file_text += f"\n\n--- Halaman {page_num + 1} ---\n{text}"
                except Exception as e:
                    st.error(f"Gagal membaca PDF: {e}")

            # --- Baca TXT ---
            elif uploaded_file.type == "text/plain":
                try:
                    file_text = uploaded_file.read().decode("utf-8", errors="ignore")
                except Exception as e:
                    st.error(f"Gagal membaca file TXT: {e}")

            # --- Tampilkan isi file ---
            if file_text.strip():
                st.subheader("📝 Isi Dokumen")
                st.text_area("Konten Dokumen", file_text, height=300)

                # --- Analisis oleh AI ---
                if st.button("🔍 Ringkas dan Analisis"):
                    with st.spinner("AI sedang membaca dan menganalisis..."):
                        result = get_ai_response(
                            messages_payload=[
                                {
                                    "role": "user",
                                    "content": f"Tolong ringkas dan analisis isi dokumen berikut secara profesional dalam bahasa indonesia:\n\n{file_text}"
                                }
                            ],
                            model_name=model_id,
                            api_key=st.session_state.api_key
                        )
                        st.success("✅ Hasil Analisis AI:")
                        st.markdown(result)
            else:
                st.warning("❗ Tidak ada teks yang bisa dibaca dari file ini.")

    # --- TAB 3: HISTORY ---
    with tab3:
        st.header("📜 Riwayat Chat per User")
        for user, logs in st.session_state.history.items():
            with st.expander(f"💬 {user}"):
                for chat in logs:
                    role = "🧑" if chat['role'] == "user" else "🤖"
                    st.markdown(f"{role} **{chat['role'].capitalize()}**: {chat['content']}")
