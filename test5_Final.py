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

def set_png_as_page_bg_repeat_scroll(png_file): # 해당 이미지는 직접 인터넷에서 찾아서 다운받음
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
    st.markdown(page_bg_img, unsafe_allow_html=True)    # scroll 기능을 넣으려 하였으나 적용되지 않음

set_png_as_page_bg_repeat_scroll('background.png')

# ▒▒▒ 4. 폰트 및 UI 스타일 적용 (Jua 폰트 전체 적용) ▒▒▒ - ChatGPT로부터 폰트를 추천 받았으나 한국어와 호환되지 않는 지 적용이 안됨 -> 직접 폰트 찾아서 url 대체
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

# ▒▒▒ 6. 상태 관리용 SessionState 초기화 ▒▒▒ -> Streamlit 앱이 새로고침되거나 입력이 바뀌어도 상태 정보가 보존되도록 함
# Streamlit의 세션 상태(st.session_state)에 특정 키가 없을 때, 기본값을 설정해주는 역할
if 'additional_question' not in st.session_state:
    st.session_state.additional_question = None 
if 'additional_answer' not in st.session_state:
    st.session_state.additional_answer = None
if 'final_result' not in st.session_state:
    st.session_state.final_result = None
if 'recommended_songs' not in st.session_state:
    st.session_state.recommended_songs = []

# ▒▒▒ 7. 1단계: 추가 질문 생성 ▒▒▒
if st.button("🎧 음악 추천 받기"):

    st.session_state.additional_answer = None
    st.session_state.final_result = None

    with st.spinner("추가 질문 생성 중..."):
        # ChatGPT에게 입력되는 프롬프트
        user_msg = f"""
        아래 사용자 입력을 참고하여, 음악 추천을 더욱 정교하게 하기 위해 추가 질문 1개를 작성해 주세요

        - 감정: {emotion}
        - 상황: {situation}
        - 장르: {genre}
        - 국가: {country}

        요구사항:
        - 사용자의 감정, 상황, 취향 등을 존중하며 공감하는 말을 먼저 건네주세요.
        - 사용자가 부담 없이 대화할 수 있도록, 마치 친한 친구처럼 자연스럽고 부드럽게 이야기해주세요. 
        - 질문은 간결하게 1문장으로 작성
        """

        try: # GPT의 응답
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 AI 음악 큐레이터야. 추가 맞춤형 질문을 생성해줘."},  # system: GPT에게 정체성과 역할을 부여하는 지시문
                    {"role": "user", "content": user_msg} # user: 사용자의 실제 입력 내용
                ],
                temperature=0.7 # 응답을 더욱 창의적으로 만들어줌 * 높을수록 랜덤 정도 증가 
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

        # 기존 추천곡 중복방지용 리스트 생성
        exclude_list = ", ".join([
            f"{song['title']} by {song['artist']}" 
            for song in st.session_state.recommended_songs
        ]) if st.session_state.recommended_songs else "없음"

        final_user_msg = f"""
        사용자 입력 + 추가 답변을 기반으로 최종 음악 추천을 진행합니다:

        - 감정: {emotion}
        - 상황: {situation}
        - 장르: {genre}
        - 국가: {country}
        - 추가 정보: {st.session_state.additional_answer}
        - 이미 추천된 곡 리스트 (절대 추천 금지): {exclude_list}

        요구사항:
        - 한국/일본/미국 음악 추천
        - 기존 추천 리스트에 있는 곡은 절대 중복 추천하지 말 것
        - 시대/언어/국가 다양성 반영
        - 각 곡의 소개 및 추천 이유 포함 
            - 톤은 전문적이되, 설명은 너무 길거나 어려우면 안 되고, 사용자가 음악을 듣고 싶은 기분이 들도록 감성적인 말투로 표현해주세요. 
        - 반드시 아래 JSON 형식만 응답:

        [
        {{
            "title": "곡 제목",
            "artist": "아티스트",
            "description": "소개와 추천 이유"
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
                    {"role": "system", "content": "너는 한국, 일본, 미국 음악을 추천하는 친절한 음악 큐레이터다. JSON만 출력한다."},
                    {"role": "user", "content": final_user_msg}
                ],
                temperature=0.8 
            )
            reply_text = gpt_response.choices[0].message.content # GPT의 첫 응답에서 텍스트만을 추출한다
            st.session_state.final_result = json.loads(reply_text) # GPT의 JSON string을 python의 딕셔너리를 모아놓은 리스트 형식으로 변환시킨 후 해당 변수에 저장해 나중에 활용할 수 있도록 함

            # 추천결과 누적 기록 (중복방지용)
            for music in st.session_state.final_result:
                st.session_state.recommended_songs.append({
                    "title": music['title'],
                    "artist": music['artist']
                })  # 추천된 곡의 제목과 아티스트를 recommended_songs 상태변수에 저장하여 중복 방지

        except Exception as e:
            st.error(f"최종 추천 실패: {e}")
            st.stop()

# ▒▒▒ 10. 최종 결과 출력 및 API 연동 ▒▒▒
if st.session_state.final_result: # 상태변수에 값이 지정되었을 때 

    def get_spotify_token():
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(spotify_id, spotify_secret)
        )
        return res.json().get("access_token")

    token = get_spotify_token()

    for music in st.session_state.final_result: # final result에 들어 있는 응답들에 대해
        st.markdown("### 🎵 " + music['title'] + " - " + music['artist'])
        st.markdown("📝 " + music['description'])

        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get("https://api.spotify.com/v1/search", headers=headers, params={
            "q": music["spotify_query"], # spotify query에 저장된 응답
            "type": "track",
            "limit": 1 # 상위 검색결과 1개 추출
        }) # Spotify에서 곡을 검색하는 과정
        items = res.json().get("tracks", {}).get("items", []) # Spotify의 응답 파싱
        if items: # 노래가 발견되면
            img = items[0]['album']['images'][0]['url'] # 이미지를 추출
            st.image(img, width=250) # 이미지 디스플레이
            st.markdown(f"[🎧 Spotify에서 듣기]({items[0]['external_urls']['spotify']})")  # spotify에서 듣기
        else:
            st.warning("🎵 Spotify 검색 결과 없음")

        yt = requests.get("https://www.googleapis.com/youtube/v3/search", params={  # 유투브 API기반으로 유투브 영상 불러오기
            "part": "snippet",
            "q": music["youtube_query"],
            "key": youtube_key,
            "type": "video",
            "maxResults": 1 # 상위 검색결과 1개 추출
        }).json()
        vids = yt.get("items", [])
        if vids:
            vid_id = vids[0]["id"]["videoId"]
            st.video(f"https://www.youtube.com/watch?v={vid_id}")
        else:
            st.warning("📺 YouTube 검색 결과 없음")

        # ▒▒▒ 정확도 평가 요청 ▒▒▒
        eval_prompt = f"""
        다음은 사용자의 음악 추천 요청 정보와 추천된 음악의 정보입니다. 아래 평가 기준에 따라 각 항목의 일치도를 판단하세요.

        [평가 목적]
        - 사용자의 감정, 상황, 장르, 국가 선호도와 추천된 곡이 얼마나 잘 맞는지 평가합니다.
        - 평가 결과는 정성적(높음/중간/낮음)과 정량적(0~100점)으로 제공합니다.
        - 출력은 반드시 JSON 형식만 출력하세요.

        [평가 기준 설명]
        - 감정(emotion_match): 곡의 분위기나 설명이 사용자의 감정과 잘 어울리는지 판단 (예: 슬픈 감정 ↔ 감성적 발라드)
        - 상황(situation_match): 곡이 사용자의 상황에 적합한 테마나 분위기를 가지는지 판단 (예: 출근길 ↔ 에너지 있는 음악)
        - 장르(genre_match): 사용자의 선호 장르와 곡의 실제 장르 또는 스타일이 유사한지 판단 (명확하지 않으면 설명에서 유추)
        - 국가(country_match): 아티스트 국적, 음악 스타일이 사용자의 선호 국가와 일치하는지 판단

        [일치도 기준]
        - "높음": 매우 잘 부합함, 확실한 일치
        - "중간": 어느 정도 부합하지만 일부 차이 있음
        - "낮음": 관련성이 약하거나 거의 부합하지 않음

        [총점 산출 기준]
        - 각 항목에 대해 높음=25점, 중간=15점, 낮음=5점으로 환산하여 총합(100점 만점)을 계산하세요.

        [사용자 정보]
        감정: {emotion}
        상황: {situation}
        장르: {genre}
        국가: {country}
        추가 정보: {st.session_state.additional_answer}

        [추천 곡 정보]
        제목: {music['title']}
        아티스트: {music['artist']}
        설명: {music['description']}

        [출력 형식 예시]
        {{
            "emotion_match": "중간",
            "situation_match": "높음",
            "genre_match": "높음",
            "country_match": "낮음",
            "total_score": 65
        }}

        위 형식 그대로, 반드시 JSON만 응답하세요. 설명이나 다른 문장은 절대 포함하지 마세요.
        """

        try:
            eval_result = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "일치도를 평가하는 시스템입니다. JSON으로만 응답하세요."},
                    {"role": "user", "content": eval_prompt}
                ]
            )
            match_result = json.loads(eval_result.choices[0].message.content)
            st.success(f"🎯 일치도: {match_result['total_score']}%")
            with st.expander("🔎 세부 평가 보기"):
                st.write(f"감정: {match_result['emotion_match']}")
                st.write(f"상황: {match_result['situation_match']}")
                st.write(f"장르: {match_result['genre_match']}")
                st.write(f"국가: {match_result['country_match']}")
        except Exception as e:
            st.warning(f"일치도 평가 실패: {e}")

        st.divider()
