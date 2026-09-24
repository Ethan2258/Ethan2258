from __future__ import annotations

import gzip
import hashlib
import http.client
import ipaddress
import json
import platform
import re
import stat
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


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
NODESEEK_SOURCES = (
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/nodeseek.mrs",
    "https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs",
)
WEBRTC_SOURCES = (
    "https://raw.githubusercontent.com/MeALiYeYe/ProxyConfigFiles/main/Mihomo/rule/WebRTC/WebRTC.mrs",
    "https://cdn.jsdelivr.net/gh/MeALiYeYe/ProxyConfigFiles@main/Mihomo/rule/WebRTC/WebRTC.mrs",
)
TELEGRAM_OFFICIAL_CIDR_SOURCES = (
    "https://core.telegram.org/resources/cidr.txt",
)
FETCH_ATTEMPTS = 3
SOURCES = (
    {
        "output": "TelegramSG.mrs",
        "srs_output": "TelegramSG.srs",
        "kind": "ipcidr",
        "url": "https://rule.kelee.one/Loon/TelegramSG.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/TelegramSG.lsr",
        "mirrors": (
            "https://raw.githubusercontent.com/Qmxn/Tool/X/Loon/Rule/TelegramSG/TelegramSG.lsr",
        ),
    },
    {
        "output": "TelegramNL.mrs",
        "srs_output": "TelegramNL.srs",
        "kind": "ipcidr",
        "url": "https://rule.kelee.one/Loon/TelegramNL.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/TelegramNL.lsr",
        "mirrors": (
            "https://raw.githubusercontent.com/Qmxn/Tool/X/Loon/Rule/TelegramNL/TelegramNL.lsr",
        ),
    },
)
RULE_ARTIFACTS = {
    "NodeSeek": {
        "kind": "domain",
        "files": ("Nodeseek.yaml", "Nodeseek.mrs", "Nodeseek.srs"),
    },
    "WebRTC": {
        "kind": "domain",
        "files": ("Webrtc_domain.mrs", "Webrtc_domain.srs"),
    },
    "TelegramSG": {
        "kind": "ipcidr",
        "files": ("TelegramSG.mrs", "TelegramSG.srs"),
    },
    "TelegramNL": {
        "kind": "ipcidr",
        "files": ("TelegramNL.mrs", "TelegramNL.srs"),
    },
}


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


def source_urls(source: dict) -> tuple[str, ...]:
    return (source["url"], source["fallback"], *source.get("mirrors", ()))


def download_rule_source(source: dict) -> tuple[bytes, str, list[tuple[str, str]]]:
    failures: list[str] = []
    for url in source_urls(source):
        try:
            data = fetch(url)
            return data, url, parse_lsr_records(data, source["kind"])
        except (OSError, RuntimeError, ValueError, urllib.error.URLError) as error:
            failures.append(f"{url}: {error}")
    raise RuntimeError("; ".join(failures))


def download_first(urls: tuple[str, ...]) -> tuple[bytes, str]:
    failures: list[str] = []
    for url in urls:
        try:
            return fetch(url), url
        except (OSError, urllib.error.URLError, RuntimeError) as error:
            failures.append(f"{url}: {error}")
    raise RuntimeError("; ".join(failures))


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
        value = value.removeprefix("*.").removeprefix(".").strip()
        if rule_type in {"DOMAIN", "DOMAIN-SUFFIX", "HOST", "HOST-SUFFIX"}:
            value = value.lower().rstrip(".")
            if not DOMAIN_SET_ENTRY.fullmatch(value):
                raise ValueError(f"line {line_number}: invalid domain value {value!r}")
        elif rule_type == "DOMAIN-KEYWORD":
            value = value.lower()
        elif rule_type in {"IP-CIDR", "IP-CIDR6"}:
            try:
                network = ipaddress.ip_network(value, strict=False)
            except ValueError as error:
                raise ValueError(
                    f"line {line_number}: invalid network {value!r}"
                ) from error
            expected_version = 6 if rule_type == "IP-CIDR6" else 4
            if network.version != expected_version:
                raise ValueError(
                    f"line {line_number}: {rule_type} contains IPv{network.version}"
                )
            value = network.with_prefixlen
        entry = (rule_type, value)
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

    windows = platform.system() == "Windows"
    prefix = "mihomo-windows-amd64-compatible-" if windows else "mihomo-linux-amd64-compatible-"
    suffix = ".zip" if windows else ".gz"
    candidates = [
        asset
        for asset in release.get("assets", [])
        if asset.get("name", "").startswith(prefix)
        and asset.get("name", "").endswith(suffix)
    ]
    if not candidates:
        raise RuntimeError(
            f"no compatible {platform.system()} amd64 Mihomo release asset found"
        )

    archive = directory / f"mihomo{suffix}"
    binary = directory / ("mihomo.exe" if windows else "mihomo")
    archive.write_bytes(fetch(candidates[0]["browser_download_url"]))
    if windows:
        with zipfile.ZipFile(archive) as compressed:
            executables = [name for name in compressed.namelist() if name.endswith(".exe")]
            if not executables:
                raise RuntimeError("Mihomo archive did not contain an executable")
            binary.write_bytes(compressed.read(executables[0]))
    else:
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

    windows = platform.system() == "Windows"
    archive_suffix = ".zip" if windows else ".tar.gz"
    assets = [
        asset
        for asset in release.get("assets", [])
        if asset.get("name", "").startswith("sing-box-")
        and asset.get("name", "").endswith(archive_suffix)
    ]
    candidates = []
    suffixes = (
        ("-windows-amd64.zip",)
        if windows
        else (
            "-linux-amd64.tar.gz",
            "-linux-amd64-glibc.tar.gz",
            "-linux-amd64-musl.tar.gz",
        )
    )
    for suffix in suffixes:
        candidates = [asset for asset in assets if asset["name"].endswith(suffix)]
        if candidates:
            break
    if not candidates:
        raise RuntimeError(
            f"no {platform.system()} amd64 Sing-box release asset found"
        )

    archive = directory / f"sing-box{archive_suffix}"
    extract_directory = directory / "sing-box"
    archive.write_bytes(fetch(candidates[0]["browser_download_url"]))
    extract_directory.mkdir()
    if windows:
        with zipfile.ZipFile(archive) as compressed:
            compressed.extractall(extract_directory)
    else:
        with tarfile.open(archive, "r:gz") as compressed:
            compressed.extractall(extract_directory, filter="data")
    binary_name = "sing-box.exe" if windows else "sing-box"
    binaries = list(extract_directory.rglob(binary_name))
    if not binaries:
        raise RuntimeError("Sing-box archive did not contain a binary")
    binary = binaries[0]
    if not windows:
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return binary


def singbox_version(binary: Path) -> str:
    result = subprocess.run([str(binary), "version"], capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"unable to query Sing-box version: {detail}")
    return (result.stdout or result.stderr).strip().splitlines()[0]


def mihomo_version(binary: Path) -> str:
    result = subprocess.run([str(binary), "-v"], capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"unable to query Mihomo version: {detail}")
    fields = (result.stdout or result.stderr).strip().splitlines()[0].split()
    if len(fields) < 3:
        raise RuntimeError("unable to parse Mihomo version")
    return " ".join(fields[:3])


def convert(binary: Path, input_path: Path, output_path: Path, kind: str) -> None:
    command = [str(binary), "convert-ruleset", kind, "text", str(input_path), str(output_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Mihomo conversion failed: {detail}")
    if not output_path.is_file() or output_path.read_bytes()[:4] != MRS_MAGIC:
        raise RuntimeError(f"{output_path.name}: converter did not produce a valid MRS file")


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


def verify_mrs(
    binary: Path,
    input_path: Path,
    kind: str,
    expected_records: list[tuple[str, str]],
    workspace: Path,
) -> None:
    output_path = workspace / f"{input_path.name}.verified.txt"
    decode_mrs(binary, input_path, output_path, kind)
    actual = {
        line.strip()
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    expected = set(records_to_entries(expected_records))
    if actual != expected:
        raise RuntimeError(
            f"{input_path.name}: generated MRS differs from its normalized source "
            f"({len(actual)} decoded, {len(expected)} expected)"
        )


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


def download_domain_mrs(
    mihomo: Path,
    urls: tuple[str, ...],
    workspace: Path,
    stem: str,
    minimum_rules: int,
) -> tuple[bytes, str, list[tuple[str, str]]]:
    failures: list[str] = []
    for index, url in enumerate(urls):
        try:
            data = fetch(url)
            records = mrs_domain_records(
                mihomo,
                data,
                workspace,
                f"{stem}-{index}",
            )
            if len(records) < minimum_rules:
                raise RuntimeError(
                    f"expected at least {minimum_rules} rules, received {len(records)}"
                )
            return data, url, records
        except (OSError, RuntimeError, ValueError, urllib.error.URLError) as error:
            failures.append(f"{url}: {error}")
    raise RuntimeError("; ".join(failures))


def telegram_official_networks() -> tuple[
    list[ipaddress.IPv4Network | ipaddress.IPv6Network], bytes, str
]:
    data, used_url = download_first(TELEGRAM_OFFICIAL_CIDR_SOURCES)
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as error:
        raise RuntimeError(f"Telegram official CIDR list is not UTF-8: {error}") from error
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for line_number, raw_line in enumerate(lines, 1):
        value = raw_line.strip()
        if not value:
            continue
        try:
            networks.append(ipaddress.ip_network(value, strict=True))
        except ValueError as error:
            raise RuntimeError(
                f"Telegram official CIDR line {line_number} is invalid: {value!r}"
            ) from error
    if len(networks) < 10 or not {network.version for network in networks} == {4, 6}:
        raise RuntimeError("Telegram official CIDR list is unexpectedly small or not dual-stack")
    return networks, data, used_url


def validate_telegram_records(
    name: str,
    records: list[tuple[str, str]],
    official_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    networks = [ipaddress.ip_network(value, strict=True) for _, value in records]
    outside = [
        network
        for network in networks
        if not any(
            network.version == official.version and network.subnet_of(official)
            for official in official_networks
        )
    ]
    if outside:
        raise RuntimeError(f"{name}: CIDRs outside Telegram official ranges: {outside}")
    return networks


def write_artifact_manifest(
    counts: dict[str, int],
    mihomo: str,
    singbox: str,
) -> None:
    rule_sets = {}
    for name, specification in RULE_ARTIFACTS.items():
        if name not in counts:
            raise RuntimeError(f"missing generated rule count for {name}")
        files = {}
        for filename in specification["files"]:
            artifact = ROOT / filename
            if not artifact.is_file():
                raise RuntimeError(f"missing generated artifact: {filename}")
            data = artifact.read_bytes()
            files[filename] = {
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        rule_sets[name] = {
            "kind": specification["kind"],
            "rules": counts[name],
            "files": files,
        }
    manifest = {
        "schema": 1,
        "tools": {"mihomo": mihomo, "sing_box": singbox},
        "rule_sets": rule_sets,
    }
    (ROOT / ".github/rule-artifacts.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


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


def verify_srs(
    binary: Path,
    input_path: Path,
    expected_rules: list[dict[str, list[str]]],
    workspace: Path,
) -> None:
    actual_rules = decompile_srs(
        binary,
        input_path,
        workspace / f"{input_path.name}.verified.json",
    )
    normalize = lambda rules: [
        {
            key: sorted(values) if isinstance(values, list) else values
            for key, values in sorted(rule.items())
        }
        for rule in rules
    ]
    if normalize(actual_rules) != normalize(expected_rules):
        raise RuntimeError(f"{input_path.name}: generated SRS differs from its source")


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


def records_to_egern_yaml(records: list[tuple[str, str]]) -> str:
    domain_suffixes = [val for r_type, val in records if r_type in {"DOMAIN-SUFFIX", "HOST-SUFFIX"}]
    domains = [val for r_type, val in records if r_type in {"DOMAIN", "HOST"}]
    lines: list[str] = []
    if domain_suffixes:
        lines.append("domain_suffix_set:")
        lines.extend(f"  - {item}" for item in sorted(set(domain_suffixes)))
    if domains:
        lines.append("domain_set:")
        lines.extend(f"  - {item}" for item in sorted(set(domains)))
    return "\n".join(lines) + "\n"


def update_nodeseek(binary: Path, singbox: Path, workspace: Path) -> int:
    data, used_url, records = download_domain_mrs(
        binary,
        NODESEEK_SOURCES,
        workspace,
        "nodeseek-source",
        3,
    )
    entries = records_to_entries(records)
    yaml_text = records_to_egern_yaml(records)
    temporary_output = workspace / "Nodeseek.yaml"
    temporary_output.write_bytes(yaml_text.encode("utf-8"))
    mrs_output = workspace / "Nodeseek.mrs"
    mrs_output.write_bytes(data)
    verify_mrs(binary, mrs_output, "domain", records, workspace)
    srs_output = workspace / "Nodeseek.srs"
    expected_rules = [
        singbox_rule(
            domain=[entry for entry in entries if not entry.startswith("+.")],
            domain_suffix=[entry[2:] for entry in entries if entry.startswith("+.")],
        )
    ]
    compile_srs(
        singbox,
        expected_rules,
        srs_output,
    )
    verify_srs(singbox, srs_output, expected_rules, workspace)
    temporary_output.replace(ROOT / "Nodeseek.yaml")
    mrs_output.replace(ROOT / "Nodeseek.mrs")
    srs_output.replace(ROOT / "Nodeseek.srs")
    print(f"Nodeseek.yaml: {len(entries)} rules from {used_url}")
    print(f"Nodeseek.mrs: {len(entries)} rules from {used_url}")
    print(f"Nodeseek.srs: {len(entries)} rules from {used_url}")
    return len(entries)


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


def preserve_existing_webrtc(mihomo: Path, singbox: Path, workspace: Path, download_error: RuntimeError) -> int:
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
    return len(entries)


def update_webrtc(mihomo: Path, singbox: Path, workspace: Path) -> int:
    try:
        data, used_url, records = download_domain_mrs(
            mihomo,
            WEBRTC_SOURCES,
            workspace,
            "webrtc-source",
            20,
        )
    except RuntimeError as error:
        return preserve_existing_webrtc(mihomo, singbox, workspace, error)
    input_path = workspace / "Webrtc_domain_source.mrs"
    input_path.write_bytes(data)
    entries = records_to_entries(records)
    verify_mrs(mihomo, input_path, "domain", records, workspace)
    temporary_output = workspace / "Webrtc_domain.srs"
    expected_rules = [
        singbox_rule(
            domain=[entry for entry in entries if not entry.startswith("+.")],
            domain_suffix=[entry[2:] for entry in entries if entry.startswith("+.")],
        )
    ]
    compile_srs(
        singbox,
        expected_rules,
        temporary_output,
    )
    verify_srs(singbox, temporary_output, expected_rules, workspace)
    input_path.replace(ROOT / "Webrtc_domain.mrs")
    temporary_output.replace(ROOT / "Webrtc_domain.srs")
    print(f"Webrtc_domain.mrs: {len(entries)} rules from {used_url}")
    print(f"Webrtc_domain.srs: {len(entries)} rules from {used_url}")
    return len(entries)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mihomo-rule-update-") as temporary:
        workspace = Path(temporary)
        binary = mihomo_binary(workspace)
        singbox = singbox_binary(workspace)
        current_mihomo_version = mihomo_version(binary)
        current_singbox_version = singbox_version(singbox)
        print(f"Using {current_mihomo_version}")
        print(f"Using {current_singbox_version}")
        counts = {
            "NodeSeek": update_nodeseek(binary, singbox, workspace),
            "WebRTC": update_webrtc(binary, singbox, workspace),
        }
        official_telegram, _, official_telegram_url = telegram_official_networks()
        telegram_groups: dict[
            str, list[ipaddress.IPv4Network | ipaddress.IPv6Network]
        ] = {}
        print(
            f"Telegram official CIDR audit: {len(official_telegram)} dual-stack ranges; "
            f"{official_telegram_url}"
        )
        for source in SOURCES:
            _, used_url, records = download_rule_source(source)
            if source["output"].startswith("Telegram"):
                telegram_groups[source["output"]] = validate_telegram_records(
                    source["output"],
                    records,
                    official_telegram,
                )
            entries = records_to_entries(records)
            input_path = workspace / f"{source['output']}.txt"
            temporary_output = workspace / source["output"]
            input_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
            convert(binary, input_path, temporary_output, source["kind"])
            verify_mrs(binary, temporary_output, source["kind"], records, workspace)
            srs_output = workspace / source["srs_output"]
            srs_rules = records_to_srs_rules(records, source["kind"])
            compile_srs(singbox, srs_rules, srs_output)
            verify_srs(singbox, srs_output, srs_rules, workspace)
            temporary_output.replace(ROOT / source["output"])
            srs_output.replace(ROOT / source["srs_output"])
            print(f"{source['output']}: {len(entries)} rules from {used_url}")
            print(f"{source['srs_output']}: {len(records)} Loon records from {used_url}")
            counts[Path(source["output"]).stem] = len(records)
        singapore = telegram_groups["TelegramSG.mrs"]
        netherlands = telegram_groups["TelegramNL.mrs"]
        overlap = [
            (left, right)
            for left in singapore
            for right in netherlands
            if left.version == right.version and left.overlaps(right)
        ]
        if overlap:
            raise RuntimeError(f"Telegram SG/NL ranges overlap: {overlap}")
        write_artifact_manifest(
            counts,
            current_mihomo_version,
            current_singbox_version,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
