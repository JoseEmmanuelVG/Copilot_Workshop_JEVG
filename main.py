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
    # Require a username cookie to access the assessment
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/", status_code=302)

    questions = load_questions()
    return templates.TemplateResponse("assessment.html", {"request": request, "questions": questions, "username": username})


@app.get("/")
async def root(request: Request):
    # If username cookie present, go straight to assessment
    username = request.cookies.get("username")
    if username:
        return RedirectResponse(url="/assessment", status_code=302)
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.post("/welcome")
async def welcome_submit(request: Request):
    form = await request.form()
    username = form.get("username")
    if not username:
        return templates.TemplateResponse("welcome.html", {"request": request, "error": "Please enter a username"})
    response = RedirectResponse(url="/assessment", status_code=303)
    response.set_cookie(key="username", value=username)
    return response


@app.post("/submit")
async def submit(request: Request):
    form = await request.form()
    questions = load_questions()
    score = 0
    for q in questions:
        qid = str(q["id"])
        # If the stored answer is a list, treat this as a multi-choice question
        if isinstance(q.get("answer"), list):
            # getlist returns all values for this field (checkboxes)
            submitted = form.getlist(qid)
            if not submitted:
                continue
            # Compare as sets (order doesn't matter)
            if set(map(str, submitted)) == set(map(str, q["answer"])):
                score += 1
        else:
            submitted = form.get(qid)
            if submitted is None:
                continue
            if submitted == str(q["answer"]):
                score += 1
    return RedirectResponse(url=f"/result?score={score}", status_code=303)


@app.get("/result")
async def result(request: Request, score: int = 0):
    total = len(load_questions())
    username = request.cookies.get("username")
    return templates.TemplateResponse("result.html", {"request": request, "score": score, "total": total, "username": username})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)