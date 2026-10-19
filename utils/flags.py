"""bleed-style --flag parsing.

    text, flags = parse_flags("hi, hello --self_destruct 10 --reply", {"self_destruct": int, "reply": bool})
    -> ("hi, hello", {"self_destruct": 10, "reply": True})

Type spec values:
    bool  -> a switch; present = True. Also accepts an explicit value: on/off/true/false/yes/no
    int / float / str -> takes the text after the flag up to the next flag
Unknown flags are left in the text untouched.
Em dashes (—) are treated as -- so auto-formatted phones still work.
"""
import re

TRUE = {"on", "true", "yes", "enable", "enabled", "1"}
FALSE = {"off", "false", "no", "disable", "disabled", "0"}


class FlagError(ValueError):
    pass


def to_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in TRUE:
        return True
    if v in FALSE:
        return False
    raise FlagError(f"`{value}` isn't on/off")


def parse_flags(text: str, spec: dict[str, type]) -> tuple[str, dict]:
    text = (text or "").replace("—", "--").replace("–", "--")
    names = "|".join(re.escape(n) for n in sorted(spec, key=len, reverse=True))
    if not names:
        return text.strip(), {}
    pattern = re.compile(rf"(?:^|\s)--({names})(?=\s|$)(.*?)(?=\s--(?:{names})(?:\s|$)|$)", re.S | re.I)
    flags: dict = {}
    spans = []
    for m in pattern.finditer(text):
        name = m.group(1).lower()
        raw = m.group(2).strip()
        typ = spec[name]
        try:
            if typ is bool:
                flags[name] = to_bool(raw) if raw else True
            elif not raw:
                raise FlagError(f"`--{name}` needs a value")
            elif typ is int:
                flags[name] = int(raw.split()[0])
            elif typ is float:
                flags[name] = float(raw.split()[0])
            else:
                flags[name] = raw
        except ValueError as e:
            raise FlagError(str(e) if isinstance(e, FlagError) else f"`--{name}` got an invalid value `{raw}`")
        spans.append(m.span())
    for start, end in reversed(spans):
        text = text[:start] + text[end:]
    return text.strip(), flags
