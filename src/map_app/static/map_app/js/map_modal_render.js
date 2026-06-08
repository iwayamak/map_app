var DEFAULT_MAP_TERMS = {
    use_record_items: true,
    modal_records_title: "記録項目",
    modal_empty_records_text: "記録なし",
    modal_note_title: "メモ",
    modal_count_label: "累積記録数",
    modal_title_icon: "📍",
    modal_photo_profile: "preserve",
    modal_photo_stage_max_height_vh: 70,
    modal_sections: {
        access: true,
        meta: true,
        custom_fields: true,
        detail_note: true,
        records: true,
        tags: true,
        photos: true
    },
    system_info_only_tag_label: "情報のみ表示",
    system_piano_info_only_tag_label: "情報のみ表示"
};

function coerceBoolean(value, defaultValue) {
    if (typeof value === "boolean") return value;
    if (typeof value === "number") return value !== 0;
    if (typeof value === "string") {
        var normalized = value.trim().toLowerCase();
        if (normalized === "true" || normalized === "1" || normalized === "yes" || normalized === "on") return true;
        if (normalized === "false" || normalized === "0" || normalized === "no" || normalized === "off" || normalized === "") return false;
    }
    if (value === null || value === undefined) return defaultValue;
    return Boolean(value);
}

function getMapTerms() {
    var node = document.getElementById("map-domain-terms");
    if (!node || !node.textContent) return DEFAULT_MAP_TERMS;
    try {
        var parsed = JSON.parse(node.textContent);
        return Object.assign({}, DEFAULT_MAP_TERMS, parsed || {});
    } catch (error) {
        return DEFAULT_MAP_TERMS;
    }
}

function isModalSectionActive(sectionKey) {
    var terms = getMapTerms();
    var sections = terms && terms.modal_sections && typeof terms.modal_sections === "object"
        ? terms.modal_sections
        : {};
    if (!Object.prototype.hasOwnProperty.call(sections, sectionKey)) {
        return true;
    }
    return coerceBoolean(sections[sectionKey], true);
}

function getModalPhotoConfig() {
    var terms = getMapTerms();
    var profile = String((terms && terms.modal_photo_profile) || "preserve");
    if (profile !== "preserve" && profile !== "fit_width" && profile !== "fill") {
        profile = "preserve";
    }
    var maxHeightVh = parseInt((terms && terms.modal_photo_stage_max_height_vh), 10);
    if (!Number.isFinite(maxHeightVh)) {
        maxHeightVh = 70;
    }
    maxHeightVh = Math.max(40, Math.min(90, maxHeightVh));
    return { profile: profile, maxHeightVh: maxHeightVh };
}

function buildLoadingModalHtml() {
    var spinnerHtml = window.MapAppLoadingSpinner
        ? window.MapAppLoadingSpinner.render("activity-modal-spinner")
        : "<div class='activity-modal-spinner' aria-hidden='true'><span class='map-loading-ring'></span></div>";
    return (
        "<div class='activity-modal-content activity-modal-loading'>" +
            spinnerHtml +
            "<p class='activity-modal-loading-text'>読み込み中</p>" +
        "</div>"
    );
}

function buildErrorModalHtml() {
    return "<div class='activity-modal-content'>詳細の読み込みに失敗しました。</div>";
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function escapeJsString(value) {
    return String(value)
        .replace(/\\/g, "\\\\")
        .replace(/\"/g, "\\\"")
        .replace(/'/g, "\\'");
}

function escapeHtmlWithLineBreaks(value) {
    return escapeHtml(value).replace(/\r?\n/g, "<br>");
}

function splitTrailingUrlPunctuation(value) {
    var punctuation = "";
    var text = String(value || "");
    while (/[),.!?]$/.test(text)) {
        punctuation = text.slice(-1) + punctuation;
        text = text.slice(0, -1);
    }
    return { url: text, trailing: punctuation };
}

function getReadableUrlLabel(rawUrl, previewMap) {
    if (previewMap && previewMap[rawUrl] && previewMap[rawUrl].title) {
        try {
            var parsedWithTitle = new URL(rawUrl);
            return {
                host: parsedWithTitle.hostname.replace(/^www\./, ""),
                summary: String(previewMap[rawUrl].title),
            };
        } catch (error) {
            return {
                host: rawUrl,
                summary: String(previewMap[rawUrl].title),
            };
        }
    }
    try {
        var parsedUrl = new URL(rawUrl);
        var host = parsedUrl.hostname.replace(/^www\./, "");
        var path = (parsedUrl.pathname || "").replace(/\/$/, "");
        var trimmedPath = path && path !== "/" ? path : "";
        var summary = trimmedPath ? host + trimmedPath : host;
        if (summary.length > 36) {
            summary = summary.slice(0, 33) + "...";
        }
        return {
            host: host,
            summary: summary || host,
        };
    } catch (error) {
        return {
            host: rawUrl,
            summary: rawUrl,
        };
    }
}

function getLinkIconHtml(rawUrl, previewMap) {
    var faviconUrl = previewMap && previewMap[rawUrl] ? previewMap[rawUrl].favicon_url : "";
    if (faviconUrl) {
        return "<img class='activity-modal-detail-note-favicon' src='" + escapeHtml(faviconUrl) + "' alt='' loading='lazy' referrerpolicy='no-referrer' onerror='this.style.display=\"none\"; this.nextElementSibling.style.display=\"inline-flex\";' />" +
            "<span class='activity-modal-detail-note-link-icon activity-modal-detail-note-link-icon--fallback' aria-hidden='true' style='display:none;'>↗</span>";
    }
    return "<span class='activity-modal-detail-note-link-icon' aria-hidden='true'>↗</span>";
}

function renderTextWithLinksAndLineBreaks(value) {
    var text = String(value || "");
    var urlPattern = /(https?:\/\/[^\s<]+)/g;
    var lastIndex = 0;
    var html = "";
    var match;
    var previewMap = arguments.length > 1 ? arguments[1] : null;

    while ((match = urlPattern.exec(text)) !== null) {
        var rawUrl = match[0];
        var parts = splitTrailingUrlPunctuation(rawUrl);
        var url = parts.url;
        var trailing = parts.trailing;
        var urlLabel = getReadableUrlLabel(url, previewMap);

        html += escapeHtmlWithLineBreaks(text.slice(lastIndex, match.index));
        html += "<a class='activity-modal-detail-note-link' href='" + escapeHtml(url) + "' target='_blank' rel='noopener noreferrer'>" +
            getLinkIconHtml(url, previewMap) +
            "<span class='activity-modal-detail-note-link-copy'>" +
                "<span class='activity-modal-detail-note-link-title'>" + escapeHtml(urlLabel.summary) + "</span>" +
                "<span class='activity-modal-detail-note-link-host'>" + escapeHtml(urlLabel.host) + "</span>" +
            "</span>" +
        "</a>";
        html += escapeHtml(trailing);
        lastIndex = match.index + rawUrl.length;
    }

    html += escapeHtmlWithLineBreaks(text.slice(lastIndex));
    return html;
}

function renderHeaderGuideHtml(activity) {
    if (!isModalSectionActive("access")) {
        return "";
    }
    var items = [];
    var station = activity && activity.nearest_station ? escapeHtml(activity.nearest_station) : "";
    var walkingMinutes = activity && Number.isInteger(activity.walking_minutes)
        ? activity.walking_minutes
        : null;
    var scheduleNote = activity && activity.playable_schedule_note
        ? escapeHtml(activity.playable_schedule_note)
        : "";

    if (station || walkingMinutes !== null) {
        var accessValue = station;
        if (walkingMinutes !== null) {
            accessValue = accessValue
                ? accessValue + " 徒歩 " + escapeHtml(walkingMinutes) + "分"
                : "徒歩 " + escapeHtml(walkingMinutes) + "分";
        }
        items.push(
            "<div class='activity-modal-guide-item'>" +
                "<span class='activity-modal-guide-label'>アクセス</span>" +
                "<span class='activity-modal-guide-value'>" + accessValue + "</span>" +
            "</div>"
        );
    }
    if (scheduleNote) {
        items.push(
            "<div class='activity-modal-guide-item activity-modal-guide-item--wide'>" +
                "<span class='activity-modal-guide-label'>利用案内</span>" +
                "<span class='activity-modal-guide-note-text'>" + scheduleNote + "</span>" +
            "</div>"
        );
    }

    if (items.length === 0) {
        return "";
    }
    return "<div class='activity-modal-guide'>" + items.join("") + "</div>";
}

function renderActivityItemsSection(activity) {
    if (!isModalSectionActive("records")) {
        return "";
    }
    var terms = getMapTerms();
    if (!coerceBoolean(terms.use_record_items, true)) {
        return "";
    }
    var activityItems = activity && Array.isArray(activity.activity_items) ? activity.activity_items : [];
    if (activity && (activity.status_badge === "未訪問" || isPianoInfoOnlyMode())) {
        return "";
    }
    if (activityItems.length === 0) {
        return (
            "<div class='activity-modal-items'>" +
                "<div class='activity-modal-section-title'>🎵 " + escapeHtml(terms.modal_records_title) + "</div>" +
                "<div class='activity-modal-empty-text'>" + escapeHtml(terms.modal_empty_records_text) + "</div>" +
            "</div>"
        );
    }
    return (
        "<div class='activity-modal-items'>" +
            "<div class='activity-modal-section-title'>🎵 " + escapeHtml(terms.modal_records_title) + "</div>" +
            "<ol class='activity-modal-item-list'>" + activityItems.map(function(itemName) {
                return "<li>" + escapeHtml(itemName) + "</li>";
            }).join("") + "</ol>" +
        "</div>"
    );
}

function renderDetailNoteSection(activity) {
    if (!isModalSectionActive("detail_note")) {
        return "";
    }
    var terms = getMapTerms();
    var detailNote = activity && activity.detail_note ? String(activity.detail_note).trim() : "";
    var detailNoteLinkPreviews = activity && activity.detail_note_link_previews ? activity.detail_note_link_previews : null;
    if (!detailNote) {
        return "";
    }

    return (
        "<div class='activity-modal-detail-note'>" +
            "<div class='activity-modal-section-title'>📝 " + escapeHtml(terms.modal_note_title) + "</div>" +
            "<div class='activity-modal-detail-note-body'>" + renderTextWithLinksAndLineBreaks(detailNote, detailNoteLinkPreviews) + "</div>" +
        "</div>"
    );
}

function renderCustomFieldsSection(activity) {
    return "";
}

function renderTagsHtml(tags) {
    if (!isModalSectionActive("tags")) {
        return "";
    }
    if (!Array.isArray(tags) || tags.length === 0) return "";

    var chips = tags.map(function(tag) {
        var name = "";
        var color = "#4b5563";
        var textColor = "#f9fafb";
        if (typeof tag === "string") {
            name = tag;
        } else if (tag && typeof tag === "object") {
            name = tag.name || "";
            color = tag.color || color;
            textColor = tag.text_color || textColor;
        }
        return (
            "<button type='button' class='activity-modal-tag-chip' data-tag-name='" + escapeHtml(name) + "' style='background:" + escapeHtml(color) + ";color:" + escapeHtml(textColor) + ";' aria-label='タグ " + escapeHtml(name) + " で検索'>" +
                escapeHtml(name) +
            "</button>"
        );
    }).join("");

    return (
        "<div class='activity-modal-tags'>" +
            "<div class='activity-modal-section-title'>🏷️ タグ</div>" +
            "<div class='activity-modal-tag-list'>" + chips + "</div>" +
        "</div>"
    );
}

function renderPhotosHtml(activity) {
    if (!isModalSectionActive("photos")) {
        return "";
    }
    var photoAssets = Array.isArray(activity.photo_assets) ? activity.photo_assets : [];
    if (photoAssets.length === 0 && Array.isArray(activity.photo_urls)) {
        photoAssets = activity.photo_urls.map(function(url) {
            return { thumb_url: url, medium_url: url, full_url: url };
        });
    }
    if (photoAssets.length > 0) {
        var photoConfig = getModalPhotoConfig();
        var galleryId = "location-gallery-" + String(activity.id);
        var thumbsHtml = photoAssets.map(function(photo, index) {
            var thumbUrl = photo.thumb_url || photo.medium_url || photo.full_url;
            var mediumUrl = photo.medium_url || photo.full_url || thumbUrl;
            var fullUrl = photo.full_url || mediumUrl || thumbUrl;
            var thumbUrlHtml = escapeHtml(thumbUrl);
            var mediumUrlHtml = escapeHtml(mediumUrl);
            var fullUrlHtml = escapeHtml(fullUrl);
            var mediumUrlJs = escapeJsString(mediumUrl);
            var fullUrlJs = escapeJsString(fullUrl);
            var activeClass = index === 0 ? " is-active" : "";
            return (
                "<button type='button'" +
                    " class='location-photo-thumb" + activeClass + "'" +
                    " data-image-url='" + mediumUrlHtml + "'" +
                    " onclick='setLocationGalleryImage(\"" + galleryId + "\", \"" + mediumUrlJs + "\", \"" + fullUrlJs + "\", this)'" +
                    " aria-label='写真" + (index + 1) + "を表示'>" +
                    "<img src='" + thumbUrlHtml + "' alt='写真 " + (index + 1) + "' />" +
                "</button>"
            );
        }).join("");

        var first = photoAssets[0];
        var firstMedium = first.medium_url || first.full_url || first.thumb_url;
        var firstFull = first.full_url || firstMedium;

        return (
            "<div class='location-photo-gallery activity-modal-gallery'>" +
                "<div class='activity-modal-section-title'>📸 写真（" + photoAssets.length + "枚）</div>" +
                "<div class='location-photo-main-wrapper location-photo-main-wrapper--" + photoConfig.profile + "'" +
                    " style='height:clamp(260px,48vh,520px);--photo-stage-max-height:" + photoConfig.maxHeightVh + "vh;'>" +
                    "<div id='" + galleryId + "-bg' class='location-photo-main-stage-bg' style='background-image:url(\"" + escapeHtml(firstMedium) + "\")'></div>" +
                    "<img id='" + galleryId + "-main'" +
                        " class='location-photo-main'" +
                        " src='" + escapeHtml(firstMedium) + "'" +
                        " data-full-url='" + escapeHtml(firstFull) + "'" +
                        " data-gallery-id='" + galleryId + "'" +
                        " alt='写真 1'" +
                        " onclick='showImageModal(this.dataset.fullUrl || this.src)' />" +
                "</div>" +
                "<div class='location-photo-thumbs'>" + thumbsHtml + "</div>" +
                "<p class='activity-modal-photo-hint'>📷 下の写真で切り替え / タップで拡大表示</p>" +
            "</div>"
        );
    }

    if (activity.legacy_image_url) {
        return (
            "<div class='location-photo-gallery activity-modal-gallery'>" +
                "<div class='activity-modal-section-title'>📸 写真</div>" +
                "<div class='location-photo-main-wrapper' style='height:clamp(260px,48vh,520px)'>" +
                    "<div class='location-photo-main-stage-bg' style='background-image:url(\"" + escapeHtml(activity.legacy_image_url) + "\")'></div>" +
                    "<img class='location-photo-main'" +
                        " src='" + escapeHtml(activity.legacy_image_url) + "'" +
                        " alt='ピアノ設置場所の写真'" +
                        " data-full-url='" + escapeHtml(activity.legacy_image_url) + "'" +
                        " onclick='showImageModal(this.dataset.fullUrl || this.src)' />" +
                "</div>" +
                "<p class='activity-modal-photo-hint'>📷 タップして拡大表示</p>" +
            "</div>"
        );
    }

    return "";
}

function isPianoInfoOnlyMode() {
    var terms = getMapTerms();
    var candidates = [];
    if (terms && terms.system_info_only_tag_label) candidates.push(String(terms.system_info_only_tag_label));
    if (terms && terms.system_piano_info_only_tag_label) candidates.push(String(terms.system_piano_info_only_tag_label));
    candidates.push("情報のみ表示", "ピアノ情報のみ表示");
    return candidates.some(function(label) {
        var selector = "input[name='tags'][value='" + label.replace(/'/g, "\\'") + "']:checked";
        return Boolean(document.querySelector(selector));
    });
}

function renderMetaSection(activity) {
    if (!isModalSectionActive("meta")) {
        return "";
    }
    var terms = getMapTerms();
    if (isPianoInfoOnlyMode()) {
        return "";
    }
    return (
        "<div class='activity-modal-meta'>" +
            "<div class='activity-modal-meta-row activity-modal-meta-row-inline'>" +
                "<div class='activity-modal-meta-item'>" +
                    "<span class='activity-modal-label'>" + escapeHtml(terms.modal_count_label) + "</span>" +
                    "<span class='activity-modal-count'>" + escapeHtml(activity.current_count || 0) + "回</span>" +
                "</div>" +
                "<div class='activity-modal-meta-item'>" +
                    "<span class='activity-modal-label'>訪問区分</span>" +
                    "<span class='activity-modal-badge' style='background: " + escapeHtml(activity.badge_color || "#3b82f6") + ";'>" +
                        escapeHtml(activity.status_badge || "") +
                    "</span>" +
                "</div>" +
        "</div>" +
        "</div>"
    );
}

function buildModalHeaderStyle(terms) {
    var mode = String((terms && terms.header_bg_mode) || "gradient");
    var solidColor = String((terms && terms.header_bg_solid_color) || "#667eea");
    var gradientFrom = String((terms && terms.header_bg_gradient_from) || "#667eea");
    var gradientTo = String((terms && terms.header_bg_gradient_to) || "#764ba2");
    var gradientAngle = parseInt((terms && terms.header_bg_gradient_angle), 10);
    if (!Number.isFinite(gradientAngle)) gradientAngle = 135;
    gradientAngle = Math.max(0, Math.min(360, gradientAngle));

    if (mode === "solid") {
        return "background:" + escapeHtml(solidColor) + ";";
    }
    return (
        "background:linear-gradient(" + gradientAngle + "deg, " +
        escapeHtml(gradientFrom) + " 0%, " +
        escapeHtml(gradientTo) + " 100%);"
    );
}

function renderActivityModal(activity) {
    var terms = getMapTerms();
    var modalTitleIcon = (terms && terms.modal_title_icon) ? String(terms.modal_title_icon).trim() : "";
    if (!modalTitleIcon) {
        modalTitleIcon = "📍";
    }
    return (
        "<div class='activity-modal-content'>" +
            "<div class='activity-modal-header' style='" + buildModalHeaderStyle(terms) + "'>" +
                "<div class='activity-modal-title'>" +
                    escapeHtml(modalTitleIcon) + " " + escapeHtml(activity.location_name || "") +
                "</div>" +
                "<div class='activity-modal-date'>📅 " + escapeHtml(activity.date || "") + "</div>" +
                renderHeaderGuideHtml(activity) +
            "</div>" +
            renderMetaSection(activity) +
            renderCustomFieldsSection(activity) +
            renderDetailNoteSection(activity) +
            renderActivityItemsSection(activity) +
            renderTagsHtml(activity.tags) +
            renderPhotosHtml(activity) +
        "</div>"
    );
}
