from __future__ import annotations

import gzip
import hashlib
import http.client
import ipaddress
import json
import re
import stat
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zlib
from compression import zstd
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import zopfli.zlib


ROOT = Path(__file__).resolve().parents[2]
USER_AGENT = "Ethan2258-mihomo-rule-updater/1.0"
MIHOMO_RELEASE_API = "https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"
SINGBOX_RELEASE_API = "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
MRS_MAGIC = bytes.fromhex("28b52ffd")
SRS_MAGIC = b"SRS"
MIRROR_BRANCH = "Loon"
DOMAIN_SET_ENTRY = re.compile(
    r"^(?:\+\.)?(?:[A-Za-z0-9_*-]+\.)+[A-Za-z0-9_*-]+$"
)
SPEEDTEST_NAMESPACE_LABEL = re.compile(
    r"^(?:speedtest[a-z0-9-]*|ookla[a-z0-9-]*|librespeed[a-z0-9-]*|"
    r"speed|speed-test|st|myspeed|nperf|testspeed|test-speed|testdevelocidad|"
    r"testevelocidade|velocimetro|medidor|bandwidth|broadband|perf)$"
)
NODESEEK_SOURCES = (
    "https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/nodeseek.mrs",
)
WEBRTC_SOURCES = (
    "https://raw.githubusercontent.com/MeALiYeYe/ProxyConfigFiles/main/Mihomo/rule/WebRTC/WebRTC.mrs",
    "https://cdn.jsdelivr.net/gh/MeALiYeYe/ProxyConfigFiles@main/Mihomo/rule/WebRTC/WebRTC.mrs",
    "https://raw.githubusercontent.com/milangree/rules/main/rules/mihomo/Webrtc/Webrtc_domain.mrs",
    "https://cdn.jsdelivr.net/gh/milangree/rules@main/rules/mihomo/Webrtc/Webrtc_domain.mrs",
)
SPEEDTEST_KELEE_SOURCES = (
    "https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr",
    "https://raw.githubusercontent.com/ClaraCora/ege/main/kelee/SpeedtestInternational.lsr",
    "https://raw.githubusercontent.com/linnux-x/surge/main/Rule/SourceSnapshots/SpeedtestInternational.lsr",
    f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/Lsr/SpeedtestInternational.lsr",
)
SPEEDTEST_METACUBEX_SOURCES = (
    "https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/speedtest.mrs",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/speedtest.mrs",
    "https://cdn.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/speedtest.mrs",
)
SPEEDTEST_V2FLY_CATEGORY_SOURCES = (
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/category-speedtest",
    "https://cdn.jsdelivr.net/gh/v2fly/domain-list-community@master/data/category-speedtest",
)
SPEEDTEST_SUKKA_STATIC_SOURCES = (
    "https://raw.githubusercontent.com/SukkaW/Surge/master/Source/domainset/speedtest.conf",
    "https://cdn.jsdelivr.net/gh/SukkaW/Surge@master/Source/domainset/speedtest.conf",
)
SPEEDTEST_SUKKA_OOKLA_SOURCES = (
    "https://speedtest-net-servers.cdn.skk.moe/servers.json",
)
SPEEDTEST_LIBRESPEED_SOURCES = (
    "https://raw.githubusercontent.com/librespeed/speedtest/master/server-list.json",
    "https://cdn.jsdelivr.net/gh/librespeed/speedtest@master/server-list.json",
)
SPEEDTEST_SUKKA_LIBRESPEED_SOURCES = (
    "https://speedtest-net-servers.cdn.skk.moe/librespeed-servers.json",
)
SPEEDTEST_ONECLICK_SOURCES = (
    "https://raw.githubusercontent.com/oneclickvirt/speedtest/main/model/snapshot/speedtest-servers.json",
    "https://cdn.jsdelivr.net/gh/oneclickvirt/speedtest@main/model/snapshot/speedtest-servers.json",
)
SPEEDTEST_BLACKMATRIX_SOURCES = (
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Speedtest/Speedtest.list",
    "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Speedtest/Speedtest.list",
)
SPEEDTEST_FIXED_SUFFIXES = (
    "azurespeed.com",
    "bandwidthplace.com",
    "broadbandspeedchecker.co.uk",
    "broadbandspeedtest.org.uk",
    "fast.com",
    "fiber.google.com",
    "internethealthtest.org",
    "librespeed.org",
    "meter.net",
    "mlab-ns.appspot.com",
    "nperf.com",
    "openspeedtest.com",
    "speed.io",
    "speedcheck.org",
    "speedof.me",
    "speedsmart.net",
    "speedtest.org",
    "testmy.net",
)
SPEEDTEST_EXCLUDED_DOMAINS = {
    "7h15.ru1353t.1s.m4d3.by.5ukk4w.skk.moe",
    "chinatelecom.com.cn.dns.ink",
    "speedtest.dukekunshan.edu.cn",
    "speedtest.mfcyun.com",
}
SPEEDTEST_SHARED_GLOBAL_SERVER_SUFFIXES = {
    "ooklaserver.net",
}
FETCH_ATTEMPTS = 3
MIN_SPEEDTEST_DOMAIN_RECORDS = 15_000
MIN_SPEEDTEST_IP_RECORDS = 5
MIN_SUKKA_OOKLA_HOSTS = 1_000
MIN_LIBRESPEED_HOSTS = 10
MIN_V2FLY_MAINLAND_TAGS = 10
MIN_INDEPENDENT_SPEEDTEST_SOURCES = 5
SOURCES = (
    {
        "output": "SpeedtestInternational.mrs",
        "srs_output": "SpeedtestInternational.srs",
        "kind": "domain",
        "url": "https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/Lsr/SpeedtestInternational.lsr",
    },
    {
        "output": "SpeedtestInternational_ipcidr.mrs",
        "srs_output": "SpeedtestInternational_ipcidr.srs",
        "kind": "ipcidr",
        "url": "https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/Lsr/SpeedtestInternational.lsr",
    },
    {
        "output": "TelegramSG.mrs",
        "srs_output": "TelegramSG.srs",
        "kind": "ipcidr",
        "url": "https://rule.kelee.one/Loon/TelegramSG.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/TelegramSG.lsr",
    },
    {
        "output": "TelegramNL.mrs",
        "srs_output": "TelegramNL.srs",
        "kind": "ipcidr",
        "url": "https://rule.kelee.one/Loon/TelegramNL.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/TelegramNL.lsr",
    },
)


def fetch(url: str) -> bytes:
    last_error: Exception | None = None
    for attempt in range(FETCH_ATTEMPTS):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            sample = data[:512].lower()
            if b"attention required" in sample or b"cf-chl-" in sample:
                raise RuntimeError("Cloudflare challenge page returned")
            return data
        except (
            OSError,
            RuntimeError,
            http.client.HTTPException,
            urllib.error.URLError,
        ) as error:
            last_error = error
            if attempt + 1 < FETCH_ATTEMPTS:
                time.sleep(2**attempt)
    raise RuntimeError(f"download failed after {FETCH_ATTEMPTS} attempts: {last_error}")


def download_source(source: dict[str, str]) -> tuple[bytes, str]:
    return download_first((source["url"], source["fallback"]))


def download_first(urls: tuple[str, ...]) -> tuple[bytes, str]:
    failures: list[str] = []
    for url in urls:
        try:
            return fetch(url), url
        except (OSError, urllib.error.URLError, RuntimeError) as error:
            failures.append(f"{url}: {error}")
    raise RuntimeError("; ".join(failures))


def download_speedtest_source() -> tuple[bytes, str]:
    candidates = []
    for url in SPEEDTEST_KELEE_SOURCES:
        try:
            data = fetch(url)
            text = data.decode("utf-8-sig")
            timestamp_match = re.search(
                r"^#\s*UpdateTime:\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*$",
                text,
                re.MULTILINE,
            )
            count_match = re.search(r"^#\s*RuleCount:\s*(\d+)\s*$", text, re.MULTILINE)
            if not timestamp_match or not count_match:
                raise ValueError("missing upstream UpdateTime or RuleCount")
            updated = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
            domains = parse_lsr_records(data, "domain")
            networks = parse_lsr_records(data, "ipcidr")
            if len(domains) < MIN_SPEEDTEST_DOMAIN_RECORDS or len(networks) < MIN_SPEEDTEST_IP_RECORDS:
                raise ValueError("source is below the minimum domain/IP rule count")
            if len(domains) + len(networks) != int(count_match.group(1)):
                raise ValueError("RuleCount does not match the parsed unique rules")
            if any(kind not in {"DOMAIN", "DOMAIN-SUFFIX", "HOST", "HOST-SUFFIX"} for kind, _ in domains):
                raise ValueError("source contains unsupported domain matching semantics")
            fingerprint = frozenset((*domains, *networks))
            candidates.append((updated, data, url, fingerprint))
            print(f"Kelee candidate: {updated}, {len(domains)} domains, {len(networks)} IP rules; {url}")
        except (OSError, RuntimeError, ValueError, http.client.HTTPException) as error:
            print(f"WARNING: Kelee source unavailable or invalid: {url}: {error}")
    if not candidates:
        raise RuntimeError("No valid Kelee source is available; existing rule files are not replaced")
    latest = max(candidate[0] for candidate in candidates)
    state_path = ROOT / ".github/speedtest-source-state.json"
    if state_path.exists():
        previous = json.loads(state_path.read_text(encoding="utf-8"))
        previous_updated = datetime.strptime(previous["updated_at"], "%Y-%m-%d %H:%M:%S")
        if latest < previous_updated:
            raise RuntimeError(f"Kelee source would roll back from {previous_updated} to {latest}")
    freshest = [candidate for candidate in candidates if candidate[0] == latest]
    if any(candidate[3] != freshest[0][3] for candidate in freshest[1:]):
        raise RuntimeError("Kelee sources disagree at the same UpdateTime; refusing ambiguous data")
    _, data, url, _ = freshest[0]
    print(f"Kelee selected source: {latest}; {url}")
    if url != SPEEDTEST_KELEE_SOURCES[0]:
        print("WARNING: Using the newest validated Kelee mirror; original-site freshness is not confirmed")
    state = {
        "updated_at": latest.strftime("%Y-%m-%d %H:%M:%S"),
        "source": url,
        "sha256": hashlib.sha256(data).hexdigest(),
        "domain_rules": len(parse_lsr_records(data, "domain")),
        "ip_rules": len(parse_lsr_records(data, "ipcidr")),
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return data, url


def parse_lsr_records(data: bytes, kind: str) -> list[tuple[str, str]]:
    text = data.decode("utf-8-sig")
    entries: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    domain_types = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "HOST", "HOST-SUFFIX"}
    ip_types = {"IP-CIDR", "IP-CIDR6", "IP-ASN"}
    known_types = domain_types | ip_types
    accepted = domain_types if kind == "domain" else ip_types

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) < 2:
            raise ValueError(f"line {line_number}: expected a Loon rule with a value")
        rule_type, value = fields[0].upper(), fields[1]
        if rule_type not in known_types:
            raise ValueError(f"line {line_number}: unsupported rule type {rule_type}")
        if rule_type not in accepted:
            continue
        if not value:
            raise ValueError(f"line {line_number}: empty rule value")
        if rule_type not in {
            "DOMAIN",
            "DOMAIN-SUFFIX",
            "DOMAIN-KEYWORD",
            "HOST",
            "HOST-SUFFIX",
            "IP-CIDR",
            "IP-CIDR6",
        }:
            raise ValueError(
                f"line {line_number}: {rule_type} cannot be represented losslessly "
                f"by a Mihomo {kind} MRS file"
            )
        entry = (rule_type, value.removeprefix("*.").removeprefix("."))
        if entry not in seen:
            entries.append(entry)
            seen.add(entry)

    if not entries:
        raise ValueError(f"source contains no {kind} rules")
    return entries


def parse_lsr(data: bytes, kind: str) -> list[str]:
    entries: list[str] = []
    for rule_type, value in parse_lsr_records(data, kind):
        if rule_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"}:
            entries.append(f"+.{value}")
        else:
            entries.append(value)
    return entries


def records_to_entries(records: list[tuple[str, str]]) -> list[str]:
    return [
        f"+.{value}" if rule_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"} else value
        for rule_type, value in records
    ]


def mihomo_binary(directory: Path) -> Path:
    metadata_request = urllib.request.Request(
        MIHOMO_RELEASE_API,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(metadata_request, timeout=60) as response:
        release = json.load(response)

    candidates = [
        asset
        for asset in release.get("assets", [])
        if asset.get("name", "").startswith("mihomo-linux-amd64-compatible-")
        and asset.get("name", "").endswith(".gz")
    ]
    if not candidates:
        raise RuntimeError("no compatible Linux amd64 Mihomo release asset found")

    archive = directory / "mihomo.gz"
    binary = directory / "mihomo"
    archive.write_bytes(fetch(candidates[0]["browser_download_url"]))
    with gzip.open(archive, "rb") as compressed, binary.open("wb") as output:
        output.write(compressed.read())
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return binary


def singbox_binary(directory: Path) -> Path:
    metadata_request = urllib.request.Request(
        SINGBOX_RELEASE_API,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(metadata_request, timeout=60) as response:
        release = json.load(response)

    assets = [
        asset
        for asset in release.get("assets", [])
        if asset.get("name", "").startswith("sing-box-")
        and asset.get("name", "").endswith(".tar.gz")
    ]
    candidates = []
    for suffix in ("-linux-amd64.tar.gz", "-linux-amd64-glibc.tar.gz", "-linux-amd64-musl.tar.gz"):
        candidates = [asset for asset in assets if asset["name"].endswith(suffix)]
        if candidates:
            break
    if not candidates:
        raise RuntimeError("no Linux amd64 Sing-box release asset found")

    archive = directory / "sing-box.tar.gz"
    extract_directory = directory / "sing-box"
    archive.write_bytes(fetch(candidates[0]["browser_download_url"]))
    extract_directory.mkdir()
    with tarfile.open(archive, "r:gz") as compressed:
        compressed.extractall(extract_directory, filter="data")
    binaries = list(extract_directory.rglob("sing-box"))
    if not binaries:
        raise RuntimeError("Sing-box archive did not contain a binary")
    binary = binaries[0]
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return binary


def singbox_version(binary: Path) -> str:
    result = subprocess.run([str(binary), "version"], capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"unable to query Sing-box version: {detail}")
    return (result.stdout or result.stderr).strip().splitlines()[0]


def convert(binary: Path, input_path: Path, output_path: Path, kind: str) -> None:
    command = [str(binary), "convert-ruleset", kind, "text", str(input_path), str(output_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Mihomo conversion failed: {detail}")
    if not output_path.is_file() or output_path.read_bytes()[:4] != MRS_MAGIC:
        raise RuntimeError(f"{output_path.name}: converter did not produce a valid MRS file")


def compress_mrs_losslessly(output_path: Path) -> None:
    original = output_path.read_bytes()
    payload = zstd.decompress(original)
    compressed = zstd.compress(payload, level=19)
    if len(compressed) >= len(original):
        return
    if zstd.decompress(compressed) != payload:
        raise RuntimeError(f"{output_path.name}: lossless compression verification failed")
    output_path.write_bytes(compressed)
    print(f"{output_path.name}: lossless compression {len(original)} -> {len(compressed)} bytes")


def compress_srs_losslessly(output_path: Path) -> None:
    original = output_path.read_bytes()
    if len(original) < 6 or original[:3] != SRS_MAGIC:
        raise RuntimeError(f"{output_path.name}: invalid SRS header")
    payload = zlib.decompress(original[4:])
    compressed = original[:4] + zopfli.zlib.compress(payload, numiterations=15)
    if len(compressed) >= len(original):
        return
    if zlib.decompress(compressed[4:]) != payload:
        raise RuntimeError(f"{output_path.name}: lossless compression verification failed")
    output_path.write_bytes(compressed)
    print(f"{output_path.name}: lossless compression {len(original)} -> {len(compressed)} bytes")


def decode_mrs(binary: Path, input_path: Path, output_path: Path, kind: str) -> None:
    command = [
        str(binary),
        "convert-ruleset",
        kind,
        "mrs",
        str(input_path),
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Mihomo MRS decoding failed: {detail}")
    if not output_path.is_file() or not output_path.read_text(encoding="utf-8").strip():
        raise RuntimeError(f"{input_path.name}: converter produced an empty rule list")


def mrs_domain_records(mihomo: Path, data: bytes, workspace: Path, stem: str) -> list[tuple[str, str]]:
    if data[:4] != MRS_MAGIC:
        raise RuntimeError(f"{stem}: source has an invalid MRS/Zstandard header")
    input_path = workspace / f"{stem}.mrs"
    output_path = workspace / f"{stem}.txt"
    input_path.write_bytes(data)
    decode_mrs(mihomo, input_path, output_path, "domain")
    records: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entry in output_path.read_text(encoding="utf-8").splitlines():
        entry = entry.strip().lower()
        if not entry:
            continue
        if not DOMAIN_SET_ENTRY.fullmatch(entry):
            raise ValueError(f"{stem}: invalid domain entry {entry!r}")
        record = ("DOMAIN-SUFFIX", entry[2:]) if entry.startswith("+.") else ("DOMAIN", entry)
        if record not in seen:
            records.append(record)
            seen.add(record)
    if not records:
        raise RuntimeError(f"{stem}: source contains no domain rules")
    return records


def normalized_hostname(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    if "://" not in candidate and not candidate.startswith("//"):
        candidate = f"//{candidate}"
    try:
        hostname = urlsplit(candidate).hostname
    except ValueError:
        return None
    if not hostname:
        return None
    hostname = hostname.lower().rstrip(".")
    try:
        ipaddress.ip_address(hostname)
        return None
    except ValueError:
        pass
    if hostname.startswith("+.") or not DOMAIN_SET_ENTRY.fullmatch(hostname):
        return None
    return hostname


def json_list(data: bytes, source_name: str) -> list[dict]:
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"{source_name}: invalid JSON: {error}") from error
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        raise RuntimeError(f"{source_name}: expected a non-empty JSON object array")
    return value


def server_json_records(
    data: bytes,
    source_name: str,
    fields: tuple[str, ...],
    exclude_mainland: bool,
) -> tuple[list[tuple[str, str]], set[str]]:
    records: list[tuple[str, str]] = []
    seen: set[str] = set()
    mainland: set[str] = set()
    for item in json_list(data, source_name):
        country_code = str(item.get("cc", "")).strip().upper()
        country_name = str(item.get("country", "")).strip().lower()
        # ISO region codes distinguish Hong Kong from mainland China even when
        # a provider labels both with the broad country name "China".
        is_mainland = country_code == "CN" or (
            not country_code and country_name == "china"
        )
        for field in fields:
            hostname = normalized_hostname(item.get(field))
            if not hostname:
                continue
            if is_mainland:
                mainland.add(hostname)
                if exclude_mainland:
                    continue
            if hostname not in seen:
                records.append(("DOMAIN", hostname))
                seen.add(hostname)
    return records, mainland


def domainset_records(data: bytes, source_name: str) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as error:
        raise RuntimeError(f"{source_name}: invalid UTF-8: {error}") from error
    for line_number, raw_line in enumerate(lines, 1):
        entry = raw_line.split("#", 1)[0].strip().lower().rstrip(".")
        if not entry:
            continue
        rule_type = "DOMAIN-SUFFIX" if entry.startswith(".") else "DOMAIN"
        value = entry.removeprefix(".")
        if not DOMAIN_SET_ENTRY.fullmatch(value):
            raise ValueError(f"{source_name}:{line_number}: invalid domain {value!r}")
        record = (rule_type, value)
        if record not in seen:
            records.append(record)
            seen.add(record)
    if not records:
        raise RuntimeError(f"{source_name}: source contains no domain rules")
    return records


def v2fly_category_records(
    data: bytes,
    source_name: str,
) -> tuple[list[tuple[str, str]], set[str]]:
    records: list[tuple[str, str]] = []
    mainland: set[str] = set()
    seen: set[tuple[str, str]] = set()
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as error:
        raise RuntimeError(f"{source_name}: invalid UTF-8: {error}") from error

    for line_number, raw_line in enumerate(lines, 1):
        fields = raw_line.split("#", 1)[0].strip().lower().split()
        if not fields:
            continue
        entry, attributes = fields[0], set(fields[1:])
        if entry.startswith(("include:", "regexp:", "keyword:")) or "@ads" in attributes:
            continue

        exact = entry.startswith("full:")
        value = entry.removeprefix("full:").removeprefix("domain:").rstrip(".")
        if not DOMAIN_SET_ENTRY.fullmatch(value):
            raise ValueError(f"{source_name}:{line_number}: invalid domain {value!r}")
        if "@cn" in attributes and "@!cn" not in attributes:
            mainland.add(value)
            continue

        record = ("DOMAIN" if exact else "DOMAIN-SUFFIX", value)
        if record not in seen:
            records.append(record)
            seen.add(record)

    if not records or not mainland:
        raise RuntimeError(f"{source_name}: expected both foreign and @cn domain rules")
    return records, mainland


def loon_domain_records(data: bytes, source_name: str) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as error:
        raise RuntimeError(f"{source_name}: invalid UTF-8: {error}") from error
    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) < 2:
            raise ValueError(f"{source_name}:{line_number}: malformed Loon rule")
        rule_type = fields[0].upper()
        if rule_type == "DOMAIN-KEYWORD":
            continue
        if rule_type not in {"DOMAIN", "DOMAIN-SUFFIX", "HOST", "HOST-SUFFIX"}:
            continue
        value = fields[1].removeprefix("*.").removeprefix(".").lower().rstrip(".")
        if not DOMAIN_SET_ENTRY.fullmatch(value):
            raise ValueError(f"{source_name}:{line_number}: invalid domain {value!r}")
        normalized_type = "DOMAIN-SUFFIX" if rule_type.endswith("SUFFIX") else "DOMAIN"
        record = (normalized_type, value)
        if record not in seen:
            records.append(record)
            seen.add(record)
    if not records:
        raise RuntimeError(f"{source_name}: source contains no exact or suffix domain rules")
    return records


def speedtest_namespace_suffixes(
    exact_domains: set[str],
    blocked_domains: set[str],
) -> set[str]:
    candidates: dict[str, set[str]] = {}
    minimum_hosts: dict[str, int] = {}
    for domain in exact_domains:
        labels = domain.split(".")
        for index, label in enumerate(labels[:-1]):
            if not SPEEDTEST_NAMESPACE_LABEL.fullmatch(label):
                continue
            namespace = ".".join(labels[index:])
            if namespace in SPEEDTEST_SHARED_GLOBAL_SERVER_SUFFIXES:
                continue
            if any(
                blocked == namespace or blocked.endswith(f".{namespace}")
                for blocked in blocked_domains
            ):
                continue
            candidates.setdefault(namespace, set()).add(domain)
            minimum_hosts[namespace] = 3 if label == "st" else 2

    return {
        namespace
        for namespace, covered_domains in candidates.items()
        if len(covered_domains) >= minimum_hosts[namespace]
    }


def compact_domain_records(
    records: list[tuple[str, str]],
    blocked_domains: set[str] | None = None,
) -> list[tuple[str, str]]:
    blocked_domains = blocked_domains or set()
    exact: set[str] = set()
    suffixes: set[str] = set()
    for rule_type, raw_value in records:
        value = raw_value.lower().removeprefix("*.").removeprefix(".").rstrip(".")
        if rule_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"}:
            suffixes.add(value)
        elif rule_type in {"DOMAIN", "HOST"}:
            exact.add(value)

    # Promote only explicitly Speedtest-named namespaces with multiple verified
    # servers. This keeps future hosts covered without widening an ISP's whole
    # registrable domain (for example, never promoting all of rogers.com).
    suffixes = {
        suffix
        for suffix in suffixes
        if not any(
            blocked == suffix or blocked.endswith(f".{suffix}")
            for blocked in blocked_domains
        )
    }
    suffixes.update(speedtest_namespace_suffixes(exact, blocked_domains))

    compact_suffixes: list[str] = []
    for suffix in sorted(suffixes, key=lambda value: (value.count("."), len(value), value)):
        if any(suffix == parent or suffix.endswith(f".{parent}") for parent in compact_suffixes):
            continue
        compact_suffixes.append(suffix)

    compact_exact = sorted(
        domain
        for domain in exact
        if not any(
            domain == suffix or domain.endswith(f".{suffix}")
            for suffix in compact_suffixes
        )
    )
    return [
        *(('DOMAIN-SUFFIX', suffix) for suffix in sorted(compact_suffixes)),
        *(('DOMAIN', domain) for domain in compact_exact),
    ]


def domain_coverage_index(records: list[tuple[str, str]]) -> tuple[set[str], set[str]]:
    exact = {
        candidate.lower().removeprefix("*.").removeprefix(".").rstrip(".")
        for candidate_type, candidate in records
        if candidate_type in {"DOMAIN", "HOST"}
    }
    suffixes = {
        candidate.lower().removeprefix("*.").removeprefix(".").rstrip(".")
        for candidate_type, candidate in records
        if candidate_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"}
    }
    return exact, suffixes


def domain_record_is_covered(
    record: tuple[str, str],
    coverage: tuple[set[str], set[str]],
) -> bool:
    rule_type, raw_value = record
    value = raw_value.lower().removeprefix("*.").removeprefix(".").rstrip(".")
    exact, suffixes = coverage
    if rule_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"}:
        return any(value == suffix or value.endswith(f".{suffix}") for suffix in suffixes)
    return value in exact or any(value == suffix or value.endswith(f".{suffix}") for suffix in suffixes)


def excluded_speedtest_domain(
    record: tuple[str, str],
    mainland_domains: set[str],
) -> bool:
    rule_type, raw_value = record
    if rule_type not in {"DOMAIN", "HOST", "DOMAIN-SUFFIX", "HOST-SUFFIX"}:
        return False
    value = raw_value.lower().removeprefix("*.").removeprefix(".").rstrip(".")
    return (
        value in SPEEDTEST_SHARED_GLOBAL_SERVER_SUFFIXES
        or value.endswith(".cn")
        or (
            rule_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"}
            and any(
                mainland == value or mainland.endswith(f".{value}")
                for mainland in mainland_domains
            )
        )
        or any(
            value == mainland or value.endswith(f".{mainland}")
            for mainland in mainland_domains
        )
    )


def speedtest_source_groups(
    mihomo: Path,
    workspace: Path,
) -> tuple[list[tuple[str, list[tuple[str, str]], str]], set[str]]:
    groups: list[tuple[str, list[tuple[str, str]], str]] = []
    failures: list[str] = []
    mainland_domains: set[str] = set(SPEEDTEST_EXCLUDED_DOMAINS)

    def collect(name: str, urls: tuple[str, ...], parser, minimum: int) -> None:
        try:
            data, used_url = download_first(urls)
            records = parser(data)
            if len(records) < minimum:
                raise RuntimeError(f"expected at least {minimum} rules, received {len(records)}")
            groups.append((name, records, used_url))
        except (OSError, ValueError, RuntimeError, urllib.error.URLError) as error:
            failures.append(f"{name}: {error}")
            print(f"WARNING: ignored unavailable or invalid {name} source: {error}")

    collect(
        "MetaCubeX",
        SPEEDTEST_METACUBEX_SOURCES,
        lambda data: mrs_domain_records(mihomo, data, workspace, "speedtest-metacubex"),
        10,
    )

    def parse_v2fly(data: bytes) -> list[tuple[str, str]]:
        records, excluded = v2fly_category_records(
            data,
            "V2Fly category-speedtest",
        )
        if len(excluded) < MIN_V2FLY_MAINLAND_TAGS:
            raise RuntimeError(
                f"V2Fly category-speedtest: expected at least "
                f"{MIN_V2FLY_MAINLAND_TAGS} @cn rules, received {len(excluded)}"
            )
        mainland_domains.update(excluded)
        return records

    collect(
        "V2Fly category-speedtest",
        SPEEDTEST_V2FLY_CATEGORY_SOURCES,
        parse_v2fly,
        30,
    )
    collect(
        "Sukka static",
        SPEEDTEST_SUKKA_STATIC_SOURCES,
        lambda data: domainset_records(data, "Sukka speedtest.conf"),
        100,
    )
    def parse_sukka_ookla(data: bytes) -> list[tuple[str, str]]:
        records, excluded = server_json_records(
            data,
            "Sukka Ookla servers",
            ("host", "url"),
            exclude_mainland=True,
        )
        mainland_domains.update(excluded)
        return records

    collect(
        "Sukka live Ookla",
        SPEEDTEST_SUKKA_OOKLA_SOURCES,
        parse_sukka_ookla,
        MIN_SUKKA_OOKLA_HOSTS,
    )
    collect(
        "LibreSpeed official",
        SPEEDTEST_LIBRESPEED_SOURCES,
        lambda data: server_json_records(
            data,
            "LibreSpeed servers",
            ("server",),
            exclude_mainland=True,
        )[0],
        MIN_LIBRESPEED_HOSTS,
    )
    collect(
        "Sukka LibreSpeed mirror",
        SPEEDTEST_SUKKA_LIBRESPEED_SOURCES,
        lambda data: server_json_records(
            data,
            "Sukka LibreSpeed servers",
            ("server",),
            exclude_mainland=True,
        )[0],
        MIN_LIBRESPEED_HOSTS,
    )

    def parse_oneclick(data: bytes) -> list[tuple[str, str]]:
        records, excluded = server_json_records(
            data,
            "oneclickvirt speedtest snapshot",
            ("host", "url"),
            exclude_mainland=True,
        )
        mainland_domains.update(excluded)
        return records

    collect(
        "oneclickvirt snapshot",
        SPEEDTEST_ONECLICK_SOURCES,
        parse_oneclick,
        100,
    )
    collect(
        "blackmatrix7",
        SPEEDTEST_BLACKMATRIX_SOURCES,
        lambda data: loon_domain_records(data, "blackmatrix7 Speedtest.list"),
        4,
    )
    groups.append(
        (
            "curated international platforms",
            [("DOMAIN-SUFFIX", domain) for domain in SPEEDTEST_FIXED_SUFFIXES],
            "built-in reviewed list",
        )
    )

    successful_external = len(groups) - 1
    if successful_external < MIN_INDEPENDENT_SPEEDTEST_SOURCES:
        raise RuntimeError(
            f"only {successful_external} independent Speedtest supplemental sources succeeded; "
            f"at least {MIN_INDEPENDENT_SPEEDTEST_SOURCES} are required"
        )

    if failures:
        existing = ROOT / "SpeedtestInternational.mrs"
        if not existing.is_file() or existing.read_bytes()[:4] != MRS_MAGIC:
            raise RuntimeError("supplemental sources failed and no valid previous Speedtest MRS is available")
        previous = mrs_domain_records(
            mihomo,
            existing.read_bytes(),
            workspace,
            "speedtest-previous",
        )
        groups.append(("validated previous release", previous, str(existing)))
        print(f"Preserving the previous release because {len(failures)} supplemental source group(s) failed")

    return groups, mainland_domains


def decompile_srs(binary: Path, input_path: Path, output_path: Path) -> list[dict]:
    command = [
        str(binary),
        "rule-set",
        "decompile",
        str(input_path),
        "-o",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Sing-box SRS decompilation failed: {detail}")
    try:
        source = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"{input_path.name}: invalid decompiled rule-set: {error}") from error
    rules = source.get("rules") if isinstance(source, dict) else None
    if not isinstance(rules, list) or not rules or not all(isinstance(rule, dict) for rule in rules):
        raise RuntimeError(f"{input_path.name}: decompiled rule-set contains no rules")
    return rules


def singbox_rule(domain: list[str] | None = None, domain_suffix: list[str] | None = None,
                 domain_keyword: list[str] | None = None, ip_cidr: list[str] | None = None) -> dict[str, list[str]]:
    rule: dict[str, list[str]] = {}
    for key, values in (
        ("domain", domain),
        ("domain_suffix", domain_suffix),
        ("domain_keyword", domain_keyword),
        ("ip_cidr", ip_cidr),
    ):
        if values:
            rule[key] = values
    return rule


def current_srs_source_version(binary: Path) -> int:
    result = subprocess.run(
        [str(binary), "rule-set", "upgrade", "stdin"],
        input=json.dumps({"version": 1, "rules": []}),
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Sing-box rule-set version detection failed: {detail}")
    upgraded = json.loads(result.stdout)
    version = upgraded.get("version")
    if type(version) is not int or version < 1 or upgraded.get("rules", []) != []:
        raise RuntimeError("Sing-box returned an invalid upgraded rule-set version")
    return version


def compile_srs(binary: Path, rules: list[dict[str, list[str]]], output_path: Path) -> None:
    source_version = current_srs_source_version(binary)
    source_path = output_path.with_suffix(".json")
    source_path.write_text(
        json.dumps({"version": source_version, "rules": rules}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    command = [str(binary), "rule-set", "compile", str(source_path), "-o", str(output_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Sing-box SRS compilation failed: {detail}")
    if not output_path.is_file() or output_path.read_bytes()[:3] != SRS_MAGIC:
        raise RuntimeError(f"{output_path.name}: compiler did not produce a valid SRS file")
    data = output_path.read_bytes()
    if len(data) <= 4 or not 1 <= data[3] <= source_version:
        raise RuntimeError(f"{output_path.name}: compiler produced an invalid SRS version")
    print(
        f"{output_path.name}: latest source format v{source_version}, "
        f"official compiler selected binary format v{data[3]}"
    )


def records_to_srs_rules(records: list[tuple[str, str]], kind: str) -> list[dict[str, list[str]]]:
    domains: list[str] = []
    suffixes: list[str] = []
    keywords: list[str] = []
    cidrs: list[str] = []
    for rule_type, value in records:
        if rule_type in {"DOMAIN", "HOST"}:
            domains.append(value)
        elif rule_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"}:
            suffixes.append(value)
        elif rule_type == "DOMAIN-KEYWORD":
            keywords.append(value)
        elif rule_type in {"IP-CIDR", "IP-CIDR6"}:
            cidrs.append(value)
        else:
            raise ValueError(f"{rule_type} cannot be represented by Sing-box SRS")
    if kind == "domain" and cidrs:
        raise ValueError("domain SRS cannot contain IP-CIDR rules")
    if kind == "ipcidr" and (domains or suffixes or keywords):
        raise ValueError("ipcidr SRS cannot contain domain rules")
    rule = singbox_rule(
        domain=domains,
        domain_suffix=suffixes,
        domain_keyword=keywords,
        ip_cidr=cidrs,
    )
    if not rule:
        raise ValueError("source contains no rules for Sing-box SRS")
    return [rule]


def update_nodeseek(binary: Path, singbox: Path, workspace: Path) -> None:
    data, used_url = download_first(NODESEEK_SOURCES)
    if data[:4] != MRS_MAGIC:
        raise RuntimeError("nodeseek.mrs: source has an invalid MRS/Zstandard header")

    input_path = workspace / "nodeseek.mrs"
    output_path = workspace / "nodeseek.txt"
    input_path.write_bytes(data)
    decode_mrs(binary, input_path, output_path, "domain")

    decoded_lines = output_path.read_text(encoding="utf-8").splitlines()
    entries = list(dict.fromkeys(line.strip() for line in decoded_lines if line.strip()))
    if any(not DOMAIN_SET_ENTRY.fullmatch(entry) for entry in entries):
        raise ValueError(
            "nodeseek.mrs: source contains a rule unsupported by Egern domain-set YAML"
        )
    yaml_text = "payload:\n" + "".join(f"  - {entry}\n" for entry in entries)
    temporary_output = workspace / "Nodeseek.yaml"
    temporary_output.write_text(yaml_text, encoding="utf-8")
    temporary_output.replace(ROOT / "Nodeseek.yaml")
    srs_output = workspace / "Nodeseek.srs"
    compile_srs(
        singbox,
        [
            singbox_rule(
                domain=[entry for entry in entries if not entry.startswith("+.")],
                domain_suffix=[entry[2:] for entry in entries if entry.startswith("+.")],
            )
        ],
        srs_output,
    )
    srs_output.replace(ROOT / "Nodeseek.srs")
    print(f"Nodeseek.yaml: {len(entries)} rules from {used_url}")
    print(f"Nodeseek.srs: {len(entries)} rules from {used_url}")


def webrtc_entries(mihomo: Path, input_path: Path, output_path: Path) -> list[str]:
    decode_mrs(mihomo, input_path, output_path, "domain")
    entries = list(
        dict.fromkeys(
            line.strip()
            for line in output_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    )
    if any(not DOMAIN_SET_ENTRY.fullmatch(entry) for entry in entries):
        raise ValueError("Webrtc_domain.mrs: source contains an invalid domain")
    return entries


def preserve_existing_webrtc(mihomo: Path, singbox: Path, workspace: Path, download_error: RuntimeError) -> None:
    existing_mrs = ROOT / "Webrtc_domain.mrs"
    existing_srs = ROOT / "Webrtc_domain.srs"
    if not existing_mrs.is_file() or existing_mrs.read_bytes()[:4] != MRS_MAGIC:
        raise RuntimeError(f"WebRTC sources are unavailable and no valid existing MRS is present: {download_error}")
    if not existing_srs.is_file() or existing_srs.read_bytes()[:3] != SRS_MAGIC:
        raise RuntimeError(f"WebRTC sources are unavailable and no valid existing SRS is present: {download_error}")

    entries = webrtc_entries(
        mihomo,
        existing_mrs,
        workspace / "Webrtc_domain_existing.txt",
    )
    expected_rules = [
        singbox_rule(
            domain=[entry for entry in entries if not entry.startswith("+.")],
            domain_suffix=[entry[2:] for entry in entries if entry.startswith("+.")],
        )
    ]
    existing_rules = decompile_srs(
        singbox,
        existing_srs,
        workspace / "Webrtc_domain_existing.json",
    )
    if existing_rules != expected_rules:
        raise RuntimeError(f"WebRTC sources are unavailable and the existing MRS/SRS rules differ: {download_error}")
    print(
        f"WARNING: WebRTC sources are unavailable; preserving {len(entries)} validated existing rules: "
        f"{download_error}"
    )


def update_webrtc(mihomo: Path, singbox: Path, workspace: Path) -> None:
    try:
        data, used_url = download_first(WEBRTC_SOURCES)
    except RuntimeError as error:
        preserve_existing_webrtc(mihomo, singbox, workspace, error)
        return
    if data[:4] != MRS_MAGIC:
        raise RuntimeError("Webrtc_domain.mrs: source has an invalid MRS/Zstandard header")
    input_path = workspace / "Webrtc_domain_source.mrs"
    output_path = workspace / "Webrtc_domain_source.txt"
    input_path.write_bytes(data)
    entries = webrtc_entries(mihomo, input_path, output_path)
    temporary_output = workspace / "Webrtc_domain.srs"
    compile_srs(
        singbox,
        [
            singbox_rule(
                domain=[entry for entry in entries if not entry.startswith("+.")],
                domain_suffix=[entry[2:] for entry in entries if entry.startswith("+.")],
            )
        ],
        temporary_output,
    )
    input_path.replace(ROOT / "Webrtc_domain.mrs")
    temporary_output.replace(ROOT / "Webrtc_domain.srs")
    print(f"Webrtc_domain.mrs: {len(entries)} rules from {used_url}")
    print(f"Webrtc_domain.srs: {len(entries)} rules from {used_url}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mihomo-rule-update-") as temporary:
        workspace = Path(temporary)
        binary = mihomo_binary(workspace)
        singbox = singbox_binary(workspace)
        print(f"Using {singbox_version(singbox)}")
        update_nodeseek(binary, singbox, workspace)
        update_webrtc(binary, singbox, workspace)
        speedtest_groups, mainland_speedtest_domains = speedtest_source_groups(binary, workspace)
        source_cache: dict[tuple[str, str], tuple[bytes, str]] = {}
        for source in SOURCES:
            cache_key = (source["url"], source["fallback"])
            if cache_key not in source_cache:
                source_cache[cache_key] = (
                    download_speedtest_source()
                    if source["output"].startswith("SpeedtestInternational")
                    else download_source(source)
                )
            data, used_url = source_cache[cache_key]
            records = parse_lsr_records(data, source["kind"])
            if source["output"] == "SpeedtestInternational.mrs":
                if len(records) < MIN_SPEEDTEST_DOMAIN_RECORDS:
                    raise RuntimeError(
                        f"Kelee Speedtest domain source shrank to {len(records)} rules; "
                        f"at least {MIN_SPEEDTEST_DOMAIN_RECORDS} are required"
                    )
                filtered_records = [
                    record
                    for record in records
                    if not excluded_speedtest_domain(record, mainland_speedtest_domains)
                ]
                print(
                    f"Kelee international base: {len(records)} domain rules, "
                    f"excluded {len(records) - len(filtered_records)} known mainland endpoint(s)"
                )
                merged_records = compact_domain_records(
                    filtered_records,
                    mainland_speedtest_domains,
                )
                all_source_records = list(filtered_records)
                for group_name, group_records, group_url in speedtest_groups:
                    filtered_group = [
                        record
                        for record in group_records
                        if not excluded_speedtest_domain(record, mainland_speedtest_domains)
                    ]
                    excluded_count = len(group_records) - len(filtered_group)
                    coverage = domain_coverage_index(merged_records)
                    new_coverage = sum(
                        not domain_record_is_covered(record, coverage)
                        for record in filtered_group
                    )
                    covered = len(filtered_group) - new_coverage
                    all_source_records.extend(filtered_group)
                    merged_records = compact_domain_records(
                        [*merged_records, *filtered_group],
                        mainland_speedtest_domains,
                    )
                    print(
                        f"  {group_name}: {len(group_records)} validated rules, "
                        f"{excluded_count} excluded, {covered} already covered, "
                        f"{new_coverage} additional; {group_url}"
                    )
                final_coverage = domain_coverage_index(merged_records)
                missing = [
                    record
                    for record in all_source_records
                    if not domain_record_is_covered(record, final_coverage)
                ]
                if missing:
                    raise RuntimeError(
                        f"Speedtest semantic compaction lost {len(missing)} source rule(s): {missing[:5]}"
                    )
                covered_mainland = sorted(
                    domain
                    for domain in mainland_speedtest_domains
                    if domain_record_is_covered(("DOMAIN", domain), final_coverage)
                )
                if covered_mainland:
                    raise RuntimeError(
                        "Speedtest strict region audit still covers known mainland "
                        f"domain(s): {covered_mainland[:5]}"
                    )
                final_exact, final_suffixes = final_coverage
                retained_shared_suffixes = sorted(
                    final_suffixes & SPEEDTEST_SHARED_GLOBAL_SERVER_SUFFIXES
                )
                retained_cn_domains = sorted(
                    domain
                    for domain in final_exact | final_suffixes
                    if domain.endswith(".cn")
                )
                if retained_shared_suffixes or retained_cn_domains:
                    raise RuntimeError(
                        "Speedtest strict region audit retained an unsafe shared "
                        f"suffix or .cn domain: "
                        f"{[*retained_shared_suffixes, *retained_cn_domains][:5]}"
                    )
                print(
                    "Speedtest strict region audit: "
                    f"{len(mainland_speedtest_domains)} known mainland namespace(s) "
                    "and shared global server suffixes excluded"
                )
                print(
                    f"Speedtest semantic compaction: {len(all_source_records)} source records -> "
                    f"{len(merged_records)} rules with identical-or-broader reviewed coverage"
                )
                records = merged_records
            elif source["output"] == "SpeedtestInternational_ipcidr.mrs" and len(records) < MIN_SPEEDTEST_IP_RECORDS:
                raise RuntimeError(
                    f"Kelee Speedtest IP source shrank to {len(records)} rules; "
                    f"at least {MIN_SPEEDTEST_IP_RECORDS} are required"
                )
            entries = records_to_entries(records)
            input_path = workspace / f"{source['output']}.txt"
            temporary_output = workspace / source["output"]
            input_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
            convert(binary, input_path, temporary_output, source["kind"])
            if source["output"].startswith("SpeedtestInternational"):
                compress_mrs_losslessly(temporary_output)
            temporary_output.replace(ROOT / source["output"])
            srs_output = workspace / source["srs_output"]
            srs_rules = records_to_srs_rules(records, source["kind"])
            compile_srs(singbox, srs_rules, srs_output)
            if source["srs_output"].startswith("SpeedtestInternational"):
                compress_srs_losslessly(srs_output)
                decompile_srs(
                    singbox, srs_output, workspace / f"{source['srs_output']}.verified.json"
                )
            srs_output.replace(ROOT / source["srs_output"])
            print(f"{source['output']}: {len(entries)} rules from {used_url}")
            print(f"{source['srs_output']}: {len(records)} Loon records from {used_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
