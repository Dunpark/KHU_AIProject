## 2차 UI Update + 장르/출력값 조정

import streamlit as st
import openai
import requests
import os
import json
import base64

# ▒▒▒ 1. API 키 로드 및 클라이언트 설정 ▒▒▒
openai_api_key = st.secrets["OPENAI_API_KEY"]
spotify_id = st.secrets["SPOTIFY_CLIENT_ID"]
spotify_secret = st.secrets["SPOTIFY_CLIENT_SECRET"]
youtube_key = st.secrets["YOUTUBE_API_KEY"]
openai_client = openai.OpenAI(api_key=openai_api_key)

# 🔧 추가됨: 페이지 전체 테마 및 UI 초기 설정
st.set_page_config(
    page_title="음악 추천기",
    page_icon="🎵",
    layout="centered",  # 화면 중앙 정렬
    initial_sidebar_state="collapsed"
)

# ▒▒▒ 3. 배경이미지 설정 (Base64 인코딩 방식 활용) ▒▒▒

@st.cache_data  # ✅ 최신 Streamlit 캐시 사용법으로 교체
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

# 배경 적용 (※ 여기에 파일명 맞춰주면 됩니다)
set_png_as_page_bg_repeat_scroll('background.png')


# ▒▒▒ 4. 폰트 적용 (Jua 폰트 적용) ▒▒▒
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');

    * {
        font-family: 'Jua', sans-serif !important;
    }

    html, body, [class*="css"] {
        font-family: 'Jua', sans-serif !important;
        font-size: 20px !important;
        color: #091747 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ▒▒▒ 5. 추가 UI 스타일 적용 (입력창, 셀렉트박스, 버튼 등) ▒▒▒
st.markdown(
    """
    <style>
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

# ▒▒▒ 2. 사용자 입력 UI ▒▒▒
st.title("🎵 AI 기반 음악 추천 웹앱")

# 🔧 추가됨: 입력창 간 넉넉한 여백 확보
st.write("")
st.write("")

emotion = st.text_input("당신의 감정은?")
situation = st.text_input("당신의 현재 상황은?")
genre = st.selectbox("선호 장르", ["상관없음", "팝", "재즈", "힙합", "EDM"])
country = st.selectbox("듣고 싶은 언어/국가", ["상관없음", "한국", "미국", "일본"])

# ▒▒▒ 3. 사용자 입력 구조화 ▒▒▒
user_profile = {
    "emotion": emotion.strip() if emotion else None,
    "situation": situation.strip() if situation else None,
    "genre": genre if genre != "상관없음" else None,
    "country": country if country != "상관없음" else None
}

# ▒▒▒ 4. 추천 실행 버튼 ▒▒▒
if st.button("🎧 음악 추천 받기"):
    with st.spinner("GPT에게 음악을 추천받고, Spotify & YouTube에서 정보를 가져오는 중입니다..."):

        # GPT 프롬프트
        system_msg = (
            "당신은 한국,일본,미국 음악을 추천하는 GPT 기반 뮤직 큐레이터입니다. "
            "절대 말로 설명하지 말고, 오직 JSON 배열만 응답해야 합니다."
        )

        user_msg = f"""
        아래 조건에 따라 음악을 추천해주세요:

        - 감정: {user_profile['emotion']}
        - 상황: {user_profile['situation']}
        - 장르: {user_profile['genre']}
        - 국가 또는 언어: {user_profile['country']}

        요구사항:
        - 시대/언어/국가의 다양성 반영
        - 곡마다 소개와 추천 이유와 포함
        - JSON 이외의 텍스트 출력 금지
        - 출력은 반드시 아래 형식을 따를 것

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

        # GPT 호출 이후 처리
        try:
            gpt_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.8
            )
            reply_text = gpt_response.choices[0].message.content

            # GPT 응답이 문자열(JSON 형식)일 경우 파싱
            if isinstance(reply_text, str):
                gpt_result = json.loads(reply_text)
            else:
                gpt_result = reply_text

        except json.JSONDecodeError as e:
            st.error("❌ GPT 응답을 JSON으로 파싱하지 못했습니다.")
            st.text(reply_text)
            st.stop()
        except Exception as e:
            st.error(f"❌ GPT 호출 중 오류 발생: {e}")
            st.stop()

        # Spotify 토큰 발급
        def get_spotify_token():
            res = requests.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(spotify_id, spotify_secret)
            )
            return res.json().get("access_token")

        token = get_spotify_token()

        # Spotify + YouTube 정보 통합 출력
        for music in gpt_result:
            st.markdown("### 🎵 " + music['title'] + " - " + music['artist'])
            st.markdown("📝 " + music['description'])

            # Spotify 검색
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

            # YouTube 검색
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
