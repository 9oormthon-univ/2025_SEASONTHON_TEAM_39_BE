import os
import base64
import json
import magic
from fastapi import FastAPI, UploadFile, File, HTTPException
from openai import AsyncOpenAI
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# OpenAI 비동기 클라이언트 초기화
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()


@app.post("/analyze_mood/")
async def analyze_mood(file: UploadFile = File(...)):
    """
    업로드된 이미지 파일을 분석하여 감정 태그를 추출하고 에너지와 긍정도합니다.
    """
    try:
        image_data = await file.read() # 파일 데이터를 비동기적으로 읽기
        
        # python-magic을 활용 파일 MIME 타입 유추
        mime_type = magic.from_buffer(image_data, mime=True)
        if not mime_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="유효한 이미지 파일이 아닙니다.")

        # 이미지를 base64로 인코딩
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # 챗GPT-4o에 보낼 프롬프트 구성
        prompt = """
        You are an AI assistant that analyzes the mood and emotional tone of images.
        Analyze the image and provide the following information in a structured JSON format:

        1.  **main_emotion**: The single most dominant emotion or mood (e.g., '평온함', '신비로움', '활기참').
        2.  **secondary_emotions**: A list of 2-3 supporting emotions or moods.
        3.  **energy_level_percentage**: An specific integer from 0 to 100 representing the energy level.
        4.  **positivity_level_percentage**: An specific integer from 0 to 100 representing the overall positivity.
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

        return result
        
    except HTTPException as e:
        # FastAPI의 HTTPException을 그대로 반환
        raise e
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"내부 서버 오류: {e}")

