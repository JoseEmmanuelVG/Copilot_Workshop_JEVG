from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

QUESTIONS_PATH = Path(__file__).parent / "questions.json"


def load_questions():
    with QUESTIONS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/assessment")
async def get_assessment(request: Request):
    questions = load_questions()
    return templates.TemplateResponse(request, "assessment.html", {"questions": questions})


@app.get("/")
async def root():
    return RedirectResponse(url="/assessment", status_code=302)


@app.post("/submit")
async def submit(request: Request):
    form = await request.form()
    questions = load_questions()
    score = 0
    for q in questions:
        qid = str(q["id"])
        submitted = form.get(qid)
        if submitted is None:
            continue
        if submitted == str(q["answer"]):
            score += 1
    return RedirectResponse(url=f"/result?score={score}", status_code=303)


@app.get("/result")
async def result(request: Request, score: int = 0):
    total = len(load_questions())
    return templates.TemplateResponse(request, "result.html", {"score": score, "total": total})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
