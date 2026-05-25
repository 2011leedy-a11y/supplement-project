import streamlit as st
from openai import OpenAI
import time
import re

st.set_page_config(page_title="💊 영양제 안전 분석 AI", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 전체 배경 */
.stApp {
    background: #f7f8fc;
}

/* 면책 배너 */
.disclaimer {
    background: #fffbeb;
    border-left: 4px solid #d4a017;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 0.85rem;
    color: #7a5c00;
    margin-bottom: 16px;
}

/* 헤더 */
.main-header {
    background: linear-gradient(135deg, #5b6fa6, #7b8fc7);
    color: white;
    padding: 24px 32px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(91,111,166,0.15);
}
.main-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
.main-header p  { margin: 6px 0 0; opacity: 0.85; font-size: 0.9rem; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #2c3354 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown { color: #c8cfe8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #e8ecf8 !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: white !important;
    border-radius: 8px !important;
}

/* 버튼 */
.stButton > button {
    background: #4a5a8a !important;
    color: #e8ecf8 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    background: #5b6fa6 !important;
    transform: translateY(-1px) !important;
}

/* 채팅 입력창 */
[data-testid="stChatInput"] {
    border-radius: 12px !important;
    border: 1.5px solid #d0d5e8 !important;
}
</style>
""", unsafe_allow_html=True)

ASSISTANT_ID = "asst_7CST1rzZqiLB1St0kjK7Sj8o"

def remove_citations(text):
    text = re.sub(r'【\d+:\d+†[^】]*】', '', text)
    text = re.sub(r'\[\d+:\d+†[^]]*\]', '', text)
    return text.strip()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.session_state.messages.append({
        "role": "assistant",
        "content": "안녕하세요! 영양제 복용 안전 분석 AI입니다 💊\n\n복용 중인 영양제나 의약품 이름을 알려주시면 성분 중복, 병용금기, 복용법을 분석해드려요.\n\n왼쪽 예시 버튼을 눌러보세요! 😊"
    })

if "example_input" not in st.session_state:
    st.session_state.example_input = ""

with st.sidebar:
    st.markdown("## ⚙️ 설정")
    api_key = st.text_input(
        "OpenAI API 키",
        type="password",
        placeholder="sk-...",
        help="https://platform.openai.com/api-keys 에서 발급"
    )
    if api_key:
        st.success("✅ API Key 입력됨")
    else:
        st.warning("⚠️ API Key를 입력하세요")

    st.markdown("---")
    st.markdown("### 💡 예시 질문")
    st.caption("클릭하면 바로 입력돼요")

    examples = [
        "오메가3 분석해줘",
        "종근당 칼슘 먹어도 돼?",
        "비타민C랑 철분 같이 먹어도 돼?",
        "심바로드정이랑 같이 먹으면 안 되는 영양제 있어?",
        "오메가3랑 비타민D 중복 성분 있어?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.example_input = ex
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.session_state.example_input = ""
        st.session_state.messages.append({
            "role": "assistant",
            "content": "안녕하세요! 영양제 복용 안전 분석 AI입니다 💊\n\n복용 중인 영양제나 의약품 이름을 알려주시면 성분 중복, 병용금기, 복용법을 분석해드려요.\n\n왼쪽 예시 버튼을 눌러보세요! 😊"
        })
        st.rerun()

st.markdown("""
<div class="main-header">
    <h1>💊 영양제 복용 안전 분석 AI</h1>
    <p>영양제·의약품 이름을 입력하면 성분 분석, 중복 검사, 병용금기를 알려드립니다</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
    ⚠️ 본 서비스는 참고용 정보 제공 목적이며, 의료 처방을 대체하지 않습니다.
    실제 복용 결정은 반드시 <strong>의사·약사와 상담</strong>하시기 바랍니다.
</div>
""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def get_ai_response(prompt, api_key):
    client = OpenAI(api_key=api_key)
    if st.session_state.thread_id is None:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user", content=prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )
    while run.status in ["queued", "in_progress"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
    messages_list = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    return remove_citations(messages_list.data[0].content[0].text.value)

if st.session_state.example_input:
    prompt = st.session_state.example_input
    st.session_state.example_input = ""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("분석 중... 잠시만요 💊"):
            try:
                answer = get_ai_response(prompt, api_key)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"오류: {str(e)}")
    st.rerun()

if prompt := st.chat_input("제품명 또는 성분명을 입력하세요..."):
    if not api_key:
        st.warning("왼쪽 사이드바에 OpenAI API 키를 입력해주세요.")
        st.stop()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("분석 중... 잠시만요 💊"):
            try:
                answer = get_ai_response(prompt, api_key)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"오류: {str(e)}")
    st.rerun()
