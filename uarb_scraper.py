import re
from tempfile import TemporaryDirectory

from playwright.sync_api import sync_playwright

from doc_downloader import (
    create_zip,
    download_documents,
    open_document_tab,
)
from email_reply import (
    send_email_response,
    send_no_documents_response,
)


UARB_URL = "https://uarb.novascotia.ca/fmi/webd/UARB15"


def extract_metadata(page):
    page.locator(
        ".fm_object_292 .text"
    ).wait_for(
        state="visible",
        timeout=30000,
    )

    metadata = {
        "title": page.locator(
            ".csFM-4BAC3292-04BC-FC44-A278-B61F356EAB45"
        ).inner_text().strip(),
        "type": page.locator(
            ".fm_object_298 .text"
        ).inner_text().strip(),
        "category": page.locator(
            ".fm_object_287 .text"
        ).inner_text().strip(),
        "date_received": page.locator(
            ".fm_object_292 .text"
        ).inner_text().strip(),
        "decision_date": page.locator(
            ".fm_object_294 .text"
        ).inner_text().strip(),
        "document_counts": {},
    }

    tab_buttons = page.locator(
        ".iwps_button_bar_segment button"
    )

    for index in range(tab_buttons.count()):
        text = (
            tab_buttons
            .nth(index)
            .inner_text()
            .strip()
        )

        match = re.fullmatch(
            r"(Exhibits|Key Documents|Other Documents|"
            r"Transcripts|Recordings)\s*-\s*(\d+)",
            text,
        )

        if match:
            document_type = match.group(1)
            count = int(match.group(2))

            metadata["document_counts"][
                document_type
            ] = count

    return metadata


def process_document_request(
    recipient,
    original_subject,
    original_message_id,
    matter_number,
    document_type,
    download_limit=10,
    headless=True,
):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=headless,
        )

        try:
            page = browser.new_page()

            page.goto(
                UARB_URL,
                wait_until="domcontentloaded",
            )

            matter_input = page.locator(
                ".fm_object_254 .text"
            )
            search_button = page.locator(
                ".fm_object_258 button"
            )

            matter_input.wait_for(
                state="visible",
                timeout=30000,
            )

            # FileMaker requires the field to be focused
            # before it accepts keyboard input.
            matter_input.click()
            page.wait_for_timeout(500)

            matter_input.type(
                matter_number,
                delay=150,
            )

            matter_input.press("Tab")
            search_button.click()

            metadata = extract_metadata(page)
            print("Metadata:", metadata)

            available_count = (
                metadata["document_counts"]
                .get(document_type, 0)
            )

            with TemporaryDirectory(
                prefix="uarb_"
            ) as temp_folder:
                downloaded_files = []
                zip_path = None

                if available_count > 0:
                    open_document_tab(
                        page,
                        document_type,
                    )

                    downloaded_files = (
                        download_documents(
                            page,
                            temp_folder,
                            limit=min(
                                download_limit,
                                available_count,
                            ),
                        )
                    )

                    if downloaded_files:
                        zip_name = (
                            f"{matter_number}_"
                            f"{document_type.replace(' ', '_')}"
                            f".zip"
                        )

                        zip_path = create_zip(
                            downloaded_files,
                            temp_folder,
                            zip_name,
                        )

                if available_count == 0:
                    email_result = (
                        send_no_documents_response(
                            recipient=recipient,
                            original_subject=(
                                original_subject
                            ),
                            original_message_id=(
                                original_message_id
                            ),
                            matter_number=matter_number,
                            document_type=document_type,
                            metadata=metadata,
                        )
                    )
                else:
                    email_result = send_email_response(
                        recipient=recipient,
                        original_subject=(
                            original_subject
                        ),
                        original_message_id=(
                            original_message_id
                        ),
                        matter_number=matter_number,
                        document_type=document_type,
                        metadata=metadata,
                        downloaded_files=(
                            downloaded_files
                        ),
                        zip_path=zip_path,
                    )

                result = {
                    "matter_number": matter_number,
                    "document_type": document_type,
                    "available_count": available_count,
                    "downloaded_count": len(
                        downloaded_files
                    ),
                    "metadata": metadata,
                    "email_result": email_result,
                }

                print(
                    "Request completed:",
                    result,
                )

                return result

        finally:
            browser.close()
