"""Воспроизводимая генерация заготовок API из openapi.yaml."""

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Запустить изолированный генератор и форматирование."""
    root = Path(__file__).resolve().parents[1]
    local_uv = root / ".tools/uv-0.12.17/bin/uv"
    uv = str(local_uv) if local_uv.exists() else shutil.which("uv")
    if uv is None:
        raise SystemExit("Не найден uv. Установите uv и повторите генерацию.")
    subprocess.run(
        [
            uv,
            "run",
            "--isolated",
            "--only-group",
            "codegen",
            "--locked",
            "fastapi-codegen",
            "--input",
            "openapi.yaml",
            "--output",
            "generated",
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--python-version",
            "3.14",
            "--disable-timestamp",
            "--strict-nullable",
            "--no-allow-remote-refs",
        ],
        cwd=root,
        check=True,
    )
    (root / "generated/__init__.py").write_text(
        '"""Модели и обработчики, сгенерированные из openapi.yaml."""\n',
        encoding="utf-8",
    )
    for command in [
        ["ruff", "check", "generated", "--fix"],
        ["isort", "generated"],
        ["black", "generated"],
    ]:
        subprocess.run([sys.executable, "-m", *command], cwd=root, check=True)


if __name__ == "__main__":
    main()
