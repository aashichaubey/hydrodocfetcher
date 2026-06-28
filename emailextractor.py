import base64
"""
    Takes Gmail's encoded email body data and returns normal text.

    Input:
        data: base64url encoded string from Gmail message payload

    Output:
        decoded email body as a string
"""
def extract_request(data):
    decoded_bytes = base64.urlsafe_b64decode(data + "===")
    text = decoded_bytes.decode("utf-8")

    return text

