import streamlit as st
from openai import OpenAI
import time

st.set_page_config(page_title="💊 영양제 안전 분석 AI", layout="wide")

st.markdown("""
<style>
[data-testid="stChatMessage"] { padding: 12px 16px; border-radius: 12px; }
[data-testid="stSidebar"] { background-color: #f8f9fa; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ 설정")
    api_key = st.text_input(
        "OpenAI API 키",
        type="password",
        placeholder="sk-...",
        help="https://platform.openai.com/api-keys 에서 발급"
    )
    st.divider()
    st.markdown("**사용 예시**")
    st.markdown("- 오메가3 분석해줘")
    st.markdown("- 종근당 칼슘 먹어도 돼?")
    st.markdown("- 심바로드정이랑 같이 먹으면 안 되는 영양제 있어?")
    st.markdown("- 비타민C랑 철분 같이 먹어도 돼?")
    st.divider()
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.rerun()

# Assistant ID 고정
ASSISTANT_ID = "asst_7CST1rzZqiLB1St0kjK7Sj8o"

st.title("💊 영양제 복용 안전 분석 AI")
st.caption("영양제·의약품 이름을 입력하면 성분 분석, 중복 검사, 병용금기를 알려드립니다.")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.session_state.messages.append({
        "role": "assistant",
        "content": "안녕하세요! 영양제 복용 안전 분석 AI입니다 💊\n\n제품명이나 성분명을 입력해 주세요.\n\n**예시:**\n- 오메가3 분석해줘\n- 종근당 칼슘이랑 비타민D 같이 먹어도 돼?\n- 심바로드정 병용금기 알려줘"
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("제품명 또는 성분명을 입력하세요..."):

    if not api_key:
        st.warning("왼쪽 사이드바에 OpenAI API 키를 입력해주세요.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("분석 중..."):
            try:
                client = OpenAI(api_key=api_key)

                # Thread 없으면 새로 생성
                if st.session_state.thread_id is None:
                    thread = client.beta.threads.create()
                    st.session_state.thread_id = thread.id

                # 메시지 추가
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=prompt
                )

                # Assistant 실행
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID
                )

                # 완료 대기
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )

                # 결과 가져오기
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                answer = messages.data[0].content[0].text.value

                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
