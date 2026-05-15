var DEFAULT_MAP_TERMS = {
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
    return Boolean(sections[sectionKey]);
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
    return (
        "<div class='performance-modal-content performance-modal-loading'>" +
            "<div class='performance-modal-spinner' aria-hidden='true'></div>" +
            "<p class='performance-modal-loading-text'>読み込み中...</p>" +
        "</div>"
    );
}

function buildErrorModalHtml() {
    return "<div class='performance-modal-content'>詳細の読み込みに失敗しました。</div>";
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
        return "<img class='performance-modal-detail-note-favicon' src='" + escapeHtml(faviconUrl) + "' alt='' loading='lazy' referrerpolicy='no-referrer' onerror='this.style.display=\"none\"; this.nextElementSibling.style.display=\"inline-flex\";' />" +
            "<span class='performance-modal-detail-note-link-icon performance-modal-detail-note-link-icon--fallback' aria-hidden='true' style='display:none;'>↗</span>";
    }
    return "<span class='performance-modal-detail-note-link-icon' aria-hidden='true'>↗</span>";
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
        html += "<a class='performance-modal-detail-note-link' href='" + escapeHtml(url) + "' target='_blank' rel='noopener noreferrer'>" +
            getLinkIconHtml(url, previewMap) +
            "<span class='performance-modal-detail-note-link-copy'>" +
                "<span class='performance-modal-detail-note-link-title'>" + escapeHtml(urlLabel.summary) + "</span>" +
                "<span class='performance-modal-detail-note-link-host'>" + escapeHtml(urlLabel.host) + "</span>" +
            "</span>" +
        "</a>";
        html += escapeHtml(trailing);
        lastIndex = match.index + rawUrl.length;
    }

    html += escapeHtmlWithLineBreaks(text.slice(lastIndex));
    return html;
}

function renderHeaderGuideHtml(performance) {
    if (!isModalSectionActive("access")) {
        return "";
    }
    var items = [];
    var station = performance && performance.nearest_station ? escapeHtml(performance.nearest_station) : "";
    var walkingMinutes = performance && Number.isInteger(performance.walking_minutes)
        ? performance.walking_minutes
        : null;
    var scheduleNote = performance && performance.playable_schedule_note
        ? escapeHtml(performance.playable_schedule_note)
        : "";

    if (station || walkingMinutes !== null) {
        var accessValue = station;
        if (walkingMinutes !== null) {
            accessValue = accessValue
                ? accessValue + " 徒歩 " + escapeHtml(walkingMinutes) + "分"
                : "徒歩 " + escapeHtml(walkingMinutes) + "分";
        }
        items.push(
            "<div class='performance-modal-guide-item'>" +
                "<span class='performance-modal-guide-label'>アクセス</span>" +
                "<span class='performance-modal-guide-value'>" + accessValue + "</span>" +
            "</div>"
        );
    }
    if (scheduleNote) {
        items.push(
            "<div class='performance-modal-guide-item performance-modal-guide-item--wide'>" +
                "<span class='performance-modal-guide-label'>利用案内</span>" +
                "<span class='performance-modal-guide-note-text'>" + scheduleNote + "</span>" +
            "</div>"
        );
    }

    if (items.length === 0) {
        return "";
    }
    return "<div class='performance-modal-guide'>" + items.join("") + "</div>";
}

function renderSongsSection(performance) {
    if (!isModalSectionActive("records")) {
        return "";
    }
    var terms = getMapTerms();
    var songs = performance && Array.isArray(performance.songs) ? performance.songs : [];
    if (performance && (performance.status_badge === "未訪問" || isPianoInfoOnlyMode())) {
        return "";
    }
    if (songs.length === 0) {
        return (
            "<div class='performance-modal-songs'>" +
                "<div class='performance-modal-section-title'>🎵 " + escapeHtml(terms.modal_records_title) + "</div>" +
                "<div class='performance-modal-empty-text'>" + escapeHtml(terms.modal_empty_records_text) + "</div>" +
            "</div>"
        );
    }
    return (
        "<div class='performance-modal-songs'>" +
            "<div class='performance-modal-section-title'>🎵 " + escapeHtml(terms.modal_records_title) + "</div>" +
            "<ol class='performance-modal-song-list'>" + songs.map(function(song) {
                return "<li>" + escapeHtml(song) + "</li>";
            }).join("") + "</ol>" +
        "</div>"
    );
}

function renderDetailNoteSection(performance) {
    if (!isModalSectionActive("detail_note")) {
        return "";
    }
    var terms = getMapTerms();
    var detailNote = performance && performance.detail_note ? String(performance.detail_note).trim() : "";
    var detailNoteLinkPreviews = performance && performance.detail_note_link_previews ? performance.detail_note_link_previews : null;
    if (!detailNote) {
        return "";
    }

    return (
        "<div class='performance-modal-detail-note'>" +
            "<div class='performance-modal-section-title'>📝 " + escapeHtml(terms.modal_note_title) + "</div>" +
            "<div class='performance-modal-detail-note-body'>" + renderTextWithLinksAndLineBreaks(detailNote, detailNoteLinkPreviews) + "</div>" +
        "</div>"
    );
}

function renderCustomFieldsSection(performance) {
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
            "<button type='button' class='performance-modal-tag-chip' data-tag-name='" + escapeHtml(name) + "' style='background:" + escapeHtml(color) + ";color:" + escapeHtml(textColor) + ";' aria-label='タグ " + escapeHtml(name) + " で検索'>" +
                escapeHtml(name) +
            "</button>"
        );
    }).join("");

    return (
        "<div class='performance-modal-tags'>" +
            "<div class='performance-modal-section-title'>🏷️ タグ</div>" +
            "<div class='performance-modal-tag-list'>" + chips + "</div>" +
        "</div>"
    );
}

function renderPhotosHtml(performance) {
    if (!isModalSectionActive("photos")) {
        return "";
    }
    var photoAssets = Array.isArray(performance.photo_assets) ? performance.photo_assets : [];
    if (photoAssets.length === 0 && Array.isArray(performance.photo_urls)) {
        photoAssets = performance.photo_urls.map(function(url) {
            return { thumb_url: url, medium_url: url, full_url: url };
        });
    }
    if (photoAssets.length > 0) {
        var photoConfig = getModalPhotoConfig();
        var galleryId = "location-gallery-" + String(performance.id);
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
            "<div class='location-photo-gallery performance-modal-gallery'>" +
                "<div class='performance-modal-section-title'>📸 写真（" + photoAssets.length + "枚）</div>" +
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
                "<p class='performance-modal-photo-hint'>📷 下の写真で切り替え / タップで拡大表示</p>" +
            "</div>"
        );
    }

    if (performance.legacy_image_url) {
        return (
            "<div class='location-photo-gallery performance-modal-gallery'>" +
                "<div class='performance-modal-section-title'>📸 写真</div>" +
                "<div class='location-photo-main-wrapper' style='height:clamp(260px,48vh,520px)'>" +
                    "<div class='location-photo-main-stage-bg' style='background-image:url(\"" + escapeHtml(performance.legacy_image_url) + "\")'></div>" +
                    "<img class='location-photo-main'" +
                        " src='" + escapeHtml(performance.legacy_image_url) + "'" +
                        " alt='ピアノ設置場所の写真'" +
                        " data-full-url='" + escapeHtml(performance.legacy_image_url) + "'" +
                        " onclick='showImageModal(this.dataset.fullUrl || this.src)' />" +
                "</div>" +
                "<p class='performance-modal-photo-hint'>📷 タップして拡大表示</p>" +
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

function renderMetaSection(performance) {
    if (!isModalSectionActive("meta")) {
        return "";
    }
    var terms = getMapTerms();
    if (isPianoInfoOnlyMode()) {
        return "";
    }
    return (
        "<div class='performance-modal-meta'>" +
            "<div class='performance-modal-meta-row performance-modal-meta-row-inline'>" +
                "<div class='performance-modal-meta-item'>" +
                    "<span class='performance-modal-label'>" + escapeHtml(terms.modal_count_label) + "</span>" +
                    "<span class='performance-modal-count'>" + escapeHtml(performance.current_count || 0) + "回</span>" +
                "</div>" +
                "<div class='performance-modal-meta-item'>" +
                    "<span class='performance-modal-label'>訪問区分</span>" +
                    "<span class='performance-modal-badge' style='background: " + escapeHtml(performance.badge_color || "#3b82f6") + ";'>" +
                        escapeHtml(performance.status_badge || "") +
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

function renderPerformanceModal(performance) {
    var terms = getMapTerms();
    var modalTitleIcon = (terms && terms.modal_title_icon) ? String(terms.modal_title_icon).trim() : "";
    if (!modalTitleIcon) {
        modalTitleIcon = "📍";
    }
    return (
        "<div class='performance-modal-content'>" +
            "<div class='performance-modal-header' style='" + buildModalHeaderStyle(terms) + "'>" +
                "<div class='performance-modal-title'>" +
                    escapeHtml(modalTitleIcon) + " " + escapeHtml(performance.location_name || "") +
                "</div>" +
                "<div class='performance-modal-date'>📅 " + escapeHtml(performance.date || "") + "</div>" +
                renderHeaderGuideHtml(performance) +
            "</div>" +
            renderMetaSection(performance) +
            renderCustomFieldsSection(performance) +
            renderDetailNoteSection(performance) +
            renderSongsSection(performance) +
            renderTagsHtml(performance.tags) +
            renderPhotosHtml(performance) +
        "</div>"
    );
}
