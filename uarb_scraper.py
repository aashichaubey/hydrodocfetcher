import re
from tempfile import TemporaryDirectory
from email_reply import send_email_response

from playwright.sync_api import sync_playwright

from doc_downloader import (
    create_zip,
    download_documents,
    open_document_tab,
)


UARB_URL = "https://uarb.novascotia.ca/fmi/webd/UARB15"


def extract_metadata(page):
    page.locator(".fm_object_292 .text").wait_for(
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
        text = tab_buttons.nth(index).inner_text().strip()

        match = re.fullmatch(
            r"(Exhibits|Key Documents|Other Documents|"
            r"Transcripts|Recordings)\s*-\s*(\d+)",
            text,
        )

        if match:
            document_type = match.group(1)
            count = int(match.group(2))

            metadata["document_counts"][document_type] = count

    return metadata


def open_matter(
    matter_number,
    document_type,
    download_limit=5,
):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
        )
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

        # FileMaker needs the field clicked before it accepts typing.
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

        open_document_tab(
            page,
            document_type,
        )

        with TemporaryDirectory(
            prefix="uarb_"
        ) as temp_folder:
            files = download_documents(
                page,
                temp_folder,
                limit=download_limit,
            )

            zip_name = (
                f"{matter_number}_"
                f"{document_type.replace(' ', '_')}.zip"
            )

            zip_path = create_zip(
                files,
                temp_folder,
                zip_name,
            )

            send_email_response(
                recipient="aashic63@gmail.com",
                matter_number=matter_number,
                document_type=document_type,
                metadata=metadata,
                downloaded_files=files,
                zip_path=zip_path,
            )

            print("Downloaded files:", files)
            print("ZIP file:", zip_path)
            print("Temporary folder:", temp_folder)
            print(
                "The ZIP and PDFs will be deleted "
                "after you press Enter."
            )

            input("Press Enter to finish...")

        browser.close()

        return metadata


if __name__ == "__main__":
    open_matter(
        matter_number="M12205",
        document_type="Other Documents",
        download_limit=10,
    )