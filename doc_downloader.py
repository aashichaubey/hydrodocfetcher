from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def open_document_tab(page, document_type):
    tab = page.locator(
        ".iwps_button_bar_segment button"
    ).filter(
        has_text=f"{document_type} -"
    )

    if tab.count() != 1:
        raise RuntimeError(
            f"Could not find document tab: {document_type}"
        )

    tab.click()

    # Wait for the document rows to load.
    page.locator(
        "tr.v-grid-row-has-data .fm_object_299 button"
    ).first.wait_for(
        state="visible",
        timeout=10000,
    )


def download_documents(
    page,
    download_folder,
    limit=10,
):
    folder = Path(download_folder)
    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    downloaded_files = []
    processed_document_numbers = set()

    scroll_container = page.locator(
        ".v-grid-scroller.v-grid-scroller-vertical"
    )

    max_scroll_attempts = 20
    scroll_attempts = 0

    while (
        len(downloaded_files) < limit
        and scroll_attempts < max_scroll_attempts
    ):
        rows = page.locator(
            "tr.v-grid-row-has-data"
        )

        row_count = rows.count()
        new_rows_found = 0

        for index in range(row_count):
            if len(downloaded_files) >= limit:
                break

            # FileMaker replaces row elements while scrolling,
            # so retrieve the current collection every time.
            rows = page.locator(
                "tr.v-grid-row-has-data"
            )

            if index >= rows.count():
                break

            row = rows.nth(index)

            document_number = row.locator(
                ".fm_object_201 .text"
            ).inner_text().strip()

            if (
                document_number
                in processed_document_numbers
            ):
                continue

            go_get_button = row.locator(
                ".fm_object_299 button"
            )

            go_get_button.click()

            download_button = page.locator(
                ".fm-download-button"
            )

            download_button.wait_for(
                state="visible",
                timeout=10000,
            )

            # The modal appears before FileMaker finishes
            # preparing the file.
            page.wait_for_timeout(1000)

            filename = (
                download_button
                .inner_text()
                .strip()
            )

            if not filename:
                filename = f"{document_number}.pdf"

            file_path = (
                folder
                / Path(filename).name
            )

            with page.expect_download(
                timeout=30000,
            ) as download_info:
                download_button.click()

            download = download_info.value
            download.save_as(file_path)

            downloaded_files.append(file_path)
            processed_document_numbers.add(
                document_number
            )
            new_rows_found += 1

            print(
                f"Downloaded {document_number}: "
                f"{file_path.resolve()}"
            )

            close_button = page.get_by_role(
                "button",
                name="Close",
                exact=True,
            )

            close_button.click()

            download_button.wait_for(
                state="hidden",
                timeout=10000,
            )

        if len(downloaded_files) >= limit:
            break

        # Scroll the virtual FileMaker grid by one page.
        scroll_result = scroll_container.evaluate(
            """
            element => {
                const before = element.scrollTop;
                const maximum =
                    element.scrollHeight
                    - element.clientHeight;

                element.scrollTop = Math.min(
                    before + element.clientHeight,
                    maximum
                );

                element.dispatchEvent(
                    new Event(
                        "scroll",
                        { bubbles: true }
                    )
                );

                return {
                    before: before,
                    after: element.scrollTop,
                    maximum: maximum
                };
            }
            """
        )

        page.wait_for_timeout(1000)
        scroll_attempts += 1

        print(
            "Grid scroll:",
            scroll_result,
        )

        # We reached the bottom, so no more records exist.
        if (
            scroll_result["after"]
            == scroll_result["before"]
        ):
            break

        if new_rows_found == 0:
            print(
                "No new rows in this view; "
                "continuing to scroll..."
            )

    return downloaded_files


def create_zip(
    files,
    output_folder,
    zip_name,
):
    folder = Path(output_folder)
    zip_path = (
        folder
        / Path(zip_name).name
    )

    with ZipFile(
        zip_path,
        mode="w",
        compression=ZIP_DEFLATED,
    ) as zip_file:
        for file_path in files:
            file_path = Path(file_path)

            zip_file.write(
                file_path,
                arcname=file_path.name,
            )

    print(
        f"Created ZIP: "
        f"{zip_path.resolve()}"
    )

    return zip_path