# spotify/spotify_utills_1.py
"""
    main_emotion으로 seed track을 검색한 뒤,
    energy_level, valence 기준으로 추천곡 반환
"""

from fastapi import FastAPI
from pydantic import BaseModel
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

load_dotenv()

#SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
#SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

app = FastAPI()

# 입력 JSON 모델 정의
class EmotionInput(BaseModel):
    main_emotion: str
    secondary_emotions: list[str] | None = None
    energy_level: float
    valence: float
    description: str | None = None


@app.post("/recommend")
def recommend_song(data: EmotionInput, limit: int = 5):
    """
    main_emotion으로 seed track을 검색한 뒤,
    energy_level, valence 기준으로 추천곡 반환
    """

    # 1. main_emotion으로 트랙 검색
    search_result = sp.search(q=data.main_emotion, type="track", limit=1)
    if not search_result["tracks"]["items"]:
        return {"error": f"No tracks found for emotion: {data.main_emotion}"}

    seed_track_id = search_result["tracks"]["items"][0]["id"]

    # 2. 추천곡 검색 (energy, valence 기준)
    recs = sp.recommendations(
        seed_tracks=[seed_track_id],
        limit=limit,
        target_energy=data.energy_level,
        target_valence=data.valence
    )

    results = []
    for track in recs["tracks"]:
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

