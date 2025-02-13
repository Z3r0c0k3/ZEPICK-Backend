# ZEPICK API server

- stack : python(FastAPI), MongoDB

## API

### `/verify/code-gen`

- Request
  - POST `{"uuid": "인게임 사용자 UUID", "ip": "인게임 사용자 IP주소"}`
- Response
  - `{"status": "True", "code": "인증코드"}`
  - `{"status": "False", "message": "Duplicate UUID found in another collection."}`

### `/verify/verify-code`

- Request

  - POST `{"verify-code": "인증코드"}`

- Response
  - `{"status": "False", "message": "No matching code found."}`
  - `{"status": "True"}`
