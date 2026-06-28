# “Hi User, M12205 is about the Halifax Regional
# Water Commission - Windsor Street Exchange Redevelopment
# Project - $69,270,000. It relates to Capital Expenditure
# within the Water category. The matter had an initial
# filing on April 7, 2025 and a final filing on October 23,
# 2025. I found 13 Exhibits, 5 Key Documents, 21 Other
# Documents, and no Transcripts or Recordings. I downloaded
# 10 out of the 21 Other Documents and am attaching them as
# a ZIP here.”
from dotenv import load_dotenv

load_dotenv()
import base64
import os
from datetime import datetime
from pathlib import Path

import httpx


FROM_EMAIL = (
    "UARB Document Agent "
    "<documents@agent.aashichaubey.com>"
)


def format_date(date_string):
    if not date_string:
        return "an unknown date"

    date = datetime.strptime(
        date_string,
        "%m/%d/%Y",
    )

    return f"{date.strftime('%B')} {date.day}, {date.year}"


def format_count(count, document_type):
    if count == 0:
        return f"no {document_type}"

    return f"{count} {document_type}"


def create_email_body(
    matter_number,
    document_type,
    metadata,
    downloaded_count,
):
    counts = metadata["document_counts"]
    total_count = sum(counts.values())
    requested_count = counts.get(document_type, 0)

    count_summary = ", ".join(
        [
            format_count(
                counts.get("Exhibits", 0),
                "Exhibits",
            ),
            format_count(
                counts.get("Key Documents", 0),
                "Key Documents",
            ),
            format_count(
                counts.get("Other Documents", 0),
                "Other Documents",
            ),
            format_count(
                counts.get("Transcripts", 0),
                "Transcripts",
            ),
            format_count(
                counts.get("Recordings", 0),
                "Recordings",
            ),
        ]
    )

    received_date = format_date(
        metadata["date_received"]
    )
    decision_date = format_date(
        metadata["decision_date"]
    )

    if requested_count == 0:
        download_summary = (
            f"I found no {document_type} for this matter, "
            f"so there is no ZIP attachment."
        )
    else:
        download_summary = (
            f"I downloaded {downloaded_count} out of the "
            f"{requested_count} {document_type} and attached "
            f"them as a ZIP here."
        )

    return (
        f"Hi,\n"
        f"{matter_number} is about the {metadata['title']}. "
        f"It relates to {metadata['category']} within "
        f"the {metadata['type']} category.\n"
        f"The matter had an initial filing on "
        f"{received_date} and a final filing on "
        f"{decision_date}.\n"
        f"There are {total_count} files in total. "
        f"I found {count_summary}.\n\n"
        f"{download_summary}\n\n"
        f"Regards,\n"
        f"UARB Document Agent"
    )


def build_reply_subject(original_subject):
    if not original_subject:
        return "Re: Document request"

    if original_subject.lower().startswith("re:"):
        return original_subject

    return f"Re: {original_subject}"


def send_invalid_request_response(
    recipient,
    original_subject,
    original_message_id,
):
    api_key = os.environ["RESEND_API_KEY"]

    email_body = (
        "Hi,\n\n"
        "Invalid request. Please provide a matter number "
        "(for example, M12205) and one document type: "
        "Exhibits, Key Documents, Other Documents, "
        "Transcripts, or Recordings.\n\n"
        "Regards,\n"
        "UARB Document Agent"
    )

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": [recipient],
            "reply_to": (
                "documents@agent.aashichaubey.com"
            ),
            "subject": build_reply_subject(
                original_subject
            ),
            "headers": {
                "In-Reply-To": original_message_id,
                "References": original_message_id,
            },
            "text": email_body,
        },
        timeout=60,
    )

    response.raise_for_status()
    result = response.json()
    print("Invalid-request email sent:", result)
    return result


def send_email_response(
    recipient,
    original_subject,
    original_message_id,
    matter_number,
    document_type,
    metadata,
    downloaded_files,
    zip_path,
):
    api_key = os.environ["RESEND_API_KEY"]
    email_body = create_email_body(
        matter_number=matter_number,
        document_type=document_type,
        metadata=metadata,
        downloaded_count=len(downloaded_files),
    )

    email_payload = {
        "from": FROM_EMAIL,
        "to": [recipient],
        "reply_to": (
            "documents@agent.aashichaubey.com"
        ),
        "subject": build_reply_subject(
            original_subject
        ),
        "headers": {
            "In-Reply-To": original_message_id,
            "References": original_message_id,
        },
        "text": email_body,
    }

    if zip_path is not None:
        zip_path = Path(zip_path)
        zip_content = base64.b64encode(
            zip_path.read_bytes()
        ).decode("utf-8")
        email_payload["attachments"] = [
            {
                "filename": zip_path.name,
                "content": zip_content,
            }
        ]

    response = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=email_payload,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()
    print("Response email sent:", result)

    return result
