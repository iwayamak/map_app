from map_app.domain import map_css_link_tags, map_js_script_tags


def get_css_styles(site_settings):
    favicon_tag = ""
    if site_settings.favicon:
        favicon_tag = f'<link rel="icon" href="{site_settings.favicon.url}">'

    return f"""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    {favicon_tag}
{map_css_link_tags()}
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
