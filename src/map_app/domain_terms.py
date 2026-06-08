TRUE_STRINGS = {"1", "true", "t", "yes", "y", "on"}
FALSE_STRINGS = {"0", "false", "f", "no", "n", "off", ""}
LOADING_SPINNER_STYLES = {"simple_ring", "piano_keys"}


def get_domain_term_bool(domain_terms, key, default=False):
    if not isinstance(domain_terms, dict):
        return default
    if key not in domain_terms:
        return default
    value = domain_terms.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in TRUE_STRINGS:
            return True
        if normalized in FALSE_STRINGS:
            return False
    return bool(value)


def infer_loading_spinner_style(*values):
    source = " ".join(str(value or "") for value in values).lower()
    if any(token in source for token in ("ピアノ", "piano", "keyboard", "鍵盤")):
        return "piano_keys"
    return "simple_ring"


def normalize_loading_spinner_style(value, *fallback_values):
    normalized = str(value or "").strip().lower()
    if normalized in LOADING_SPINNER_STYLES:
        return normalized
    return infer_loading_spinner_style(*fallback_values)
