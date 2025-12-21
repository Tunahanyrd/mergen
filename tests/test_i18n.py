from src.core.i18n import I18n


def test_i18n_switching():
    I18n.set_language("en")
    assert I18n.get("app_title") == "MERGEN"

    I18n.set_language("tr")
    assert I18n.get("app_title") == "MERGEN"  # Same
    assert I18n.get("general") == "Genel"


def test_i18n_fallback():
    I18n.set_language("en")
    assert I18n.get("non_existent_key") == "non_existent_key"
