(function($) {
    'use strict';

    $(document).ready(function() {
        // 演奏日フィールドの&nbsp;をCSSで非表示にする（HTMLを書き換えない）
        function fixDateField() {
            const datetimeshortcuts = $('.form-row.field-date .datetimeshortcuts');

            if (datetimeshortcuts.length > 0) {
                // CSSでスペースを詰める
                datetimeshortcuts.css({
                    'white-space': 'nowrap',
                    'word-spacing': '-0.3em'
                });
            }
        }

        // 初期化
        setTimeout(fixDateField, 100);
    });
})(django.jQuery);
