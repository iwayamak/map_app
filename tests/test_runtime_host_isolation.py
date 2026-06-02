from pathlib import Path
from unittest import TestCase


RUNTIME_ROOT = Path(__file__).resolve().parents[1] / "src" / "map_app"
FORBIDDEN_RUNTIME_PATTERNS = (
    "suusan_piano_map",
    "goshuin_map",
    "from piano_map",
    "import piano_map",
)
SCAN_SUFFIXES = {".py", ".html", ".js", ".css"}


class RuntimeHostIsolationTests(TestCase):
    def test_runtime_code_does_not_reference_host_specific_modules(self):
        violations = []

        for path in sorted(RUNTIME_ROOT.rglob("*")):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            if "migrations" in path.parts:
                continue

            content = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(content.splitlines(), start=1):
                for pattern in FORBIDDEN_RUNTIME_PATTERNS:
                    if pattern in line:
                        violations.append(f"{path.relative_to(RUNTIME_ROOT)}:{lineno}: {line.strip()}")

        self.assertEqual(
            violations,
            [],
            "Runtime code must not reference host-specific modules or reintroduce piano_map imports:\n"
            + "\n".join(violations),
        )
