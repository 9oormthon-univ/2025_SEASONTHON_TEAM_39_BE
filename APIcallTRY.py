import os
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import json

# .env 파일에서 환경 변수 로드
load_dotenv()

app = FastAPI()



# Spotify API 인증 정보 로드
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Spotipy 클라이언트 설정
sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

import base64
import magic
from openai import AsyncOpenAI

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# OpenAI 비동기 클라이언트 초기화
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/analyze_mood/")
async def analyze_mood(
    file: UploadFile = File(...),
    text_input: str = Form(..., max_length=100)
):

    """
    업로드된 이미지와 이에 대한 설명(100자 이내)을 분석하여 감정 태그를 추출하고 에너지와 긍정도를 파악합니다.
    """
    try:
        image_data = await file.read() # 파일 데이터를 비동기적으로 읽기
        #text_input = await text_input.read() # 텍스트 데이터를 비동기적으로 읽기

        # python-magic을 활용 파일 MIME 타입 유추
        mime_type = magic.from_buffer(image_data, mime=True)
        if not mime_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="유효한 이미지 파일이 아닙니다.")

        # 이미지를 base64로 인코딩
        base64_image = base64.b64encode(image_data).decode('utf-8')

        #text가 100자 이내인지 확인
        if len(text_input) > 100:
            raise HTTPException(status_code=400, detail="텍스트 설명은 100자 이내로 작성해주세요.")

        # bytes를 문자열로 디코딩
        #text_input = text_input.decode('utf-8')

        # 챗GPT-4o에 보낼 프롬프트 구성
        prompt = """
        You are an AI assistant that analyzes the mood and emotional tone of images.
        Analyze the image and text(max length 100) provide the following information in a structured JSON format:

        1.  **main_emotion**: The single most dominant emotion or mood (e.g., "calm", "acoustic", "mysterious", "ambient","aggressive","rock","upbeat","dance").
        2.  **secondary_emotions**: A list of 2-3 supporting emotions or moods.
        3.  **energy_level**: An specific integer from 0.00 to 1.00 representing the energy level.
        4.  **valence**: An specific integer from 0.00 to 1.00 representing the overall positivity.
        5.  **description**: A brief, descriptive sentence about the image's atmosphere.

        The final output must be a valid JSON object.
        """
        
        # GPT-4o 모델을 비동기적으로 호출
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "text", "text": f"The user-provided text is: \"{text_input}\""},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                            "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )

        # 응답에서 JSON 데이터 추출
        result = json.loads(response.choices[0].message.content)
        main_emotion = result.get("main_emotion")
        valence = result.get("valence")

        if main_emotion is None or valence is None:
            raise HTTPException(status_code=500, detail="분석 결과가 없습니다.")
        
        search_result = sp.search(q=main_emotion, type="track", limit=10)
        items = search_result.get("tracks", {}).get("items", [])
        if not items:
            return {"error": f"No tracks found for emotion: {main_emotion}"}

        results = []
        for track in items:
            results.append({
                "name": track["name"],
                "artist": ", ".join([a["name"] for a in track["artists"]]),
                "url": track["external_urls"]["spotify"]
            })

        return {
            "tracks": results
        }
        
    except HTTPException as e:
        # FastAPI의 HTTPException을 그대로 반환
        raise e
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"내부 서버 오류: {e}")


def recommend_song(data: dict, limit: int = 10):
    """
    main_emotion을 사용하여 Spotify에서 트랙을 검색하고 추천합니다.
    """
    try:
        main_emotion = data.get("main_emotion")
        if not main_emotion:
            return {"error": "main_emotion not found in analysis result"}

        # 1. main_emotion으로 트랙 검색
        search_result = sp.search(q=main_emotion, type="track", limit=10)
        items = search_result.get("tracks", {}).get("items", [])
        if not items:
            return {"error": f"No tracks found for emotion: {main_emotion}"}

        results = []
        for track in items:
            results.append({
                "name": track["name"],
                "artist": ", ".join([a["name"] for a in track["artists"]]),
                "url": track["external_urls"]["spotify"]
            })

        return {
            "tracks": results
        }

    except Exception as e:
        return {"error": f"Spotify API error: {str(e)}"}

'''@app.post("/analyze_and_get_tracks/")
async def analyze_and_get_tracks(
    image: UploadFile = File(...),
    text: str = Form(...)
):
    """
    이미지와 텍스트를 anlz_mood API에 전송하고,
    그 결과를 바탕으로 Spotify 트랙을 추천합니다.
    """
    try:
        # anlz_mood API에 전송할 파일, 데이터 준비
        files = {
            "image": (image.filename, await image.read(), image.content_type),
            "text_input": (None, text, "text/plain") 
        }

        # anlz_mood API에 POST 요청 보내기
        response = requests.post(
            f"{ANLZ_MOOD_API_URL}/analyze_mood/",
            files=files
        )
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

        # anlz_mood API로부터 받은 JSON 응답
        mood_analysis_result = response.json()

        # anlz_mood API의 결과를 바탕으로 Spotify 로직 수행
        recommended_tracks = recommend_song(mood_analysis_result)

        return {
            "mood_analysis_result": mood_analysis_result,
            "recommended_tracks": recommended_tracks
        }

    except requests.exceptions.RequestException as e:
        # anlz_mood API 호출 중 네트워크 또는 HTTP 오류 발생 시
        return {"error": f"anlz_mood API 호출 오류: {str(e)}"}
    except Exception as e:
        # 기타 오류 발생 시
        return {"error": str(e)}'''
