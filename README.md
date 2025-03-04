# ZEPICK API server

- stack : python(FastAPI), MongoDB

## API

### `/verify/code-gen`

- Request
  - POST `{"uuid": "인게임 사용자 UUID", "ip": "인게임 사용자 IP주소"}`
- Response
  - `{"status": "True", "code": "인증코드"}`
    - 정상 로직.
  - `{"status": "False", "message": "Duplicate UUID found in another collection."}`
    - 이미 존재하는 UUID가 다른 컬렉션에 존재할 때 발생.
  - `{"status": "False", "message": "This user is not authorized or is not a valid user."}`
    - 정품인증 유저가 아니거나 마인크래프트 사용자가 아닐 때 발생.
  - `{"status": "False", "message": "This user has been reported."}``
    - 인증한 사용자가 악성 사용자로 신고된 상태일 때 발생.

### `/verify/verify-code`

- Request

  - POST `{"verify_code": "인증코드"}`

- Response
  - `{"status": "False", "message": "No matching code found."}`
    - 일치하는 코드가 없을 때 발생.
  - `{"status": "True"}`
    - 정상 로직.
