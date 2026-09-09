from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_dashboard_renders_without_api_key() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path).run()

    assert not app.exception
    assert app.title[0].value == "Web Lead Automation"
    assert app.text_input[0].label == "Bölge"
    assert app.text_input[0].value == "Gemlik Bursa"
    assert app.selectbox[0].label == "Sektör"
    assert app.button[0].label == "Lead Ara"
    assert app.warning
