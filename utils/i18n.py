import gettext
from constants.i18n import DOMAIN, LOCALEDIR

def t(locale: str, key: str) -> str:
    i18n = gettext.translation(
        domain=DOMAIN, localedir=LOCALEDIR, fallback=True, languages=[locale]
    )
    i18n.install()
    _ = i18n.gettext
    return _(key)
