'''최종
C:/dev/spotify
python -m uvicorn recom:app --reload
'''

from fastapi import FastAPI
import os
import httpx
from dotenv import load_dotenv
import base64
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
#from spotify.main import music_results
from pydantic import BaseModel

load_dotenv()


SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

# 입력 JSON 모델 정의
class EmotionInput(BaseModel):
    main_emotion: str
    secondary_emotions: list[str] | None = None
    energy_level: float
    valence: float
    description: str | None = None

app = FastAPI()

async def get_spotify_access_token():
    """
    Spotify API 접근을 위한 액세스 토큰을 발급받습니다.
    """
    auth_string = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
        response.raise_for_status()
        return response.json()["access_token"]

@app.post("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/recommend")
def recommend_song(data: EmotionInput, limit: int = 10):
    """
    main_emotion으로 seed track을 검색
    """
    try:
        # 1. main_emotion으로 트랙 검색
        search_result = sp.search(q=data.main_emotion, type="track", limit=limit)
        items = search_result["tracks"]["items"]
        if not items:
            return {"error": f"No tracks found for emotion: {data.main_emotion}"}

        results = []
        for track in items:
             results.append({
                "name": track["name"],
                "artist": ", ".join([a["name"] for a in track["artists"]]),
                "url": track["external_urls"]["spotify"]
            })

        return {
            "tracks": results}

        '''
        # 2. 추천곡 검색 
        recs = sp.track(
            track_id=seed_track_id,
            #limit=limit,
            #target_energy=data.energy_level,
            #target_valence=data.valence
        )'''

        name = recs["name"]
        artist = recs["artists"][0]["name"]
        url = recs["external_urls"]["spotify"]

        #return name, artist, url
        return recs

        '''    results = []{
                "name": recs["name"],
                #search_result["tracks"]["items"][0]["name"],
                "artist": ", ".join([a["name"] for a in search_result["tracks"]["items"][0]["artists"]]),
                "url": search_result["tracks"]["items"][0]["external_urls"]["spotify"]
            },
            "recommendations": results
        }   '''
        

        results = []
        for track in recs["albums"]:
            results.append({
                "name": track["name"],
                "artist": ", ".join([a["name"] for a in track["artists"]]),
                "url": track["external_urls"]["spotify"]
            }) 

        return {
            "seed_track": {
                "name": search_result["tracks"]["items"][0]["name"],
                "artist": ", ".join([a["name"] for a in search_result["tracks"]["items"][0]["artists"]]),
                "url": search_result["tracks"]["items"][0]["external_urls"]["spotify"]
            },
            "recommendations": results
        }
    except Exception as e:
        return {"error": str(e)}
