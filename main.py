import datetime
import json
from fastapi import FastAPI
import requests
from pydantic import BaseModel, UUID4
from pymongo import MongoClient
import random
import string
import httpx
from dotenv import load_dotenv
import os

app = FastAPI()

# MongoDB 연결 설정
client = MongoClient("mongodb://localhost:27017/")
db = client["zepick_verify"]
verify_codes_collection = db["verify-codes"]

# Pydantic 모델 정의
class CodeGenRequest(BaseModel):
    uuid: UUID4
    ip: str

class VerifyCodeRequest(BaseModel):
    verify_code: str

@app.get("/")
async def root():
    return {"message": "Welcome to ZEPICK Backend API."}

@app.post("/verify/code-gen")
async def generate_code(request: CodeGenRequest):
    # UUID str 형변환
    request.uuid = str(request.uuid)
    request.uuid = request.uuid.replace("-", "")

    # UUID 중복 확인
    for collection_name in db.list_collection_names():
        if collection_name != "verify-codes":
            if db[collection_name].find_one({"uuid": request.uuid}):
                return {"status": "False", "message": "Duplicate UUID found in another collection."}

    # 사용자 UUID 검증
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://playerdb.co/api/player/minecraft/{request.uuid}")
        data = response.json()
        if data["code"] == "minecraft.api_failure":
            return {"status": "False", "message": "This user is not authorized or is not a valid user."}
        elif data["code"] == "player.found":
            username = data["data"]["player"]["username"]
            avatar = data["data"]["player"]["avatar"]
        else:
            return {"status": "False", "message": "1: Unexpected error occurred."}
    # 악성 사용자 여부 검증
        response = await client.get(f"https://userdb.ourmc.space/api/v1/report/search/{username}")
        data = response.json()
        if data["value"]["count"] > 0:
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            ban_reasons = {
                0 : "비인가 프로그램(핵) 사용",
                1 : "서버 테러 행위",
                2 : "서버 내 사기 행위",
                3 : "서버 해킹 행위",
                4 : "서버 내 분쟁 조장 행위",
                5 : "서버 내 부적절한 언행 사용",
                6 : "기타 악의적인 행위"
                
            }
            ban_reason = ban_reasons[data['value']['list'][0]['reason']]
            print(f"{username}: {ban_reason}")
            embed = {
              "content": "# 인증을 요청한 사용자의 전과가 확인되어 인증을 미승인했습니다.\n||@everyone||",
              "embeds": [
                {
                  "title": "인증 사용자 전과 감지",
                  "description": f"username: `{username}`",
                  "url": f"https://userdb.ourmc.space/user/{request.uuid}#{data['value']['list'][0]['id']}",
                  "color": 4607,
                  "fields": [
                    {
                      "name": f"마지막 전과사유: {ban_reason}",
                      "value": f"전과 횟수: {data['value']['count']}",
                      "inline": True
                    }
                  ],
                  "author": {
                    "name": "ZEPICK 사용자 전과 조회",
                    "icon_url": "https://i.imgur.com/kb0t8va.png"
                  },
                  "footer": {
                    "text": "인증 시간",
                    "icon_url": "https://i.imgur.com/DYHGKRZ.png"
                  },
                  "timestamp": timestamp,
                  "thumbnail": {
                    "url": avatar
                  }
                }
              ],
              "attachments": []
            }
            headers = {
                'Content-Type': 'application/json'
            }
            # Load environment variables from .env file
            load_dotenv()

            # Get the webhook URL from environment variables
            webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

            response = requests.post(webhook_url, data=json.dumps(embed), headers=headers)
            if response.status_code == 204:
                print('웹훅 전송 성공!')
            else:
                print(f'웹훅 전송 실패: {response.status_code}')
            
            return {"status": "False", "message": "This user has been reported."}
        elif data["value"]["count"] <= 0:
            # 랜덤 코드 생성 및 중복 확인
            while True:
                random_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                if not verify_codes_collection.find_one({"code": random_code}):
                    break
                
            # verify-codes 컬렉션에 코드 저장
            verify_codes_collection.insert_one({"code": random_code})

            # 새로운 컬렉션 생성 및 데이터 삽입
            new_collection = db[random_code]
            new_collection.insert_one({"uuid": request.uuid, "ip": request.ip, "username": username, "avatar": avatar})

            return {"status": "True", "code": random_code}
        else:
            return {"status": "False", "message": "Unexpected error occurred."}

@app.post("/verify/verify-code")
async def verify_code(request: VerifyCodeRequest):
    if verify_codes_collection.find_one({"code": request.verify_code}):
        user_data = db[request.verify_code].find_one({}, {"_id": 0, "avatar": 1})
        if user_data:
            return {"status": "True", "avatar": (user_data["avatar"]+"/100")}
        else:
            return {"status": "False", "message": "Avatar URL not found."}
    else:
        return {"status": "False", "message": "No matching code found."}