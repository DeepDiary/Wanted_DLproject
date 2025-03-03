import streamlit as st
import requests
from PIL import Image
import io

# FastAPI 서버 주소: 상황에 맞춰 바꿔주세요
API_URL = "http://localhost:8031"

st.set_page_config(page_title="Deep Diary", layout="centered")

# 세션 스테이트 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def add_message(role, content):
    """챗 메시지를 session_state에 저장"""
    st.session_state.chat_history.append({"role": role, "content": content})

# --------------------------------
#   상단 영역: 이미지 업로드
# --------------------------------
st.title("Deep Diary")

uploaded_file = st.file_uploader("오늘의 사진을 업로드해주세요", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption=None, use_column_width=True)

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    files = {'file': ('uploaded_image.png', img_bytes, 'image/png')}
    response = requests.post(f"{API_URL}/generate_caption", files=files)

    if response.status_code != 200:
        st.error("이미지 캡션 생성 실패: " + response.text)

# --------------------------------
#   "일기 쓰기 시작" 버튼 (메인영역)
# --------------------------------
if st.button("일기 쓰기 시작"):
    resp = requests.get(f"{API_URL}/initial_question")
    if resp.status_code == 200:
        question = resp.json().get("question", "")
        add_message("assistant", question)
    else:
        st.error("첫 번째 질문 가져오기 실패: " + resp.text)

# --------------------------------
#   사용자 채팅 입력
# --------------------------------
user_input = st.chat_input("답변을 입력해보세요")
if user_input:
    # 1) 사용자 메시지 세션에 추가
    add_message("user", user_input)
    # 2) FastAPI에 후속 질문 요청
    resp = requests.post(f"{API_URL}/followup_question", json={"user_answer": user_input})
    if resp.status_code == 200:
        data = resp.json()
        emotion = data["emotion"]
        next_q = data["followup_question"]
        # 감정 + 후속 질문을 하나의 메시지로
        answer_text = f"감정: {emotion}\n\n{next_q}"
        add_message("assistant", answer_text)
    else:
        add_message("assistant", f"오류가 발생했습니다: {resp.text}")

# --------------------------------
#  사이드바: "일기 마무리하기" & "트로트 추천" 버튼
# --------------------------------
with st.sidebar:
    st.markdown("## 메뉴")
    
    if st.button("일기 마무리하기"):
        resp = requests.get(f"{API_URL}/summarize_conversation")
        if resp.status_code == 200:
            data = resp.json()
            diary_summary = data["diary_summary"]
            final_emotion = data["final_emotion"]
            summary_text = f"**일기 요약**: {diary_summary}\n\n**최종 감정**: {final_emotion}"
            add_message("assistant", summary_text)
        else:
            st.error("일기 요약 요청 실패: " + resp.text)

    if st.button("오늘의 트로트 추천받기"):
        with st.spinner("트로트 추천을 불러오는 중..."):
            resp = requests.get(f"{API_URL}/recommend_song")
        if resp.status_code == 200:
            data = resp.json()
            recommended_song = data.get("recommended_song", {})
            title = recommended_song.get("title", "")
            artist = recommended_song.get("artist", "")
            lyrics = recommended_song.get("lyrics", "")

            # 보기 좋게 출력하기: Markdown과 이모지 활용
            text = f"""
            ### 🎶 **추천 곡**: {title}
            **가수**: {artist}

            **가사**:
            {lyrics}
            """

            # 1) 그냥 st.write()나 st.markdown()으로 즉시 출력하는 방법:
            #    st.markdown(text)

            # 2) 대화형 챗봇 메시지에 추가하는 구조라면:
            add_message("assistant", text)  
        else:
            st.error("트로트 추천 실패: " + resp.text)


# --------------------------------
#   대화 내역 표시 (마지막)
# --------------------------------
for msg in st.session_state.chat_history:
    if msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])
    else:
        with st.chat_message("user"):
            st.write(msg["content"])
