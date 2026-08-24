from __future__ import annotations

import gzip
import json
import re
import stat
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
USER_AGENT = "Ethan2258-mihomo-rule-updater/1.0"
MIHOMO_RELEASE_API = "https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"
SINGBOX_RELEASE_API = "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
MRS_MAGIC = bytes.fromhex("28b52ffd")
SRS_MAGIC = b"SRS\x02"
MIRROR_BRANCH = "Loon"
DOMAIN_SET_ENTRY = re.compile(
    r"^(?:\+\.)?(?:[A-Za-z0-9_*-]+\.)+[A-Za-z0-9_*-]+$"
)
NODESEEK_SOURCES = (
    "https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/nodeseek.mrs",
)
WEBRTC_SOURCES = (
    "https://raw.githubusercontent.com/milangree/rules/main/rules/mihomo/Webrtc/Webrtc_domain.mrs",
    "https://cdn.jsdelivr.net/gh/milangree/rules@main/rules/mihomo/Webrtc/Webrtc_domain.mrs",
)

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

    candidates = [
        asset
        for asset in release.get("assets", [])
        if asset.get("name", "").startswith("sing-box-")
        and asset.get("name", "").endswith("-linux-amd64.tar.gz")
    ]
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


def compile_srs(binary: Path, rules: list[dict[str, list[str]]], output_path: Path) -> None:
    source_path = output_path.with_suffix(".json")
    source_path.write_text(
        json.dumps({"version": 3, "rules": rules}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    command = [str(binary), "rule-set", "compile", str(source_path), "-o", str(output_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Sing-box SRS compilation failed: {detail}")
    if not output_path.is_file() or output_path.read_bytes()[:4] != SRS_MAGIC:
        raise RuntimeError(f"{output_path.name}: compiler did not produce a valid SRS file")


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


def update_webrtc(mihomo: Path, singbox: Path, workspace: Path) -> None:
    data, used_url = download_first(WEBRTC_SOURCES)
    if data[:4] != MRS_MAGIC:
        raise RuntimeError("Webrtc_domain.mrs: source has an invalid MRS/Zstandard header")
    input_path = workspace / "Webrtc_domain_source.mrs"
    output_path = workspace / "Webrtc_domain_source.txt"
    input_path.write_bytes(data)
    decode_mrs(mihomo, input_path, output_path, "domain")
    entries = list(dict.fromkeys(line.strip() for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()))
    if any(not DOMAIN_SET_ENTRY.fullmatch(entry) for entry in entries):
        raise ValueError("Webrtc_domain.mrs: source contains an invalid domain")
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
    temporary_output.replace(ROOT / "Webrtc_domain.srs")
    print(f"Webrtc_domain.srs: {len(entries)} rules from {used_url}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mihomo-rule-update-") as temporary:
        workspace = Path(temporary)
        binary = mihomo_binary(workspace)
        singbox = singbox_binary(workspace)
        update_nodeseek(binary, singbox, workspace)
        update_webrtc(binary, singbox, workspace)
        for source in SOURCES:
            data, used_url = download_source(source)
            records = parse_lsr_records(data, source["kind"])
            entries = parse_lsr(data, source["kind"])
            input_path = workspace / f"{source['output']}.txt"
            temporary_output = workspace / source["output"]
            input_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
            convert(binary, input_path, temporary_output, source["kind"])
            temporary_output.replace(ROOT / source["output"])
            srs_output = workspace / source["srs_output"]
            compile_srs(singbox, records_to_srs_rules(records, source["kind"]), srs_output)
            srs_output.replace(ROOT / source["srs_output"])
            print(f"{source['output']}: {len(entries)} rules from {used_url}")
            print(f"{source['srs_output']}: {len(records)} rules from {used_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
