import re

from playwright.sync_api import sync_playwright
from doc_downloader import open_document_tab
from doc_downloader import (
    open_document_tab,
    download_first_document,
)

UARB_URL = "https://uarb.novascotia.ca/fmi/webd/UARB15"

def extract_metadata(page):
    # Wait until the matter details have loaded.
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


def open_matter(matter_number):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(UARB_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        app = page.frame_locator("iframe")

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

        matter_input.click()
        page.wait_for_timeout(500)
        matter_input.type(matter_number, delay=150)
        matter_input.press("Tab")
        search_button.click()
        metadata = extract_metadata(page)
        print(metadata)
        page.wait_for_timeout(500)
        open_document_tab(page, "Other Documents")
        page.wait_for_timeout(500)
        download_first_document(page)

        page.wait_for_timeout(8000)
        input("Press Enter to close the browser...")

        browser.close()


if __name__ == "__main__":
    open_matter("M12205")


"""
extract metadata

Title - Description: 
Type - (e.g Water): <div class="v-csslayout v-layout v-widget iwp-glass-pane v-csslayout-iwp-glass-pane v-has-width v-has-height" style="top: 178px; right: 570px; width: 179px; height: 28px;"></div>
Category - (e.g Capital Expenditure): <div class="v-csslayout v-layout v-widget iwp-glass-pane v-csslayout-iwp-glass-pane v-has-width v-has-height" style="top: 210px; right: 570px; width: 179px; height: 28px;"></div>
Date Recieved - <div class="v-csslayout v-layout v-widget iwp-glass-pane v-csslayout-iwp-glass-pane v-has-width v-has-height" style="top: 0px; left: 0px; width: 103px; height: 28px;"></div>
Descision Date - <div class="v-csslayout v-layout v-widget iwp-glass-pane v-csslayout-iwp-glass-pane v-has-width v-has-height" style="top: 0px; left: 0px; width: 103px; height: 28px;"></div>
# of exhibits- <div class="v-csslayout v-layout v-widget iwps_button_bar_segment v-csslayout-iwps_button_bar_segment fm_object_277 v-csslayout-fm_object_277 hand-cursor v-csslayout-hand-cursor csFM-AE11ABB7-1031-A04A-9A0F-ABB8C87B8079 v-csslayout-csFM-AE11ABB7-1031-A04A-9A0F-ABB8C87B8079 v-has-width v-has-height" style="top: 0px; left: 0px; width: 183px; height: 30px;"><button type="button" class="fm-widget v-widget v-has-width v-has-height hand-cursor fm-widget-hand-cursor text fm-widget-text inner_border fm-widget-inner_border" id="b0p0o277i0i0r1" tabindex="0" style="width: 100%; height: 100%;"><div class="fm-button-container"><span class="v-nativebutton-caption"><div class="fm-button-bar-segment-label fm-button-bar-segment-label-277 csFM-AE11ABB7-1031-A04A-9A0F-ABB8C87B8079-fm-button-bar-segment-label"><div class="fm-text-paragraph" style="max-width: 169px; max-height: 30px;"><span class="fm-text-character">Exhibits - 13</span></div></div></span></div></button></div>
and same for rest of # of recordings, other documents etc.


Water - <div class="fm-textarea v-widget v-readonly v-has-width v-has-height iwps_edit_box fm-textarea-iwps_edit_box fm_object_298 fm-textarea-fm_object_298 fm-inactive" id="b0p0o298i0i0r1" style="top: 178px; right: 570px; width: 179px; height: 28px;"><div class="inner_border"><div class="text" tabindex="-1">Water
</div><div class="placeholder"></div></div></div>
Capital Expenditure - <div class="fm-textarea v-widget v-readonly v-has-width v-has-height fm-inactive iwps_edit_box fm-textarea-iwps_edit_box fm_object_287 fm-textarea-fm_object_287" id="b0p0o287i0i0r1" style="top: 210px; right: 570px; width: 179px; height: 28px;"><div class="inner_border"><div class="text" tabindex="-1">Capital Expenditure Approvals
</div><div class="placeholder"></div></div></div>
Start date - <div class="fm-textarea v-widget v-readonly v-has-width v-has-height iwps_edit_box fm-textarea-iwps_edit_box fm_object_292 fm-textarea-fm_object_292 fm-inactive" id="b0p0o292i0i0r1" style="top: 0px; left: 0px; width: 103px; height: 28px;"><div class="inner_border"><div class="text" tabindex="-1">04/07/2025
</div><div class="placeholder"></div></div></div>
End date - <div class="fm-textarea v-widget v-readonly v-has-width v-has-height iwps_edit_box fm-textarea-iwps_edit_box fm_object_294 fm-textarea-fm_object_294 fm-inactive" id="b0p0o294i0i0r1" style="top: 0px; left: 0px; width: 103px; height: 28px;"><div class="inner_border"><div class="text" tabindex="-1">10/23/2025
</div><div class="placeholder"></div></div></div>

Exhibits - <div class="v-csslayout v-layout v-widget iwps_button_bar_segment v-csslayout-iwps_button_bar_segment fm_object_277 v-csslayout-fm_object_277 hand-cursor v-csslayout-hand-cursor csFM-AE11ABB7-1031-A04A-9A0F-ABB8C87B8079 v-csslayout-csFM-AE11ABB7-1031-A04A-9A0F-ABB8C87B8079 v-has-width v-has-height" style="top: 0px; left: 0px; width: 183px; height: 30px;"><button type="button" class="fm-widget v-widget v-has-width v-has-height hand-cursor fm-widget-hand-cursor text fm-widget-text inner_border fm-widget-inner_border" id="b0p0o277i0i0r1" tabindex="0" style="width: 100%; height: 100%;"><div class="fm-button-container"><span class="v-nativebutton-caption"><div class="fm-button-bar-segment-label fm-button-bar-segment-label-277 csFM-AE11ABB7-1031-A04A-9A0F-ABB8C87B8079-fm-button-bar-segment-label"><div class="fm-text-paragraph" style="max-width: 169px; max-height: 30px;"><span class="fm-text-character">Exhibits - 13</span></div></div></span></div></button></div>

"""