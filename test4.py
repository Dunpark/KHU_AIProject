# Update3 - 되묻기 기능 탑재

import streamlit as st
import openai
import requests
import json
import base64

# ▒▒▒ 1. API 키 로드 및 클라이언트 설정 ▒▒▒
openai_api_key = st.secrets["OPENAI_API_KEY"]
spotify_id = st.secrets["SPOTIFY_CLIENT_ID"]
spotify_secret = st.secrets["SPOTIFY_CLIENT_SECRET"]
youtube_key = st.secrets["YOUTUBE_API_KEY"]
openai_client = openai.OpenAI(api_key=openai_api_key)

# ▒▒▒ 2. 페이지 설정 ▒▒▒
st.set_page_config(
    page_title="음악 추천기",
    page_icon="🎵",
    layout="centered"
)

# ▒▒▒ 3. 배경 이미지 적용 (Base64 방식 반복 스타일) ▒▒▒
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg_repeat_scroll(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-repeat: repeat-y;
        background-size: cover;
        background-position: center top;
        background-attachment: scroll;
        background-color: transparent;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_png_as_page_bg_repeat_scroll('background.png')

# ▒▒▒ 4. 폰트 및 UI 스타일 적용 (Jua 폰트 전체 적용) ▒▒▒
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
    * { font-family: 'Jua', sans-serif !important; }
    html, body, [class*="css"] {
        font-family: 'Jua', sans-serif !important;
        font-size: 20px !important;
        color: #091747 !important;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        padding: 10px;
    }
    .stSelectbox > div {
        border-radius: 10px;
        padding: 10px;
    }
    .stButton > button {
        background-color: #B4A7FF;
        color: white;
        padding: 10px 24px;
        font-size: 16px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ▒▒▒ 5. 사용자 입력 UI ▒▒▒
st.title("🎵 AI 기반 음악 추천 웹앱")

emotion = st.text_input("당신의 감정은?")
situation = st.text_input("당신의 현재 상황은?")
genre = st.selectbox("선호 장르", ["상관없음", "팝", "재즈", "힙합", "EDM"])
country = st.selectbox("듣고 싶은 언어/국가", ["상관없음", "한국", "미국", "일본"])

# ▒▒▒ 6. 상태 관리용 SessionState 초기화 ▒▒▒
if 'additional_question' not in st.session_state:
    st.session_state.additional_question = None
if 'additional_answer' not in st.session_state:
    st.session_state.additional_answer = None
if 'final_result' not in st.session_state:
    st.session_state.final_result = None

# ▒▒▒ 7. 1단계: 추가 질문 생성 ▒▒▒
if st.button("🎧 음악 추천 받기"):

    st.session_state.additional_answer = None
    st.session_state.final_result = None

    with st.spinner("추가 질문 생성 중..."):

        user_msg = f"""
        아래 사용자 입력을 참고하여, 음악 추천을 더욱 정교하게 하기 위해 추가 질문 1개를 작성해 주세요:

        - 감정: {emotion}
        - 상황: {situation}
        - 장르: {genre}
        - 국가: {country}

        요구사항:
        - 질문은 간결하게 1문장으로 작성
        - 반드시 질문문장만 출력 (다른 문장, 설명, 따옴표 불필요)
        """

        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 AI 음악 큐레이터야. 추가 맞춤형 질문을 생성해줘."},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.7
            )
            st.session_state.additional_question = response.choices[0].message.content.strip()

        except Exception as e:
            st.error(f"추가 질문 생성 실패: {e}")

# ▒▒▒ 8. 2단계: 사용자에게 추가 질문 제시 ▒▒▒
if st.session_state.additional_question and st.session_state.additional_answer is None:
    st.write("🎯 **추가 질문:**")
    st.markdown(f"> {st.session_state.additional_question}")
    additional_answer = st.text_input("이 질문에 답해주세요:")

    if st.button("✅ 최종 추천 받기"):
        st.session_state.additional_answer = additional_answer

# ▒▒▒ 9. 3단계: 최종 GPT 추천 ▒▒▒
if st.session_state.additional_answer and st.session_state.final_result is None:

    with st.spinner("최종 음악 추천을 받고 있습니다..."):

        final_user_msg = f"""
        사용자 입력 + 추가 답변을 기반으로 최종 음악 추천을 진행합니다:

        - 감정: {emotion}
        - 상황: {situation}
        - 장르: {genre}
        - 국가: {country}
        - 추가 정보: {st.session_state.additional_answer}

        요구사항:
        - 한국/일본/미국 음악 추천
        - 시대/언어/국가 다양성 반영
        - 각 곡의 소개 및 추천 이유 포함
        - 반드시 아래 JSON 형식만 응답:

        [
        {{
            "title": "곡 제목",
            "artist": "아티스트",
            "description": "소개와 추천 이유",
            "spotify_query": "Spotify 검색용 키워드",
            "youtube_query": "YouTube 검색용 키워드"
        }},
        ...
        ]
        """

        try:
            gpt_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 한국, 일본, 미국 음악을 추천하는 GPT 음악 큐레이터다. JSON만 출력한다."},
                    {"role": "user", "content": final_user_msg}
                ],
                temperature=0.8
            )
            reply_text = gpt_response.choices[0].message.content
            st.session_state.final_result = json.loads(reply_text)

        except Exception as e:
            st.error(f"최종 추천 실패: {e}")
            st.stop()

# ▒▒▒ 10. 최종 결과 출력 및 API 연동 ▒▒▒
if st.session_state.final_result:

    def get_spotify_token():
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(spotify_id, spotify_secret)
        )
        return res.json().get("access_token")

    token = get_spotify_token()

    for music in st.session_state.final_result:
        st.markdown("### 🎵 " + music['title'] + " - " + music['artist'])
        st.markdown("📝 " + music['description'])

        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get("https://api.spotify.com/v1/search", headers=headers, params={
            "q": music["spotify_query"],
            "type": "track",
            "limit": 1
        })
        items = res.json().get("tracks", {}).get("items", [])
        if items:
            img = items[0]['album']['images'][0]['url']
            st.image(img, width=250)
            st.markdown(f"[🎧 Spotify에서 듣기]({items[0]['external_urls']['spotify']})")
        else:
            st.warning("🎵 Spotify 검색 결과 없음")

        yt = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet",
            "q": music["youtube_query"],
            "key": youtube_key,
            "type": "video",
            "maxResults": 1
        }).json()
        vids = yt.get("items", [])
        if vids:
            vid_id = vids[0]["id"]["videoId"]
            st.video(f"https://www.youtube.com/watch?v={vid_id}")
        else:
            st.warning("📺 YouTube 검색 결과 없음")

        st.divider()
