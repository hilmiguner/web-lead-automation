from web_lead_automation.pages.Outreach_Assistant import main


def test_outreach_page_exposes_main_without_running_on_import() -> None:
    assert callable(main)
