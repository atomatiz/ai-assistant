import gettext

domain = "base"
localedir = "./locales"


def t(locale: str, key: str) -> str:
    i18n = gettext.translation(domain, localedir, fallback=True, languages=[locale])
    i18n.install()
    _ = i18n.gettext
    return _(key)
