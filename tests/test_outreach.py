import pytest

from web_lead_automation.services.outreach import generate_outreach_bundle


def test_outreach_bundle_contains_three_distinct_whatsapp_variants_and_phone_opener() -> None:
    bundle = generate_outreach_bundle(
        business_name="Örnek Kuaför",
        sector="kuaför",
    )

    assert [message.key for message in bundle.whatsapp_messages] == [
        "standard",
        "short",
        "direct",
    ]
    assert len({message.text for message in bundle.whatsapp_messages}) == 3
    assert all("Örnek Kuaför" in message.text for message in bundle.whatsapp_messages)
    assert "Örnek Kuaför" in bundle.phone_opener


def test_outreach_uses_conservative_google_profile_wording() -> None:
    bundle = generate_outreach_bundle(business_name="Örnek İşletme")

    combined = "\n".join(message.text for message in bundle.whatsapp_messages)
    combined += "\n" + bundle.phone_opener

    assert "Google'daki işletme profilinizde" in combined
    assert "web siteniz yok" not in combined.casefold()
    assert "resmi bir site değildir" in combined or "resmi siteniz değildir" in combined


def test_demo_link_can_be_included_in_every_whatsapp_variant() -> None:
    bundle = generate_outreach_bundle(
        business_name="Örnek İşletme",
        demo_url="https://demo.example.test/ornek/",
        include_demo_link=True,
    )

    assert bundle.demo_url == "https://demo.example.test/ornek/"
    assert all(
        "https://demo.example.test/ornek/" in message.text
        for message in bundle.whatsapp_messages
    )


def test_demo_link_can_be_omitted_without_losing_saved_url() -> None:
    bundle = generate_outreach_bundle(
        business_name="Örnek İşletme",
        demo_url="https://demo.example.test/ornek",
        include_demo_link=False,
    )

    assert bundle.demo_url == "https://demo.example.test/ornek/"
    assert all("demo.example.test" not in message.text for message in bundle.whatsapp_messages)


def test_missing_demo_url_still_produces_copy_ready_messages() -> None:
    bundle = generate_outreach_bundle(
        business_name="Örnek İşletme",
        demo_url=None,
    )

    assert bundle.demo_url is None
    assert all("Demo:" not in message.text for message in bundle.whatsapp_messages)


def test_invalid_or_credentialed_demo_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="absolute HTTPS"):
        generate_outreach_bundle(
            business_name="Örnek İşletme",
            demo_url="http://example.test/demo",
        )

    with pytest.raises(ValueError, match="credentials"):
        generate_outreach_bundle(
            business_name="Örnek İşletme",
            demo_url="https://user:pass@example.test/demo",
        )


def test_business_and_sector_values_are_normalized_to_single_line() -> None:
    bundle = generate_outreach_bundle(
        business_name="  Örnek\nKuaför  ",
        sector="  güzellik\nmerkezi ",
    )

    direct = bundle.whatsapp_messages[2].text
    assert "Örnek Kuaför" in direct
    assert "güzellik merkezi işletmeniz" in direct


def test_blank_business_name_is_rejected() -> None:
    with pytest.raises(ValueError, match="business_name"):
        generate_outreach_bundle(business_name="   ")
