from __future__ import annotations

import gzip
import json
import re
import stat
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
USER_AGENT = "Ethan2258-mihomo-rule-updater/1.0"
MIHOMO_RELEASE_API = "https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"
MRS_MAGIC = bytes.fromhex("28b52ffd")
MIRROR_BRANCH = "Loon"
DOMAIN_SET_ENTRY = re.compile(
    r"^(?:\+\.)?(?:[A-Za-z0-9_*-]+\.)+[A-Za-z0-9_*-]+$"
)
NODESEEK_SOURCES = (
    "https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs",
    "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/nodeseek.mrs",
)

SOURCES = (
    {
        "output": "SpeedtestInternational.mrs",
        "kind": "domain",
        "url": "https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/Lsr/SpeedtestInternational.lsr",
    },
    {
        "output": "SpeedtestInternational_ipcidr.mrs",
        "kind": "ipcidr",
        "url": "https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/Lsr/SpeedtestInternational.lsr",
    },
    {
        "output": "TelegramSG.mrs",
        "kind": "ipcidr",
        "url": "https://rule.kelee.one/Loon/TelegramSG.lsr",
        "fallback": f"https://raw.githubusercontent.com/mihoyo-typ/KeleeOne/{MIRROR_BRANCH}/Rule/TelegramSG.lsr",
    },
    {
        "output": "TelegramNL.mrs",
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


def parse_lsr(data: bytes, kind: str) -> list[str]:
    text = data.decode("utf-8-sig")
    entries: list[str] = []
    seen: set[str] = set()
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
        if value not in seen:
            entries.append(value)
            seen.add(value)

    if not entries:
        raise ValueError(f"source contains no {kind} rules")
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


def update_nodeseek(binary: Path, workspace: Path) -> None:
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
    print(f"Nodeseek.yaml: {len(entries)} rules from {used_url}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="mihomo-rule-update-") as temporary:
        workspace = Path(temporary)
        binary = mihomo_binary(workspace)
        update_nodeseek(binary, workspace)
        for source in SOURCES:
            data, used_url = download_source(source)
            entries = parse_lsr(data, source["kind"])
            input_path = workspace / f"{source['output']}.txt"
            temporary_output = workspace / source["output"]
            input_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
            convert(binary, input_path, temporary_output, source["kind"])
            temporary_output.replace(ROOT / source["output"])
            print(f"{source['output']}: {len(entries)} rules from {used_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
