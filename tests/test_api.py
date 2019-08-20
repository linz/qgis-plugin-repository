from src.plugin.api import app

app.config["TESTING"] = True


def test_upload():
    assert app.config["TESTING"]
