from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import re

app = FastAPI()

# File Path (CSV or Excel in same folder)
file_path = "Untitled tryspreadsheet - Sheet1.csv"

# Replace with your actual Google Sheet CSV/Excel URL and Sheet ID
# file_path = "https://docs.google.com/spreadsheets/d/<Sheet-ID>/export?format=csv"

#  Load file once when app starts
if file_path.endswith(".csv"):
    df = pd.read_csv(file_path)
elif file_path.endswith(".xlsx"):
    df = pd.read_excel(file_path)
else:
    raise ValueError("Unsupported file format")


# Request schema
class QueryRequest(BaseModel):
    sub_lesson: str
    template: str = None


# Extract block by template name
def extract_block_by_template(text: str, template: str) -> str:
    if not isinstance(text, str) or not template:
        return ""

    lines = text.splitlines()
    start_idx = None
    end_idx = len(lines)

    # Template headings to detect block boundaries
    templates = [
        "Interactive Matching",
        "True / False",
        "MCQ with",
        "Drag and Drop",
        "Sorting",
        "Interactive matching",
        "MCQ options with Images ",
        "Audio Options plus Images",
        "MCQ with two options",
        "Multiple Choice with Passage"
    ]

    # Compile pattern to detect template headings in the text
    pattern = r"^\s*(" + "|".join(re.escape(t) for t in templates) + r")"

    # Find the block start by partial match of the template
    for i, line in enumerate(lines):
        if template.lower() in line.strip().lower():
            start_idx = i
            break

    if start_idx is None:
        return ""

    # Find where the next known template block starts
    for j in range(start_idx + 1, len(lines)):
        if re.match(pattern, lines[j], re.IGNORECASE):
            end_idx = j
            break

    return "\n".join(lines[start_idx:end_idx]).strip()



# Main route
@app.post("/get-question")
def get_question_template(query: QueryRequest):
    row = df[df['Sub-lesson'].str.strip().str.lower() == query.sub_lesson.strip().lower()]
    if row.empty:
        raise HTTPException(status_code=404, detail="Sub-lesson not found.")

    row = row.iloc[0]

    revised = row.get('Revised Sample Question- Suggested by Nisha, Tavisha, Diksha, Khadija', '')
    sample = row.get('Sample Questions', '')
    question_text = revised if pd.notna(revised) and revised.strip() else sample
    template_list = row.get('Templates', '')

    if query.template and query.template.strip():
        # Case 2: Sub-lesson + Template
        specific_question = extract_block_by_template(question_text, query.template)
        if specific_question:
            return {
                "Sub-lesson": query.sub_lesson,
                "Template": query.template,
                "Question": specific_question
            }
        else:
            raise HTTPException(status_code=404,
                                detail=f"Template '{query.template}' No Sample Question found for this Template.")
    else:
        # Case 1: Only Sub-lesson
        return {
            "Sub-lesson": query.sub_lesson,
            "Question": question_text,
            "Template": template_list
        }
