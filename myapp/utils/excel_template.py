from openpyxl import Workbook

def generate_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "Questions"

    ws.append([
        "Category", "Quiz Title", "Question",
        "Option A", "Option B", "Option C", "Option D",
        "Correct (A,B,C)", "Difficulty", "Marks"
    ])

    for i in range(30):
        ws.append([
            "Science", "Science Master Quiz",
            f"Sample Question {i+1}",
            "Option A", "Option B", "Option C", "Option D",
            "A", "easy", 1
        ])

    return wb