We are building an AI agent platform for utilities like Toronto Hydro or Hydro One. Utilities have
to make large, detailed regulatory filings to get projects approved and justify customer rates.
Our Regulatory Agent helps automate the research that goes into these filings by finding
examples, precedents, and approval patterns from past cases. This challenge focuses on the
data ingestion side, developing a pipeline to collect filings and build the searchable database
that lies under the Regulatory Agent’s research capabilities.

Your task is to build an AI agent that (1) fetches up to 10 documents of a given type from a
website, and (2) ZIPs those documents and sends the ZIP over email. More specifically:
1. A user will email your agent a “matter number” and a document type:
a. Matter numbers take the form M12205, M12383, etc.
b. Document types can be:
i. Exhibits
ii. Key Documents
iii. Other Documents
iv. Transcripts
v. Recordings
c. Example: “Hi Agent, Can you give me Other Documents files
from M12205? Thanks!”
2. Your agent must then fetch the files:
a. Go to https://uarb.novascotia.ca/fmi/webd/UARB15
b. Input the matter number in the “Go Directly to Matter” box
c. Press Search
d. Go to the relevant tab corresponding to the document type
e. Download up to 10 documents (use the “Go Get It” button)
f. Compress those documents into a ZIP
3. Your agent must then send an email response:
a. The ZIP must be included as an attachment
b. The email should provide a total count of all files within that matter number
c. The email should also summarize key metadata related to the matter number
d. Example: “Hi User, M12205 is about the Halifax Regional
Water Commission - Windsor Street Exchange Redevelopment
Project - $69,270,000. It relates to Capital Expenditure
within the Water category. The matter had an initial
filing on April 7, 2025 and a final filing on October 23,
2025. I found 13 Exhibits, 5 Key Documents, 21 Other
Documents, and no Transcripts or Recordings. I downloaded
10 out of the 21 Other Documents and am attaching them as
a ZIP here.”