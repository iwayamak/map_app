import hmac
import json
from hashlib import sha256

from django.conf import settings
from django.http import JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from map_app.services.video_processing.pipeline import apply_video_processing_callback


def _expected_signature(body, secret):
    return hmac.new(secret.encode("utf-8"), body, sha256).hexdigest()


def _is_valid_signature(request):
    secret = (getattr(settings, "VIDEO_PROCESSING_CALLBACK_SECRET", "") or "").strip()
    if not secret:
        return False
    provided = request.headers.get("X-Video-Processing-Signature", "").strip()
    if not provided:
        return False
    if provided.startswith("sha256="):
        provided = provided.removeprefix("sha256=")
    return constant_time_compare(provided, _expected_signature(request.body, secret))


@csrf_exempt
@require_POST
def video_processing_callback_view(request):
    if not _is_valid_signature(request):
        return JsonResponse({"error": "invalid signature"}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid json"}, status=400)

    ok, error = apply_video_processing_callback(payload)
    if not ok:
        return JsonResponse({"error": error or "callback failed"}, status=404)
    return JsonResponse({"ok": True})
