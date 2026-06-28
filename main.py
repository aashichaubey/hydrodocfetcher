import asyncio
import os
from email.utils import parseaddr

import httpx
from fastapi import (
    BackgroundTasks,
    FastAPI,
    Request,
)

from request_parser import parse_request
from uarb_scraper import process_document_request
from email_reply import send_invalid_request_response


app = FastAPI()


@app.get("/")
def home():
    return {
        "status": "Agent is running",
    }


async def process_received_email(event):
    try:
        event_data = event["data"]
        email_id = event_data["email_id"]
        message_id = event_data["message_id"]

        api_key = os.environ["RESEND_API_KEY"]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                (
                    "https://api.resend.com/"
                    f"emails/receiving/{email_id}"
                ),
                headers={
                    "Authorization": (
                        f"Bearer {api_key}"
                    )
                },
                timeout=60,
            )

            response.raise_for_status()
            email = response.json()

        subject = email.get("subject", "")
        body = (
            email.get("text")
            or email.get("html")
            or ""
        )

        sender_value = email.get("from", "")
        sender = parseaddr(sender_value)[1]

        parsed_request = parse_request(
            f"{subject}\n{body}"
        )

        matter_number = parsed_request[
            "matter_number"
        ]
        document_type = parsed_request[
            "document_type"
        ]

        print("Sender:", sender)
        print("Subject:", subject)
        print("Parsed request:", parsed_request)

        if not sender:
            raise ValueError(
                "Incoming email has no sender address."
            )

        if not matter_number or not document_type:
            result = await asyncio.to_thread(
                send_invalid_request_response,
                recipient=sender,
                original_subject=subject,
                original_message_id=message_id,
            )
            print(
                "Invalid request handled:",
                result,
            )
            return

        # The scraper is synchronous and takes time, so run it
        # in a worker thread instead of blocking FastAPI.
        result = await asyncio.to_thread(
            process_document_request,
            recipient=sender,
            original_subject=subject,
            original_message_id=message_id,
            matter_number=matter_number,
            document_type=document_type,
            download_limit=10,
            headless=True,
        )

        print(
            "Background request completed:",
            result,
        )

    except Exception as error:
        print(
            "Background request failed:",
            repr(error),
        )


@app.post("/webhooks/resend")
async def receive_email(
    request: Request,
    background_tasks: BackgroundTasks,
):
    event = await request.json()

    if event.get("type") != "email.received":
        return {
            "received": True,
            "ignored": True,
        }

    # Return quickly so Resend does not wait while the
    # documents are downloaded.
    background_tasks.add_task(
        process_received_email,
        event,
    )

    return {
        "received": True,
        "processing": True,
    }
