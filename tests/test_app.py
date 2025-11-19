from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_get_assessment():
    r = client.get("/assessment")
    assert r.status_code == 200
    assert "Assessment" in r.text
    assert "What is the capital of France?" in r.text


def test_submit_and_result():
    # Submit answers: first correct (a), second correct (b)
    data = {"1": "a", "2": "b"}
    r = client.post("/submit", data=data)
    # TestClient may follow redirects; accept either a redirect response or the final page
    assert r.status_code in (200, 303)
    if r.status_code == 303:
        location = r.headers.get("location")
        assert location is not None
        r2 = client.get(location)
        assert r2.status_code == 200
        assert "You scored" in r2.text
    else:
        assert "You scored" in r.text
