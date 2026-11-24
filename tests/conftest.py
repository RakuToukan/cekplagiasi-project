import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.preprocess import PreprosesingTeks  # noqa: E402


@pytest.fixture(scope="session")
def pre():
    return PreprosesingTeks()


@pytest.fixture(scope="session")
def contoh():
    folder = ROOT / "sample_docs"
    return (
        (folder / "dokumen_asli.txt").read_text(encoding="utf-8"),
        (folder / "dokumen_parafrase.txt").read_text(encoding="utf-8"),
    )
