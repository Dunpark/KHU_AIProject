### 1단계: UI 프레임워크 선정 및 구조 기획

# music_recommender_app.py 또는 ipynb 셀 1

import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="AI 음악 추천 웹앱", page_icon="🎵")

# 제목
st.title("🎵 AI 기반 음악 추천 웹앱")

# 설명
st.markdown("이 앱은 감정, 상황, 장르, 국가를 입력받아 GPT를 활용한 음악 큐레이션을 제공합니다.")

# 사용자 입력 영역
emotion = st.text_input("당신의 현재 감정은 무엇인가요? (예: 행복, 우울, 설렘 등)")
situation = st.text_input("현재 상황을 한 문장으로 설명해 주세요. (예: 밤에 혼자 공부 중)")
genre = st.selectbox("선호하는 음악 장르는?", ["상관없음", "팝", "락", "힙합", "클래식", "재즈", "발라드", "EDM"])
country = st.selectbox("듣고 싶은 국가/언어의 음악은?", ["상관없음", "한국", "미국", "일본", "프랑스", "스페인", "기타"])

# 제출 버튼
if st.button("🎧 추천받기"):
    st.write("추천을 생성 중입니다... (다음 단계에서 GPT 연동 예정)")



### 2단계: 사용자 입력 전처리 및 구조화
# 셀 또는 main 함수 상단에 위치
import json
import streamlit as st

# 사용자 입력
emotion = st.text_input("당신의 현재 감정은 무엇인가요?")
situation = st.text_input("현재 상황을 간단히 설명해주세요.")
genre = st.selectbox("선호하는 음악 장르는?", ["상관없음", "팝", "락", "힙합", "클래식", "재즈", "발라드", "EDM"])
country = st.selectbox("듣고 싶은 국가/언어의 음악은?", ["상관없음", "한국", "미국", "일본", "프랑스", "스페인", "기타"])

# 전처리 함수 정의
def build_user_profile(emotion, situation, genre, country):
    # 빈값 처리
    profile = {
        "emotion": emotion.strip() if emotion else None,
        "situation": situation.strip() if situation else None,
        "genre": genre if genre != "상관없음" else None,
        "country": country if country != "상관없음" else None
    }
    return profile

# 버튼 클릭 시 구조화 출력
if st.button("✅ 입력값 확인 및 구조화"):
    user_profile = build_user_profile(emotion, situation, genre, country)
    
    st.subheader("🎯 GPT에게 전달될 사용자 프로필 (JSON 형식)")
    st.json(user_profile)

    # 이후 GPT API에 이 데이터를 전송하게 됨



# 3단계
import openai
import json
import streamlit as st

# 사용자 입력 예시 (앞 단계에서 받아온 것처럼 가정)
user_profile = {
    "emotion": emotion.strip() if emotion else None,
    "situation": situation.strip() if situation else None,
    "genre": genre if genre != "상관없음" else None,
    "country": country if country != "상관없음" else None
}

# GPT 프롬프트 구성
system_msg = "당신은 전 세계 음악을 추천하는 뮤직 큐레이터입니다."

user_msg = f"""
다음 조건에 맞는 음악 3곡을 추천해주세요.

조건:
- 감정: {user_profile['emotion']}
- 상황: {user_profile['situation']}
- 장르: {user_profile['genre']}
- 국가 또는 언어: {user_profile['country']}

요구 사항:
- 시대적 다양성도 고려
- 가능한 다양한 언어와 문화권 포함
- 출력은 아래 JSON 형식으로 제공

형식:
[
  {{
    "title": "음악 제목",
    "artist": "아티스트",
    "description": "왜 이 곡을 추천하는지 간단 설명",
    "spotify_query": "Spotify에서 검색할 키워드",
    "youtube_query": "YouTube에서 검색할 키워드"
  }},
  ...
]
"""

# GPT 요청 함수
def get_music_recommendation_from_gpt(user_msg):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # 또는 "gpt-4"
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.8
        )

        content = response['choices'][0]['message']['content']
        return json.loads(content)

    except Exception as e:
        st.error(f"GPT API 호출 중 오류 발생: {e}")
        return []

# 버튼 클릭 시 GPT에게 추천 요청
if st.button("🎧 GPT에게 음악 추천 받기"):
    music_list = get_music_recommendation_from_gpt(user_msg)

    st.subheader("🎼 추천 결과")
    for music in music_list:
        st.write(f"**🎵 {music['title']}** - {music['artist']}")
        st.write(f"📝 {music['description']}")
        st.write(f"🔍 Spotify 검색어: `{music['spotify_query']}`")
        st.write(f"🔎 YouTube 검색어: `{music['youtube_query']}`")
        st.markdown("---")
 


### 4단계

import requests
import streamlit as st

# ✅ API 키 불러오기
client_id = st.secrets["SPOTIFY_CLIENT_ID"]
client_secret = st.secrets["SPOTIFY_CLIENT_SECRET"]

# ✅ 토큰 요청 함수
@st.cache_data
def get_spotify_token(client_id, client_secret):
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    auth = (client_id, client_secret)
    response = requests.post(url, headers=headers, data=data, auth=auth)
    return response.json().get("access_token")

# ✅ 검색 함수
def search_spotify_track(query, token):
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": 1
    }
    res = requests.get(search_url, headers=headers, params=params)
    items = res.json().get("tracks", {}).get("items", [])
    return items[0] if items else None

# ✅ GPT 추천곡 예시 (실제로는 GPT 응답에서 받아옴)
gpt_music_list = [
    {
        "title": "Lovely",
        "artist": "Billie Eilish",
        "spotify_query": "Lovely Billie Eilish"
    },
    {
        "title": "Someone Like You",
        "artist": "Adele",
        "spotify_query": "Someone Like You Adele"
    }
]

# ✅ 토큰 발급
token = get_spotify_token(client_id, client_secret)

# ✅ 검색 및 결과 출력
st.subheader("🎵 Spotify에서 가져온 앨범 정보")

for music in gpt_music_list:
    track = search_spotify_track(music["spotify_query"], token)
    
    if track:
        album_img = track["album"]["images"][0]["url"]
        song_name = track["name"]
        artist = track["artists"][0]["name"]
        link = track["external_urls"]["spotify"]

        st.image(album_img, width=200)
        st.markdown(f"**{song_name}** - {artist}")
        st.markdown(f"[🔗 Spotify에서 듣기]({link})")
        st.markdown("---")
    else:
        st.warning(f"❌ '{music['spotify_query']}'에 대한 결과가 없습니다.")



### 5단계

import requests
import streamlit as st

# ✅ YouTube API 키
youtube_api_key = st.secrets["YOUTUBE_API_KEY"]

# ✅ YouTube 검색 함수
def get_youtube_video_id(query, api_key):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": api_key,
        "maxResults": 1,
        "type": "video"
    }
    res = requests.get(search_url, params=params)
    data = res.json()
    items = data.get("items", [])
    if items:
        return items[0]["id"]["videoId"]
    return None

# ✅ GPT 추천곡 예시
gpt_music_list = [
    {
        "title": "Lovely",
        "artist": "Billie Eilish",
        "youtube_query": "Lovely Billie Eilish"
    },
    {
        "title": "Someone Like You",
        "artist": "Adele",
        "youtube_query": "Someone Like You Adele"
    }
]

# ✅ 결과 출력
st.subheader("📺 YouTube 영상")

for music in gpt_music_list:
    video_id = get_youtube_video_id(music["youtube_query"], youtube_api_key)

    if video_id:
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        st.markdown(f"**🎵 {music['title']} - {music['artist']}**")
        st.video(youtube_url)
        st.markdown("---")
    else:
        st.warning(f"❌ '{music['youtube_query']}'에 대한 유튜브 영상을 찾을 수 없습니다.")



### 6단계
import streamlit as st
import openai
import requests
import os
import json

# ▒▒▒ 1. API 키 로드 및 클라이언트 설정 ▒▒▒
openai_api_key = st.secrets["OPENAI_API_KEY"]
spotify_id = st.secrets["SPOTIFY_CLIENT_ID"]
spotify_secret = st.secrets["SPOTIFY_CLIENT_SECRET"]
youtube_key = st.secrets["YOUTUBE_API_KEY"]
openai_client = openai.OpenAI(api_key=openai_api_key)

# ▒▒▒ 2. 사용자 입력 UI ▒▒▒
st.set_page_config(page_title="음악 추천기", page_icon="🎵")
st.title("🎵 AI 기반 음악 추천 웹앱")
emotion = st.text_input("당신의 감정은?")
situation = st.text_input("당신의 현재 상황은?")
genre = st.selectbox("선호 장르", ["상관없음", "팝", "재즈", "클래식", "EDM"])
country = st.selectbox("듣고 싶은 언어/국가", ["상관없음", "한국", "미국", "일본", "기타"])

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
        system_msg = "당신은 음악 큐레이터입니다."
        user_msg = f"""
        다음 조건에 맞는 음악 3곡을 추천해주세요:\n{json.dumps(user_profile, indent=2)}
        아래 JSON 형식으로 응답:
        [
            {{
                "title": "",
                "artist": "",
                "description": "",
                "spotify_query": "",
                "youtube_query": ""
            }}
        ]
        """

        # GPT API 호출
        try:
            gpt_resp = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.8
            )
            gpt_result = json.loads(gpt_resp.choices[0].message.content)
        except Exception as e:
            st.error(f"GPT 오류 발생: {e}")
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
