import pandas as pd
import re


def get_question_data(file_path: str, sub_lesson: str, template: str = None) -> dict:
    # Supported templates for block detection
    template_headers = [
        "Interactive Matching",
        "True / False",
        "MCQ with",
        "Drag and Drop",
        "Sorting",
        "Interactive matching",
        "Timeline",
        "Audio Options plus Images"
    ]
    header_pattern = r"^(" + "|".join(re.escape(t) for t in template_headers) + ")"

    # Step 1: Load the file
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
        else:
            return {"error": "Unsupported file format. Only .csv and .xlsx are allowed."}
    except Exception as e:
        return {"error": f"Error loading file: {str(e)}"}

    # Step 2: Validate essential column
    if 'Sub-lesson' not in df.columns:
        return {"error": "Missing required column: 'Sub-lesson'"}
    if df.empty:
        return {"error": "The file is empty."}

    # Step 3: Find the matching sub-lesson row
    match = df[df['Sub-lesson'].astype(str).str.strip().str.lower() == sub_lesson.strip().lower()]
    if match.empty:
        return {"error": f"Sub-lesson '{sub_lesson}' not found."}

    row = match.iloc[0]

    # Step 4: Extract text content
    revised = row.get('Revised Sample Question- Suggested by Nisha, Tavisha, Diksha, Khadija', '')
    sample = row.get('Sample Questions', '')
    text_block = revised if pd.notna(revised) and revised.strip() else sample

    if not isinstance(text_block, str) or not text_block.strip():
        return {"error": "No valid question text found for this sub-lesson."}

    # Step 5: Extract block by template (if provided)
    if template:
        lines = text_block.splitlines()
        start_idx = None
        end_idx = len(lines)

        # Find the line where template starts
        for i, line in enumerate(lines):
            if template.lower() in line.strip().lower():
                start_idx = i
                break

        if start_idx is None:
            return {"error": f"Template '{template}' not found for this sub-lesson."}

        # Find where the next template block starts (using known headers)
        for j in range(start_idx + 1, len(lines)):
            if re.match(header_pattern, lines[j].strip(), re.IGNORECASE):
                end_idx = j
                break

        extracted_block = "\n".join(lines[start_idx:end_idx]).strip()
        return {
            "Sub-lesson": sub_lesson,
            "Template": template,
            "Question": extracted_block
        }

    # Step 6: If no template, return entire block and template list
    return {
        "Sub-lesson": sub_lesson,
        "Question": text_block,
        "Template": row.get('Templates', '')
    }


result = get_question_data("Untitled tryspreadsheet - Sheet1.csv", "Understand Stories with Clues", template="Sorting")
print(result)
