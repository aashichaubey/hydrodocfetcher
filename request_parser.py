# input
# “Hi Agent, Can you give me Other Documents files
# from M12205? Thanks!”

# output
# {matter_number: "M12205", document_type: "Other documents"}
document_types: ["Exhibits", "Key Documents", "Other Documents", "Transcripts", "Recordings"]
uarb_input = {"matter_num": "", "document_type": ""}
def parse_request(body):
    # Find a matter number such as M12205.
    matter_match = re.search(r"\bM\d+\b", body, re.IGNORECASE)
    matter_number = matter_match.group().upper() if matter_match else None

    # Find one of the supported document types.
    document_type = None

    for option in document_types
        if option.lower() in body.lower():
            document_type = option
            break

    return {
        "matter_number": matter_number,
        "document_type": document_type,
    } 



