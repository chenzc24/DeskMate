from __future__ import annotations

import tarfile

from deskmate_baseline.data.source_pilot import (
    LICENSE_URLS,
    PUBLIC_DOMAIN_MARK_URL,
    canonical_commons_license_url,
    clean_html,
    license_code_from_url,
    select_oxford_members,
)


def test_clean_html_preserves_readable_attribution() -> None:
    value = '<span class="licensetpl_attr">Jane &amp; John</span><br>CC BY'
    assert clean_html(value) == "Jane & John CC BY"


def test_supported_inaturalist_licenses_have_canonical_urls() -> None:
    assert LICENSE_URLS["cc0"].startswith("https://creativecommons.org/")
    assert LICENSE_URLS["cc-by"].endswith("/by/4.0/")
    assert LICENSE_URLS["cc-by-nc-sa"].endswith("/by-nc-sa/4.0/")


def test_gbif_license_urls_map_to_supported_codes() -> None:
    assert license_code_from_url("http://creativecommons.org/licenses/by-nc/4.0/") == "cc-by-nc"
    assert license_code_from_url("https://creativecommons.org/publicdomain/zero/1.0/") == "cc0"
    assert license_code_from_url("https://creativecommons.org/licenses/by-nd/4.0/") == ""


def test_commons_public_domain_metadata_gets_official_mark_url() -> None:
    assert canonical_commons_license_url("Public domain", "") == PUBLIC_DOMAIN_MARK_URL
    assert canonical_commons_license_url("CC BY-SA 4.0", "https://license.test/") == "https://license.test/"


def _member(name: str, *, regular: bool = True) -> tarfile.TarInfo:
    member = tarfile.TarInfo(name)
    member.type = tarfile.REGTYPE if regular else tarfile.DIRTYPE
    return member


def test_oxford_member_selection_is_bounded_sorted_and_safe() -> None:
    members = [
        _member("images/Persian_10.jpg"),
        _member("images/Persian_2.jpg"),
        _member("images/Ragdoll_3.jpg"),
        _member("images/Sphynx_1.jpg"),
        _member("images/../Persian_1.jpg"),
        _member("/images/Persian_1.jpg"),
        _member("images/Persian_3.jpg", regular=False),
        _member("images/Abyssinian_1.jpg"),
    ]
    selected = select_oxford_members(
        members, labels=["persian", "ragdoll", "sphynx"], limit=2
    )
    assert [item.name for item in selected["persian"]] == [
        "images/Persian_2.jpg",
        "images/Persian_10.jpg",
    ]
    assert [item.name for item in selected["ragdoll"]] == ["images/Ragdoll_3.jpg"]
    assert [item.name for item in selected["sphynx"]] == ["images/Sphynx_1.jpg"]


def test_oxford_member_selection_can_return_all_safe_members() -> None:
    members = [_member(f"images/Persian_{number}.jpg") for number in (3, 1, 2)]
    selected = select_oxford_members(members, labels=["persian"], limit=None)
    assert [item.name for item in selected["persian"]] == [
        "images/Persian_1.jpg",
        "images/Persian_2.jpg",
        "images/Persian_3.jpg",
    ]
