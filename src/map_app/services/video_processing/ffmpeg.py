import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


def get_ffmpeg_binary():
    configured_path = (getattr(settings, "FFMPEG_BINARY", "") or "").strip()
    if configured_path:
        if Path(configured_path).exists():
            return configured_path
        raise ValidationError(f"指定された ffmpeg が見つかりません: {configured_path}")

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    raise ValidationError("ffmpeg が見つかりません。動画圧縮を実行できません。")


def get_ffprobe_binary():
    configured_path = (getattr(settings, "FFMPEG_BINARY", "") or "").strip()
    if configured_path:
        probe_path = str(Path(configured_path).with_name("ffprobe"))
        if Path(probe_path).exists():
            return probe_path

    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        return ffprobe_path

    raise ValidationError("ffprobe が見つかりません。動画情報を取得できません。")


def get_media_duration_seconds(input_path):
    command = [
        get_ffprobe_binary(),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        error_output = (exc.stderr or exc.stdout or "").strip()
        raise ValidationError(f"動画情報の取得に失敗しました。{error_output[:400]}") from exc

    raw_value = (completed.stdout or "").strip()
    try:
        return max(0.0, float(raw_value))
    except ValueError as exc:
        raise ValidationError("動画情報の取得結果が不正です。") from exc


def get_media_dimensions(input_path):
    command = [
        get_ffprobe_binary(),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        str(input_path),
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        error_output = (exc.stderr or exc.stdout or "").strip()
        raise ValidationError(f"動画寸法の取得に失敗しました。{error_output[:400]}") from exc

    raw_value = (completed.stdout or "").strip().rstrip("x")
    if "x" not in raw_value:
        raise ValidationError("動画寸法の取得結果が不正です。")

    width_value, height_value = raw_value.split("x", 1)
    try:
        width = max(0, int(width_value))
        height = max(0, int(height_value))
    except ValueError as exc:
        raise ValidationError("動画寸法の取得結果が不正です。") from exc

    if width <= 0 or height <= 0:
        raise ValidationError("動画寸法を取得できませんでした。")
    return width, height


def run_ffmpeg_command(command, failure_prefix, *, progress_callback=None):
    if not progress_callback:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            error_output = (exc.stderr or exc.stdout or "").strip()
            raise ValidationError(f"{failure_prefix}{error_output[-400:]}") from exc
        return

    command = [*command, "-progress", "pipe:1", "-nostats"]
    try:
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as process:
            progress_state = {}
            output_lines = []
            for line in process.stdout or []:
                raw_line = line.strip()
                if raw_line:
                    output_lines.append(raw_line)
                if not raw_line or "=" not in raw_line:
                    continue
                key, value = raw_line.split("=", 1)
                progress_state[key] = value
                if key == "progress":
                    progress_callback(progress_state.copy())
                    progress_state = {}

            return_code = process.wait()
            if return_code != 0:
                combined_output = "\n".join(output_lines[-80:])
                raise subprocess.CalledProcessError(return_code, command, output=combined_output, stderr=combined_output)
    except subprocess.CalledProcessError as exc:
        error_output = (exc.stderr or exc.stdout or "").strip()
        raise ValidationError(f"{failure_prefix}{error_output[-400:]}") from exc
