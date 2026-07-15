"""Traceable Phase 0 source pilots for Commons, iNaturalist, and Oxford."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .manifest import MANIFEST_FIELDS
from .media import probe_image_size


LICENSE_URLS = {
    "cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "cc-by": "https://creativecommons.org/licenses/by/4.0/",
    "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
    "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/",
    "cc-by-nc-sa": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
}
PUBLIC_DOMAIN_MARK_URL = "https://creativecommons.org/publicdomain/mark/1.0/"
HTML_TAG = re.compile(r"<[^>]+>")


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(html.unescape(HTML_TAG.sub(" ", value)).split())


def canonical_commons_license_url(license_name: str, license_url: str) -> str:
    if license_url:
        return license_url
    if license_name.casefold() == "public domain":
        return PUBLIC_DOMAIN_MARK_URL
    return ""


def license_code_from_url(value: str | None) -> str:
    normalized = (value or "").casefold()
    patterns = (
        ("publicdomain/zero", "cc0"),
        ("licenses/by-nc-sa/", "cc-by-nc-sa"),
        ("licenses/by-nc/", "cc-by-nc"),
        ("licenses/by-sa/", "cc-by-sa"),
        ("licenses/by/", "cc-by"),
    )
    return next((code for pattern, code in patterns if pattern in normalized), "")


def _urlopen_with_retry(
    request: urllib.request.Request,
    *,
    timeout: int,
    attempts: int = 4,
) -> Any:
    for attempt in range(attempts):
        try:
            response = urllib.request.urlopen(request, timeout=timeout)
            time.sleep(0.25)
            return response
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 502, 503, 504} or attempt == attempts - 1:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
            time.sleep(min(delay, 15.0))
    raise RuntimeError("unreachable retry state")


def _get_json(url: str, *, user_agent: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    started = time.perf_counter()
    with _urlopen_with_retry(request, timeout=timeout) as response:
        result = json.load(response)
    elapsed = time.perf_counter() - started
    if elapsed > 1.0:
        time.sleep(max(0.0, 5.0 - elapsed))
    return result


def _download(url: str, destination: Path, *, user_agent: str, timeout: int) -> bytes:
    if destination.exists():
        return destination.read_bytes()
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with _urlopen_with_retry(request, timeout=timeout, attempts=3) as response:
        data = response.read()
    time.sleep(1.0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_archive(
    url: str,
    destination: Path,
    *,
    user_agent: str,
    timeout: int,
) -> dict[str, Any]:
    """Stream an immutable source archive to a local ignored path."""
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(destination.suffix + ".part")
        request = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with _urlopen_with_retry(request, timeout=timeout, attempts=4) as response:
                with partial.open("wb") as handle:
                    while block := response.read(1024 * 1024):
                        handle.write(block)
            partial.replace(destination)
        except Exception:
            partial.unlink(missing_ok=True)
            raise
    return {
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }


def _commons_members(
    api_url: str,
    category: str,
    *,
    user_agent: str,
    timeout: int,
) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    continuation = ""
    while True:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "file|subcat",
            "cmlimit": "500",
        }
        if continuation:
            params["cmcontinue"] = continuation
        url = f"{api_url}?{urllib.parse.urlencode(params)}"
        payload = _get_json(url, user_agent=user_agent, timeout=timeout)
        members.extend(payload.get("query", {}).get("categorymembers", []))
        continuation = payload.get("continue", {}).get("cmcontinue", "")
        if not continuation:
            return members


def enumerate_commons_files(
    api_url: str,
    root_category: str,
    *,
    limit: int,
    max_depth: int,
    user_agent: str,
    timeout: int,
) -> list[str]:
    categories: deque[tuple[str, int]] = deque([(root_category, 0)])
    visited_categories: set[str] = set()
    file_titles: list[str] = []
    seen_files: set[str] = set()
    while categories and len(file_titles) < limit:
        category, depth = categories.popleft()
        if category in visited_categories:
            continue
        visited_categories.add(category)
        for member in _commons_members(
            api_url, category, user_agent=user_agent, timeout=timeout
        ):
            title = member.get("title", "")
            if member.get("ns") == 6 and title not in seen_files:
                seen_files.add(title)
                file_titles.append(title)
                if len(file_titles) >= limit:
                    break
            elif member.get("ns") == 14 and depth < max_depth:
                categories.append((title.removeprefix("Category:"), depth + 1))
    return file_titles


def commons_image_info(
    api_url: str,
    titles: list[str],
    *,
    user_agent: str,
    timeout: int,
) -> list[dict[str, Any]]:
    if not titles:
        return []
    pages: list[dict[str, Any]] = []
    for offset in range(0, len(titles), 40):
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "titles": "|".join(titles[offset : offset + 40]),
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "960",
        }
        url = f"{api_url}?{urllib.parse.urlencode(params)}"
        payload = _get_json(url, user_agent=user_agent, timeout=timeout)
        pages.extend(payload.get("query", {}).get("pages", []))
    return [page for page in pages if page.get("imageinfo")]


def _meta_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key, {})
    return clean_html(value.get("value") if isinstance(value, dict) else "")


def _manifest_row(
    *,
    image_id: str,
    label: str,
    source_kind: str,
    source_dataset: str,
    source_page_url: str,
    original_url: str,
    author: str,
    license_name: str,
    license_url: str,
    source_group_id: str,
    data: bytes,
    width: int,
    height: int,
) -> dict[str, str]:
    return {
        "image_id": image_id,
        "label": label,
        "source_kind": source_kind,
        "source_dataset": source_dataset,
        "source_page_url": source_page_url,
        "original_url": original_url,
        "author": author,
        "license_name": license_name,
        "license_url": license_url,
        "downloaded_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_group_id": source_group_id,
        "exact_sha256": hashlib.sha256(data).hexdigest(),
        "perceptual_hash": "",
        "width": str(width),
        "height": str(height),
        "review_status": "quarantine",
        "reviewer": "",
        "duplicate_cluster_id": "",
        "split": "staging",
    }


def run_commons_pair(
    *,
    api_url: str,
    category: str,
    label: str,
    limit: int,
    max_depth: int,
    output_dir: Path,
    user_agent: str,
    timeout: int,
    group_name: str | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    candidate_titles = enumerate_commons_files(
        api_url,
        category,
        limit=max(limit * 2, limit),
        max_depth=max_depth,
        user_agent=user_agent,
        timeout=timeout,
    )
    pages = commons_image_info(
        api_url,
        candidate_titles,
        user_agent=user_agent,
        timeout=timeout,
    )
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    metadata_rejections: list[dict[str, str]] = []
    for page in pages:
        if len(rows) >= limit:
            break
        info = page["imageinfo"][0]
        if info.get("mime") not in {"image/jpeg", "image/png"}:
            continue
        download_url = info.get("thumburl") or info.get("url")
        original_url = info.get("url", "")
        if not download_url or not original_url:
            continue
        extension = ".jpg" if info.get("mime") == "image/jpeg" else ".png"
        image_id = f"commons-{page['pageid']}"
        metadata = info.get("extmetadata", {})
        license_name = _meta_value(metadata, "LicenseShortName")
        license_url = canonical_commons_license_url(
            license_name, _meta_value(metadata, "LicenseUrl")
        )
        if not license_name or not license_url:
            metadata_rejections.append(
                {
                    "title": page.get("title", ""),
                    "reason": "missing canonical license name or URL",
                }
            )
            continue
        destination_dir = output_dir / "commons" / label
        if group_name:
            destination_dir /= group_name
        destination = destination_dir / f"{image_id}{extension}"
        try:
            data = _download(
                download_url, destination, user_agent=user_agent, timeout=timeout
            )
            width, height, _ = probe_image_size(data)
        except Exception as exc:  # network/format failure is evidence, not a crash
            failures.append({"title": page.get("title", ""), "error": str(exc)})
            continue
        rows.append(
            _manifest_row(
                image_id=image_id,
                label=label,
                source_kind="wikimedia_commons",
                source_dataset=f"Category:{category}",
                source_page_url=info.get("descriptionurl", ""),
                original_url=original_url,
                author=_meta_value(metadata, "Artist"),
                license_name=license_name,
                license_url=license_url,
                source_group_id=image_id,
                data=data,
                width=width,
                height=height,
            )
        )
    return rows, {
        "source": "wikimedia_commons",
        "label": label,
        "category": category,
        "group": group_name or "",
        "candidate_titles": len(candidate_titles),
        "downloaded": len(rows),
        "failures": failures,
        "metadata_rejections": metadata_rejections,
        "complete": len(rows) >= limit,
    }


OXFORD_MEMBER = re.compile(
    r"^images/(?P<breed>Persian|Ragdoll|Sphynx)_(?P<number>[1-9][0-9]*)\.jpg$"
)


def select_oxford_members(
    members: list[tarfile.TarInfo], *, labels: list[str], limit: int | None
) -> dict[str, list[tarfile.TarInfo]]:
    """Select bounded regular image members without trusting archive paths."""
    expected = {label.casefold() for label in labels}
    selected: dict[str, list[tuple[int, tarfile.TarInfo]]] = {
        label: [] for label in expected
    }
    for member in members:
        if not member.isfile() or member.name.startswith(("/", "\\")):
            continue
        if ".." in Path(member.name).parts:
            continue
        match = OXFORD_MEMBER.fullmatch(member.name)
        if not match:
            continue
        label = match.group("breed").casefold()
        if label not in expected:
            continue
        selected[label].append((int(match.group("number")), member))
    return {
        label: [
            member
            for _, member in (sorted(items) if limit is None else sorted(items)[:limit])
        ]
        for label, items in selected.items()
    }


def run_oxford_pilot(
    *,
    archive_url: str,
    page_url: str,
    labels: list[str],
    limit: int | None,
    license_name: str,
    license_url: str,
    attribution: str,
    output_dir: Path,
    user_agent: str,
    timeout: int,
    archive_path: Path | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    archive_path = archive_path or output_dir / "oxford_iiit_pet" / "images.tar.gz"
    archive = download_archive(
        archive_url,
        archive_path,
        user_agent=user_agent,
        timeout=timeout,
    )
    rows: list[dict[str, str]] = []
    label_reports: dict[str, dict[str, Any]] = {}
    with tarfile.open(archive_path, mode="r:gz") as bundle:
        selected = select_oxford_members(bundle.getmembers(), labels=labels, limit=limit)
        for label in labels:
            label_rows: list[dict[str, str]] = []
            for member in selected[label]:
                match = OXFORD_MEMBER.fullmatch(member.name)
                if match is None:
                    continue
                number = int(match.group("number"))
                image_id = f"oxford-{label}-{number}"
                destination = (
                    output_dir
                    / "oxford_iiit_pet"
                    / label
                    / f"{image_id}.jpg"
                )
                extracted = bundle.extractfile(member)
                if extracted is None:
                    continue
                data = extracted.read()
                width, height, image_format = probe_image_size(data)
                if image_format != "jpeg":
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists() or destination.read_bytes() != data:
                    destination.write_bytes(data)
                label_rows.append(
                    _manifest_row(
                        image_id=image_id,
                        label=label,
                        source_kind="oxford_iiit_pet",
                        source_dataset="Oxford-IIIT Pet",
                        source_page_url=page_url,
                        original_url=f"{archive_url}#{member.name}",
                        author=attribution,
                        license_name=license_name,
                        license_url=license_url,
                        source_group_id=image_id,
                        data=data,
                        width=width,
                        height=height,
                    )
                )
            rows.extend(label_rows)
            label_reports[label] = {
                "downloaded": len(label_rows),
                "complete": len(label_rows) > 0
                if limit is None
                else len(label_rows) >= limit,
                "members": [row["image_id"] for row in label_rows],
            }
    return rows, {
        "source": "oxford_iiit_pet",
        "labels": label_reports,
        "archive": archive,
        "archive_url": archive_url,
        "page_url": page_url,
        "requested_count_per_label": limit,
        "image_pilot_complete": all(
            item["complete"] for item in label_reports.values()
        )
        and set(label_reports) == set(labels),
    }


def run_inaturalist_pallas(
    *,
    api_url: str,
    taxon_id: int,
    label: str,
    allowed_licenses: set[str],
    limit: int,
    output_dir: Path,
    user_agent: str,
    timeout: int,
    max_pages: int = 100,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    page = 1
    eligible_photo_count = 0
    while eligible_photo_count < limit and page <= max_pages:
        params = {
            "taxon_id": str(taxon_id),
            "quality_grade": "research",
            "photos": "true",
            "per_page": "100",
            "page": str(page),
            "order_by": "id",
            "order": "desc",
        }
        url = f"{api_url}?{urllib.parse.urlencode(params)}"
        batch = _get_json(url, user_agent=user_agent, timeout=timeout).get("results", [])
        if not batch:
            break
        results.extend(batch)
        eligible_photo_count += sum(
            bool(observation.get("photos"))
            and (
                (observation["photos"][0].get("license_code") or "").lower()
                in allowed_licenses
            )
            for observation in batch
        )
        if len(batch) < 100:
            break
        page += 1
    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    for observation in results:
        if len(rows) >= limit:
            break
        photos = observation.get("photos") or []
        if not photos:
            continue
        photo = photos[0]
        license_code = (photo.get("license_code") or "").lower()
        if license_code not in allowed_licenses:
            continue
        square_url = photo.get("url", "")
        if not square_url:
            continue
        download_url = square_url.replace("/square.", "/medium.")
        original_url = square_url.replace("/square.", "/original.")
        image_id = f"inat-{observation['id']}-{photo['id']}"
        destination = output_dir / "inaturalist" / label / f"{image_id}.jpg"
        try:
            data = _download(
                download_url, destination, user_agent=user_agent, timeout=timeout
            )
            width, height, _ = probe_image_size(data)
        except Exception as exc:
            failures.append({"observation": str(observation.get("id")), "error": str(exc)})
            continue
        rows.append(
            _manifest_row(
                image_id=image_id,
                label=label,
                source_kind="inaturalist",
                source_dataset=f"taxon:{taxon_id}:research-grade",
                source_page_url=observation.get("uri", ""),
                original_url=original_url,
                author=clean_html(photo.get("attribution")),
                license_name=license_code,
                license_url=LICENSE_URLS.get(license_code, ""),
                source_group_id=f"inat-observation-{observation['id']}",
                data=data,
                width=width,
                height=height,
            )
        )
    return rows, {
        "source": "inaturalist",
        "label": label,
        "taxon_id": taxon_id,
        "api_results": len(results),
        "eligible_photo_results": eligible_photo_count,
        "api_pages": page,
        "downloaded": len(rows),
        "failures": failures,
        "complete": len(rows) >= limit,
    }


def run_gbif_pallas(
    *,
    api_url: str,
    scientific_name: str,
    label: str,
    allowed_licenses: set[str],
    limit: int,
    output_dir: Path,
    user_agent: str,
    timeout: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    offset = 0
    total_count = 0
    while len(records) < limit:
        page_limit = min(300, limit - len(records))
        params = {
            "scientific_name": scientific_name,
            "media_type": "StillImage",
            "occurrence_status": "present",
            "limit": str(page_limit),
            "offset": str(offset),
        }
        url = f"{api_url}?{urllib.parse.urlencode(params)}"
        payload = _get_json(url, user_agent=user_agent, timeout=timeout)
        batch = payload.get("results", [])
        total_count = int(payload.get("count", 0))
        if not batch:
            break
        records.extend(batch)
        offset += len(batch)
        if payload.get("endOfRecords"):
            break

    rows: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    license_rejections = 0
    for record in records:
        if len(rows) >= limit:
            break
        selected_media: tuple[dict[str, Any], str] | None = None
        for media in record.get("media") or []:
            license_code = license_code_from_url(media.get("license"))
            if (
                media.get("type") == "StillImage"
                and media.get("identifier")
                and license_code in allowed_licenses
            ):
                selected_media = media, license_code
                break
        if selected_media is None:
            license_rejections += 1
            continue
        media, license_code = selected_media
        occurrence_key = str(record["key"])
        identifier = media["identifier"]
        media_hash = hashlib.md5(
            identifier.encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        download_url = (
            "https://api.gbif.org/v1/image/cache/960x/occurrence/"
            f"{occurrence_key}/media/{media_hash}"
        )
        image_id = f"gbif-{occurrence_key}-{media_hash[:12]}"
        destination = output_dir / "gbif" / label / f"{image_id}.jpg"
        try:
            data = _download(
                download_url, destination, user_agent=user_agent, timeout=timeout
            )
            width, height, _ = probe_image_size(data)
        except Exception as exc:
            failures.append({"occurrence": occurrence_key, "error": str(exc)})
            continue
        rows.append(
            _manifest_row(
                image_id=image_id,
                label=label,
                source_kind="gbif",
                source_dataset=record.get("datasetTitle")
                or record.get("datasetKey", "GBIF occurrence"),
                source_page_url=f"https://www.gbif.org/occurrence/{occurrence_key}",
                original_url=identifier,
                author=clean_html(
                    media.get("creator") or media.get("rightsHolder") or ""
                ),
                license_name=license_code,
                license_url=LICENSE_URLS[license_code],
                source_group_id=f"gbif-occurrence-{occurrence_key}",
                data=data,
                width=width,
                height=height,
            )
        )
    return rows, {
        "source": "gbif",
        "label": label,
        "scientific_name": scientific_name,
        "api_records": len(records),
        "api_total_count": total_count,
        "downloaded": len(rows),
        "license_rejections": license_rejections,
        "failures": failures,
        "complete": len(rows) >= limit or len(records) >= total_count,
    }


def probe_endpoint(url: str, *, user_agent: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url, headers={"User-Agent": user_agent}, method="HEAD"
    )
    started = time.perf_counter()
    try:
        with _urlopen_with_retry(request, timeout=timeout) as response:
            return {
                "url": url,
                "status": response.status,
                "content_length": int(response.headers.get("Content-Length", "0")),
                "content_type": response.headers.get("Content-Type", ""),
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "ok": response.status == 200,
            }
    except Exception as exc:
        return {
            "url": url,
            "status": None,
            "error": str(exc),
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "ok": False,
        }


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
