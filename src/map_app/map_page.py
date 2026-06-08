import re

from map_app.domain import map_css_link_tags, map_js_script_tags


def get_theme_color(site_settings):
    terms = site_settings.get_domain_terms()
    header_bg_mode = (terms.get("header_bg_mode") or "gradient").strip()
    if header_bg_mode == "solid":
        return (terms.get("header_bg_solid_color") or "#667eea").strip()
    return (terms.get("header_bg_gradient_from") or "#667eea").strip()


def get_header_background(site_settings):
    terms = site_settings.get_domain_terms()
    header_bg_mode = (terms.get("header_bg_mode") or "gradient").strip()
    if header_bg_mode == "solid":
        return (terms.get("header_bg_solid_color") or "#667eea").strip()

    gradient_from = (terms.get("header_bg_gradient_from") or "#667eea").strip()
    gradient_to = (terms.get("header_bg_gradient_to") or "#764ba2").strip()
    try:
        gradient_angle = int(terms.get("header_bg_gradient_angle", 135))
    except (TypeError, ValueError):
        gradient_angle = 135
    gradient_angle = max(0, min(360, gradient_angle))
    return f"linear-gradient({gradient_angle}deg, {gradient_from} 0%, {gradient_to} 100%)"


def normalize_document_meta(html, theme_color):
    viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />'
    theme_meta = f'<meta name="theme-color" content="{theme_color}" />'
    html = re.sub(r'<meta[^>]+name=["\']viewport["\'][^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<meta[^>]+name=["\']theme-color["\'][^>]*>', '', html, flags=re.IGNORECASE)
    injection = f"\n    {viewport_meta}\n    {theme_meta}\n"
    return re.sub(r'(<head[^>]*>)', r"\1" + injection, html, count=1, flags=re.IGNORECASE)


def get_css_styles(site_settings):
    favicon_tag = ""
    if site_settings.favicon:
        favicon_tag = f'<link rel="icon" href="{site_settings.favicon.url}">'
    terms = site_settings.get_domain_terms()
    theme_color = get_theme_color(site_settings)
    header_background = get_header_background(site_settings)
    loading_spinner_style = (terms.get("loading_spinner_style") or "simple_ring").strip()

    return f"""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
    <meta name="theme-color" content="{theme_color}" />
    {favicon_tag}
{map_css_link_tags()}
    <style>
      :root {{
        --map-safe-area-bg: {header_background};
      }}
      html, body {{
        background: {header_background} !important;
      }}
      html::before {{
        background: {header_background} !important;
      }}
    </style>
    <script>
      (function() {{
        document.documentElement.dataset.loadingStyle = "{loading_spinner_style}";
        var desired = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover";
        var metas = document.querySelectorAll('meta[name="viewport"]');
        if (!metas.length) {{
          var m = document.createElement('meta');
          m.name = 'viewport';
          m.content = desired;
          document.head.appendChild(m);
          return;
        }}
        metas.forEach(function(m) {{ m.setAttribute('content', desired); }});
      }})();
    </script>
    """


def get_javascript(map_id):
    return f"""
{map_js_script_tags()}
    <script>
        bindMarkerEvents('{map_id}');
    </script>
    """


def build_marker_icon_html(icon_color):
    return f"""
    <div style="position: relative;">
        <div style="
            width: 35px;
            height: 45px;
            background: {icon_color};
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            border: 3px solid white;
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        "></div>
        <div style="
            position: absolute;
            top: 8px;
            left: 8px;
            width: 19px;
            height: 19px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <i class="fa fa-music" style="
                color: {icon_color};
                font-size: 10px;
                transform: rotate(45deg);
            "></i>
        </div>
    </div>
    """
