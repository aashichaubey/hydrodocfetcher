from pathlib import Path
def open_document_tab(page, document_type):
    tab = page.locator(
        ".iwps_button_bar_segment button"
    ).filter(has_text=f"{document_type} -")

    if tab.count() != 1:
        raise RuntimeError(
            f"Could not find document tab: {document_type}"
        )

    tab.click()

    page.get_by_role(
        "button",
        name="GO GET IT",
        exact=True,
    ).first.wait_for(
        state="visible",
        timeout=30000,
    )



def download_documents(page, download_folder, limit=5):
    folder = Path(download_folder)
    folder.mkdir(parents=True, exist_ok=True)

    downloaded_files = []

    go_get_buttons = page.get_by_role(
        "button",
        name="GO GET IT",
        exact=True,
    )

    number_to_download = min(
        go_get_buttons.count(),
        limit,
    )

    for index in range(number_to_download):
        # Re-locate because FileMaker changes the page after each modal.
        go_get_buttons = page.get_by_role(
            "button",
            name="GO GET IT",
            exact=True,
        )

        go_get_buttons.nth(index).click()

        download_button = page.locator(".fm-download-button")
        download_button.wait_for(
            state="visible",
            timeout=30000,
        )

        filename = download_button.inner_text().strip()
        file_path = folder / Path(filename).name

        with page.expect_download() as download_info:
            download_button.click()

        download_info.value.save_as(file_path)
        downloaded_files.append(file_path)

        page.get_by_role(
            "button",
            name="Close",
            exact=True,
        ).click()

        download_button.wait_for(
            state="hidden",
            timeout=30000,
        )

        print(f"Downloaded: {file_path}")

    return downloaded_files