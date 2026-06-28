import os

import httpx
from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/")
def home():
    return {"status": "Agent is running"}


@app.post("/webhooks/resend")
async def receive_email(request: Request):
    event = await request.json()

    if event.get("type") != "email.received":
        return {"received": True}

    email_id = event["data"]["email_id"]
    api_key = os.environ["RESEND_API_KEY"]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.resend.com/emails/receiving/{email_id}",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()
        email = response.json()

    subject = email.get("subject", "")
    body = email.get("text") or email.get("html") or ""
    sender = email.get("from", "")

    print("Sender:", sender)
    print("Subject:", subject)
    print("Body:", body)

    return {"received": True}