// 管理画面でのジオコーディング機能
(function() {
    'use strict';

    // ページ読み込み時に実行
    document.addEventListener('DOMContentLoaded', function() {
        // Location モデルの編集ページかどうかを確認
        if (!document.querySelector('#id_name') || !document.querySelector('#id_latitude')) {
            return;
        }

        // ジオコーディングボタンを追加
        addGeocodingButton();
    });

    function addGeocodingButton() {
        // 場所名フィールドの後にボタンを追加
        const nameField = document.querySelector('#id_name');

        if (!nameField) return;

        // ボタンとステータスを配置するラッパー
        const wrapper = document.createElement('div');
        wrapper.id = 'geocoding-wrapper';
        wrapper.style.cssText = `
            display: flex;
            align-items: stretch;
            flex-wrap: nowrap;
            gap: 10px;
            margin: 0 0 0 10px;
            align-self: center;
        `;

        // ボタンを作成（場所名入力と同じ高さ/縦幅に揃える）
        const fieldStyles = window.getComputedStyle(nameField);
        const fieldHeight = Math.round(nameField.getBoundingClientRect().height) || 0;
        const button = document.createElement('a');
        button.href = '#';
        button.setAttribute('role', 'button');
        button.className = 'geocoding-button';
        button.textContent = '📍 緯度・経度取得';
        button.style.setProperty('flex', '0 0 auto', 'important');
        button.style.setProperty('display', 'inline-flex', 'important');
        button.style.setProperty('align-items', 'center', 'important');
        button.style.setProperty('justify-content', 'center', 'important');
        button.style.setProperty('white-space', 'nowrap', 'important');
        button.style.setProperty('box-sizing', 'border-box', 'important');
        button.style.setProperty('text-decoration', 'none', 'important');
        button.style.setProperty('user-select', 'none', 'important');
        button.style.setProperty('border', '1px solid #0b5d3b', 'important');
        button.style.setProperty('background', '#0b5d3b', 'important');
        button.style.setProperty('color', '#ffffff', 'important');
        button.style.setProperty('cursor', 'pointer', 'important');
        button.style.setProperty('height', `${fieldHeight}px`, 'important');
        button.style.setProperty('min-height', `${fieldHeight}px`, 'important');
        button.style.setProperty('max-height', `${fieldHeight}px`, 'important');
        button.style.setProperty('line-height', '1', 'important');
        button.style.setProperty('font-size', fieldStyles.fontSize || 'inherit', 'important');
        button.style.setProperty('font-family', fieldStyles.fontFamily || 'inherit', 'important');
        button.style.setProperty('font-weight', fieldStyles.fontWeight || 'inherit', 'important');
        button.style.setProperty('border-radius', '8px', 'important');
        button.style.setProperty('padding-top', '0px', 'important');
        button.style.setProperty('padding-bottom', '0px', 'important');
        button.style.setProperty('padding-left', '18px', 'important');
        button.style.setProperty('padding-right', '18px', 'important');

        // クリックイベント
        button.addEventListener('click', function(e) {
            e.preventDefault();
            geocodeAddress();
        });

        // ステータス表示用のdivを追加
        const statusDiv = document.createElement('div');
        statusDiv.id = 'geocoding-status';
        statusDiv.style.cssText = `
            flex: 1 1 320px;
            min-height: ${fieldHeight}px;
            box-sizing: border-box;
            margin: 0;
            padding: 0 12px;
            display: none;
            align-items: center;
            border-radius: 0;
        `;

        wrapper.appendChild(button);
        wrapper.appendChild(statusDiv);

        // 場所名フィールドの後に挿入
        nameField.parentElement.appendChild(wrapper);

        // 画面幅に応じてPC/スマホの表示を切り替え
        applyLayout(nameField, wrapper, button, statusDiv);
        window.addEventListener('resize', () => {
            applyLayout(nameField, wrapper, button, statusDiv);
        });

        ensureResultModal();
    }

    function applyLayout(nameField, wrapper, button, statusDiv) {
        const fieldStyles = window.getComputedStyle(nameField);
        const fieldHeight = Math.round(nameField.getBoundingClientRect().height) || 0;
        const isMobile = window.matchMedia('(max-width: 768px)').matches;

        if (isMobile) {
            // スマホ: 他の管理画面ボタンと同じサイズ感（横幅いっぱい）
            wrapper.style.setProperty('display', 'block', 'important');
            wrapper.style.setProperty('width', '100%', 'important');
            wrapper.style.setProperty('margin', '10px 0 0 0', 'important');

            button.style.setProperty('display', 'inline-flex', 'important');
            button.style.setProperty('align-items', 'center', 'important');
            button.style.setProperty('justify-content', 'center', 'important');
            button.style.setProperty('width', '100%', 'important');
            button.style.setProperty('max-width', '100%', 'important');
            button.style.setProperty('height', `${fieldHeight}px`, 'important');
            button.style.setProperty('min-height', `${fieldHeight}px`, 'important');
            button.style.setProperty('max-height', `${fieldHeight}px`, 'important');
            button.style.setProperty('line-height', '1', 'important');
            button.style.setProperty('padding-left', '14px', 'important');
            button.style.setProperty('padding-right', '14px', 'important');

            statusDiv.style.setProperty('margin-top', '8px', 'important');
            statusDiv.style.setProperty('height', `${fieldHeight}px`, 'important');
            statusDiv.style.setProperty('min-height', `${fieldHeight}px`, 'important');
            statusDiv.style.setProperty('max-height', `${fieldHeight}px`, 'important');
        } else {
            // PC: 場所名入力と同じ高さで横並び
            wrapper.style.setProperty('display', 'flex', 'important');
            wrapper.style.setProperty('align-items', 'stretch', 'important');
            wrapper.style.setProperty('flex-wrap', 'nowrap', 'important');
            wrapper.style.setProperty('width', 'auto', 'important');
            wrapper.style.setProperty('margin', '0 0 0 10px', 'important');

            button.style.setProperty('display', 'inline-flex', 'important');
            button.style.setProperty('width', 'auto', 'important');
            button.style.setProperty('max-width', 'none', 'important');
            button.style.setProperty('height', `${fieldHeight}px`, 'important');
            button.style.setProperty('min-height', `${fieldHeight}px`, 'important');
            button.style.setProperty('max-height', `${fieldHeight}px`, 'important');
            button.style.setProperty('line-height', '1', 'important');
            button.style.setProperty('padding-left', '18px', 'important');
            button.style.setProperty('padding-right', '18px', 'important');

            statusDiv.style.setProperty('margin-top', '0', 'important');
            statusDiv.style.setProperty('height', `${fieldHeight}px`, 'important');
            statusDiv.style.setProperty('min-height', `${fieldHeight}px`, 'important');
            statusDiv.style.setProperty('max-height', `${fieldHeight}px`, 'important');
        }
    }

    function geocodeAddress() {
        const nameField = document.querySelector('#id_name');
        const latField = document.querySelector('#id_latitude');
        const lngField = document.querySelector('#id_longitude');

        const rawQuery = nameField.value.trim();

        if (!rawQuery) {
            showStatus('場所名を入力してください', 'error');
            return;
        }

        showStatus('🔍 位置情報を取得中...', 'loading');

        const queryCandidates = buildQueryCandidates(rawQuery);
        const requests = queryCandidates.map((query) => {
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1&accept-language=ja`;
            return fetch(url).then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            }).catch(() => []);
        });

        Promise.all(requests)
            .then((allResponses) => {
                const merged = mergeGeocodingResults(allResponses.flat());

                if (!merged.length) {
                    showStatus('❌ 場所が見つかりませんでした。場所名を少し詳しく入力してください。', 'error');
                    return;
                }

                if (merged.length === 1) {
                    applyGeocodeResult(merged[0], latField, lngField);
                    showStatus(`✅ 取得成功: ${merged[0].display_name}`, 'success');
                    return;
                }

                showResultSelector(merged, latField, lngField);
            })
            .catch((error) => {
                console.error('Geocoding error:', error);
                showStatus('❌ エラーが発生しました。しばらくしてから再試行してください。', 'error');
            });
    }

    function buildQueryCandidates(rawQuery) {
        const normalized = rawQuery
            .normalize('NFKC')
            .replace(/[‐‑‒–—―ー]/g, '-')
            .replace(/[()（）［］「」『』]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();

        const compact = normalized.replace(/\s+/g, '');
        const stripped = compact
            .replace(/(ストリートピアノ|street\s*piano)/ig, '')
            .replace(/(都|道|府|県)$/u, '');

        const noStation = stripped.replace(/駅$/u, '');

        const candidates = new Set();
        if (normalized) candidates.add(normalized);
        if (compact && compact !== normalized) candidates.add(compact);
        if (stripped && stripped !== compact) candidates.add(stripped);
        if (noStation && noStation !== stripped) {
            candidates.add(noStation);
            candidates.add(`${noStation}駅`);
            candidates.add(`${noStation} station`);
        }

        const list = Array.from(candidates).filter(Boolean);
        return [
            ...list,
            ...list.map((q) => `${q} 日本`),
            ...list.map((q) => `${q} Japan`)
        ].slice(0, 10);
    }

    function mergeGeocodingResults(results) {
        const seen = new Set();
        const merged = [];

        results.forEach((result) => {
            const key = `${result.place_id}:${result.lat}:${result.lon}`;
            if (seen.has(key)) return;
            seen.add(key);
            merged.push(result);
        });

        return merged;
    }

    function applyGeocodeResult(result, latField, lngField) {
        latField.value = parseFloat(result.lat).toFixed(6);
        lngField.value = parseFloat(result.lon).toFixed(6);
    }

    function showResultSelector(results, latField, lngField) {
        const modal = document.querySelector('#geocoding-result-modal');
        const list = document.querySelector('#geocoding-result-list');
        const count = document.querySelector('#geocoding-result-count');
        if (!modal || !list || !count) return;

        count.textContent = `候補数: ${results.length}`;
        list.innerHTML = results.map((result, index) => `
            <button type="button" class="geocoding-candidate-button" data-index="${index}">
                ${index + 1}. ${escapeHtml(result.display_name)}
            </button>
        `).join('');

        list.querySelectorAll('.geocoding-candidate-button').forEach((button) => {
            button.addEventListener('click', () => {
                const index = Number(button.dataset.index);
                const selected = results[index];
                if (!selected) return;
                applyGeocodeResult(selected, latField, lngField);
                closeResultModal();
                showStatus(`✅ 選択: ${selected.display_name}`, 'success');
            });
        });

        openResultModal();
    }

    function ensureResultModal() {
        if (document.querySelector('#geocoding-result-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'geocoding-result-modal';
        modal.innerHTML = `
            <div class="geocoding-modal-backdrop"></div>
            <div class="geocoding-modal-content" role="dialog" aria-modal="true" aria-label="候補選択">
                <div class="geocoding-modal-header">
                    <div class="geocoding-modal-title">候補が複数あります。選択してください。</div>
                    <button type="button" id="geocoding-modal-close" class="geocoding-modal-close" aria-label="閉じる">×</button>
                </div>
                <div id="geocoding-result-count" class="geocoding-modal-count"></div>
                <div id="geocoding-result-list" class="geocoding-modal-list"></div>
            </div>
        `;
        document.body.appendChild(modal);

        modal.querySelector('.geocoding-modal-backdrop').addEventListener('click', closeResultModal);
        modal.querySelector('#geocoding-modal-close').addEventListener('click', closeResultModal);
    }

    function openResultModal() {
        const modal = document.querySelector('#geocoding-result-modal');
        if (!modal) return;
        modal.style.display = 'block';
    }

    function closeResultModal() {
        const modal = document.querySelector('#geocoding-result-modal');
        if (!modal) return;
        modal.style.display = 'none';
    }

    function escapeHtml(text) {
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function showStatus(message, type) {
        const statusDiv = document.querySelector('#geocoding-status');
        const nameField = document.querySelector('#id_name');
        const wrapper = document.querySelector('#geocoding-wrapper');
        const button = document.querySelector('.geocoding-button');
        if (!statusDiv) return;

        if (nameField && wrapper && button) {
            applyLayout(nameField, wrapper, button, statusDiv);
        }

        statusDiv.textContent = message;
        statusDiv.style.display = 'flex';
        statusDiv.style.height = '';
        statusDiv.style.minHeight = '';
        statusDiv.style.maxHeight = '';
        statusDiv.style.padding = '0 12px';

        switch(type) {
            case 'success':
                statusDiv.style.background = '#d4edda';
                statusDiv.style.color = '#155724';
                break;
            case 'error':
                statusDiv.style.background = '#f8d7da';
                statusDiv.style.color = '#721c24';
                break;
            case 'loading':
                statusDiv.style.background = '#d1ecf1';
                statusDiv.style.color = '#0c5460';
                break;
            default:
                statusDiv.style.background = '#f8f9fa';
                statusDiv.style.color = '#333';
                break;
        }

        if (type === 'success') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    }

})();
