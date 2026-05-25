# Agent Notes

- GitHub 操作（`gh` / `git push` / PR 作成）は `iwayamak` アカウントを使用すること。

## Production Access

- `suusan_piano_map` production
  - SSH: `ssh -i /Users/iwayamak/PycharmProjects/suusan_piano_map/LightsailDefaultKey-ap-northeast-1.pem ubuntu@35.79.64.241`
  - App dir: `/var/www/suusan_piano_map`
  - Shared module dir: `/var/www/map_app`
  - Services: `gunicorn`, `nginx`, `piano-map-video-worker`（存在時）

- `goshuin_map` production
  - SSH: `ssh -i /Users/iwayamak/PycharmProjects/goshuin_map/goshuin_map.pem ubuntu@18.180.51.69`
  - App dir: `/var/www/goshuin_map`
  - Shared module dir: `/var/www/map_app`
  - Services: `goshuin-gunicorn`, `nginx`

## Deploy Sequence

1. `map_app` を先に push。
2. 各アプリを push。
3. 本番で `map_app` pull → 対象アプリ pull。
4. `python manage.py migrate --noinput`
5. `python manage.py collectstatic --no-input`
6. `python manage.py check`
7. `systemctl restart`（app gunicorn）→ `systemctl reload nginx`

## Mandatory Guardrails (Root-Cause Prevention)

以下は必須ルール。

1. 変更前に実効先を機械確認する  
   - テンプレート: `get_template(...).origin`  
   - モデル/テーマ: 実フィールド名を確認（例: `Theme._meta.fields`）

2. 1パッチ1目的  
   - 復旧、共通化、見た目調整を混在させない。

3. 本番反映前に作業ツリーを clean にする  
   - `git status` が dirty のまま pull しない。必要なら `stash`/コミット/退避を先に実施。

4. 完了報告前の必須確認  
   - `systemctl is-active`  
   - `get_template(...).origin`  
   - PC/モバイルでホーム・一覧・変更画面を確認

5. 失敗時の rollback を先に準備  
   - 変更前値/変更前ファイルを控えてから作業する。
