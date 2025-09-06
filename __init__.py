#terminal
#PS c:\ dev> 하면 안되고! cd c:\dev\spotify 해야함
#python -m uvicorn main:app --reload --port 8001
#python -m uvicorn recom:app --reload --port 8004
#python -m uvicorn APIcallTRY:app --reload --port 801

#가상환경인 경우
#uvicorn spotify.main:app --reload --port 8001

#주의 - spotify! not spotipy

#변수명 energy_level, valence
#변수 0<= energy_level, valence <=1

'''
#example response from anlz_mood API
{
  "main_emotion": "calm",
  "secondary_emotions": [
    "minimalistic",
    "serene",
    "quiet"
  ],
  "energy_level": 0.2,
  "valence": 0.65,
  "description": "The image portrays a simple and calm atmosphere with its minimalistic design and muted tones."
}


{
  "main_emotion": "calm",
  "secondary_emotions": [
    "mistery",
    "quiet",
    "peaceful"
  ],
  "energy_level": 0.3,
  "valence": 0.7,
  "description": "The image depicts a serene winter landscape with snow-covered trees under a clear blue sky, creating a peaceful and calm atmosphere."
}
'''