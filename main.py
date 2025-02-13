from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import random
import string

app = FastAPI()

# MongoDB 연결 설정
client = MongoClient("mongodb://localhost:27017/")
db = client["zepick_verify"]
verify_codes_collection = db["verify-codes"]

# Pydantic 모델 정의
class CodeGenRequest(BaseModel):
    uuid: str
    ip: str

class VerifyCodeRequest(BaseModel):
    verify_code: str

@app.get("/")
async def root():
    return {"message": "Welcome to ZEPICK Backend API."}

@app.post("/verify/code-gen")
async def generate_code(request: CodeGenRequest):
    # UUID 중복 확인
    for collection_name in db.list_collection_names():
        if collection_name != "verify-codes":
            if db[collection_name].find_one({"uuid": request.uuid}):
                return {"status": "False", "message": "Duplicate UUID found in another collection."}

    # 랜덤 코드 생성 및 중복 확인
    while True:
        random_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        if not verify_codes_collection.find_one({"code": random_code}):
            break

    # verify-codes 컬렉션에 코드 저장
    verify_codes_collection.insert_one({"code": random_code})

    # 새로운 컬렉션 생성 및 데이터 삽입
    new_collection = db[random_code]
    new_collection.insert_one({"uuid": request.uuid, "ip": request.ip})

    return {"status": "True", "code": random_code}

@app.post("/verify/verify-code")
async def verify_code(request: VerifyCodeRequest):
    if verify_codes_collection.find_one({"code": request.verify_code}):
        return {"status": "True"}
    else:
        return {"status": "False", "message": "No matching code found."}
