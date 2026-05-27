from map_app.domain import get_site_settings_model


def load_site_context():
    SiteSettings = get_site_settings_model()
    loader = getattr(SiteSettings, "load_cached", SiteSettings.load)
    site_settings = loader()
    domain_terms = site_settings.get_domain_terms()
    return site_settings, domain_terms
