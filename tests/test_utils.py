from __future__ import annotations

import html
import shutil
import tempfile
from pathlib import Path

from hypothesis import assume
from hypothesis import given
from hypothesis import strategies as st

from discord_free_game_notifier import settings as settings_mod
from discord_free_game_notifier.utils import already_posted
from discord_free_game_notifier.utils import normalized_variants
from discord_free_game_notifier.webhook import GameService


@given(st.text())
def test_normalized_variants_contains_trimmed(s: str) -> None:
    variants: set[str] = normalized_variants(s)
    trimmed: str = s.strip()
    if trimmed:
        assert trimmed in variants
    else:
        # empty input -> no variants
        assert variants == set()


@given(st.text())
def test_variants_are_stripped_and_non_empty(s: str) -> None:
    variants: set[str] = normalized_variants(s)
    for v in variants:
        assert v == v.strip()
        assert v


@given(st.text().filter(lambda t: "\n" not in t and "\r" not in t and t))
def test_unescape_of_variants_present(s: str) -> None:
    variants: set[str] = normalized_variants(s)
    # For every variant, its unescaped form should also be one of the variants
    for v in variants:
        assert html.unescape(v) in variants


@given(st.text().filter(lambda t: "\n" not in t and "\r" not in t and t))
def test_already_posted_detects_variants(s: str) -> None:
    # Use a temporary directory for app_dir so file IO is isolated
    tmpdir: str = tempfile.mkdtemp()
    old_app_dir: str = settings_mod.app_dir
    try:
        settings_mod.app_dir = tmpdir

        service = GameService.STEAM
        posted_file: Path = Path(tmpdir) / f"{service.value.lower()}.txt"

        # Write one of the normalized variants into the file
        variants: set[str] = normalized_variants(s)
        # Skip if variants is empty (shouldn't happen with filter, but defensive)
        if not variants:
            return
        # choose an arbitrary variant to write
        to_write: str = next(iter(variants))
        posted_file.write_text(f"{to_write}\n", encoding="utf-8")

        assert already_posted(service, s) is True
    finally:
        settings_mod.app_dir = old_app_dir
        shutil.rmtree(tmpdir)


@given(
    st.tuples(
        st.text().filter(lambda t: "\n" not in t and "\r" not in t and t),
        st.text().filter(lambda t: "\n" not in t and "\r" not in t and t),
    ),
)
def test_already_posted_negative_when_disjoint(pair: tuple[str, str]) -> None:
    a, b = pair
    # ensure the normalized variants don't intersect
    assume(not (normalized_variants(a) & normalized_variants(b)))

    tmpdir: str = tempfile.mkdtemp()
    old_app_dir: str = settings_mod.app_dir
    try:
        settings_mod.app_dir = tmpdir
        service = GameService.STEAM
        posted_file: Path = Path(tmpdir) / f"{service.value.lower()}.txt"
        posted_file.write_text(f"{b}\n", encoding="utf-8")

        assert already_posted(service, a) is False
    finally:
        settings_mod.app_dir = old_app_dir
        shutil.rmtree(tmpdir)
