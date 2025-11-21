from fastapi.testclient import TestClient
import main


client = TestClient(main.app)


# Define 5 simple mocked questions for deterministic tests
SAMPLE_QUESTIONS = [
    {"id": 1, "text": "What does len([1,2]) return?", "options": [{"value": "a", "text": "1"}, {"value": "b", "text": "2"}], "answer": "b"},
    {"id": 2, "text": "Which keyword defines a function?", "options": [{"value": "a", "text": "def"}, {"value": "b", "text": "func"}], "answer": "a"},
    {"id": 3, "text": "What is '3' + '4'?", "options": [{"value": "a", "text": "7"}, {"value": "b", "text": "34"}], "answer": "b"},
    {"id": 4, "text": "Which is a mutable type?", "options": [{"value": "a", "text": "tuple"}, {"value": "b", "text": "list"}], "answer": "b"},
    {"id": 5, "text": "Which built-in gets length?", "options": [{"value": "a", "text": "len"}, {"value": "b", "text": "size"}], "answer": "a"}
]


from html import unescape


def test_get_assessment_contains_questions(monkeypatch):
    # Mock load_questions to return our deterministic set
    monkeypatch.setattr(main, "load_questions", lambda: SAMPLE_QUESTIONS)

    # set the username cookie so access control allows assessment
    client.cookies.set("username", "tester")
    r = client.get("/assessment")
    assert r.status_code == 200
    page = unescape(r.text)
    for q in SAMPLE_QUESTIONS:
        assert q["text"] in page


def test_post_submit_redirect_and_score(monkeypatch):
    monkeypatch.setattr(main, "load_questions", lambda: SAMPLE_QUESTIONS)

    # Prepare all-correct answers
    data = {str(q["id"]): q["answer"] for q in SAMPLE_QUESTIONS}
    # set username cookie so submit is allowed
    client.cookies.set("username", "tester")
    r = client.post("/submit", data=data)

    # TestClient may follow redirects automatically; check history for a 303
    redirected = any(h.status_code == 303 for h in r.history) or r.status_code == 303
    assert redirected, "POST /submit should perform a redirect when answers are submitted"

    # Determine final response (follow location if needed)
    if r.status_code == 303:
        location = r.headers.get("location")
        assert location, "Redirect response must include Location header"
        r2 = client.get(location)
    else:
        r2 = r

    assert r2.status_code == 200
    # Score should equal total number of questions (all-correct)
    total = len(SAMPLE_QUESTIONS)
    assert f"{total} / {total}" in r2.text


def test_result_route_returns_200(monkeypatch):
    monkeypatch.setattr(main, "load_questions", lambda: SAMPLE_QUESTIONS)
    r = client.get("/result?score=2")
    assert r.status_code == 200
    assert "2 /" in r.text
