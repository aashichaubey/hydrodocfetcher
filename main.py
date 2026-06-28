from fastapi import FastAPI
from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/")
def home():
    return {"status": "Agent is running"}

@app.post("/webhooks/resend")
async def receive_email(request: Request):
    event = await request.json()
    print("Email event received:", event)
    return {"received": True}

"""
curl -X POST http://127.0.0.1:8000/webhooks/resend \
  -H "Content-Type: application/json" \
  -d '{"type":"email.received","data":{"from":"agent@granuuneav.resend.app"}}'

"""