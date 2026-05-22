TRUE_STRINGS = {"1", "true", "t", "yes", "y", "on"}
FALSE_STRINGS = {"0", "false", "f", "no", "n", "off", ""}


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
