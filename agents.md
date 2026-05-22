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
