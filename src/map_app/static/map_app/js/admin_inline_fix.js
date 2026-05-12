// インラインフォームの動的追加時にautocompleteを再初期化
(function($) {
    $(document).ready(function() {
        // 連打による重複POSTを抑止
        var submitted = false;
        var $form = $('form');
        $form.on('submit', function() {
            if (submitted) {
                return false;
            }
            submitted = true;
            $(this).find('button[type="submit"], input[type="submit"]').prop('disabled', true);
            return true;
        });

        // ページ読み込み時に既存の行にhas_originalを追加
        $('.dynamic-activitylogitem_set').each(function() {
            var $row = $(this);
            if (!$row.hasClass('has_original')) {
                $row.addClass('has_original');
            }
        });

        // 追加ボタンのクリックを監視
        $(document).on('click', '.add-row a', function() {

            // 少し待ってから新しい行を処理（遅延を10msに短縮）
            setTimeout(function() {

                // 動的に追加されたactivitylogitem_setの行を取得
                var $newRows = $('.dynamic-activitylogitem_set').filter(function() {
                    return !$(this).data('processed');
                });

                $newRows.each(function() {
                    var $row = $(this);

                    // 追加された行のclassを統一
                    if (!$row.hasClass('has_original')) {
                        $row.addClass('has_original');
                    }


                    // 追加された行のselect要素を取得
                    var $select = $row.find('select[name*="item"]');

                    if ($select.length) {
                        // data属性をコピー（既存の行から）
                        var $existingSelect = $('#activitylogitem_set-group .form-row:first select[name*="item"]');
                        if ($existingSelect.length && $existingSelect.hasClass('admin-autocomplete')) {
                            // data属性をコピー
                            $.each($existingSelect.data(), function(key, value) {
                                $select.attr('data-' + key, value);
                            });

                            // admin-autocompleteクラスを追加
                            $select.addClass('admin-autocomplete');

                            // Select2を初期化
                            if (typeof $.fn.djangoAdminSelect2 !== 'undefined') {
                                $select.djangoAdminSelect2();
                            }
                        }
                    }

                    // 処理済みフラグを設定
                    $row.data('processed', true);
                });
            }, 10);
        });
    });
})(django.jQuery);
