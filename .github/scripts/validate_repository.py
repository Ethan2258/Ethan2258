from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILES = tuple(sorted(ROOT.glob("*.yaml")))
MRS_MAGIC = bytes.fromhex("28b52ffd")
SRS_MAGIC = b"SRS\x02"
REPOSITORY_URL = re.compile(
    r"https://(?:cdn|fastly|gcore)\.jsdelivr\.net/gh/Ethan2258/Ethan2258@main/"
    r"(?P<path>[^\"'\s]+)",
    re.IGNORECASE,
)
RULE_SET_REFERENCE = re.compile(r"RULE-SET,([^,)]+)")


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    keys: set[Any] = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        if key in keys:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        keys.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping
)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        with path.open(encoding="utf-8") as stream:
            return yaml.load(stream, Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError) as error:
        errors.append(f"{relative(path)}: {error}")
        return None


def validate_rule_references(path: Path, config: Any, errors: list[str]) -> None:
    if not isinstance(config, dict):
        errors.append(f"{relative(path)}: expected a top-level mapping")
        return

    providers = set(config.get("rule-providers", {}))
    references: set[str] = set()

    for rule in config.get("rules", []):
        if isinstance(rule, str):
            references.update(RULE_SET_REFERENCE.findall(rule))

    dns = config.get("dns", {})
    for rule in dns.get("fake-ip-filter", []):
        if isinstance(rule, str):
            references.update(RULE_SET_REFERENCE.findall(rule))

    for policy in dns.get("nameserver-policy", {}):
        if isinstance(policy, str) and policy.startswith("rule-set:"):
            references.update(name.strip() for name in policy[9:].split(","))

    missing = sorted(references - providers)
    if missing:
        errors.append(
            f"{relative(path)}: undefined rule providers: {', '.join(missing)}"
        )


def validate_repository_urls(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for match in REPOSITORY_URL.finditer(text):
        target = ROOT / match.group("path")
        if not target.is_file():
            errors.append(
                f"{relative(path)}: repository URL points to missing file "
                f"{match.group('path')}"
            )


def validate_domain_set(path: Path, config: Any, errors: list[str]) -> None:
    if not isinstance(config, dict) or set(config) != {"payload"}:
        errors.append(f"{relative(path)}: expected only a top-level payload key")
        return

    payload = config["payload"]
    if not isinstance(payload, list) or not payload:
        errors.append(f"{relative(path)}: payload must be a non-empty list")
        return
    invalid_entries = [
        entry for entry in payload if not isinstance(entry, str) or not entry
    ]
    if invalid_entries:
        errors.append(f"{relative(path)}: payload entries must be non-empty strings")
    elif len(payload) != len(set(payload)):
        errors.append(f"{relative(path)}: payload contains duplicate entries")


def validate_mrs_files(errors: list[str]) -> None:
    for path in sorted(ROOT.glob("*.mrs")):
        if path.stat().st_size <= len(MRS_MAGIC):
            errors.append(f"{relative(path)}: file is empty or truncated")
            continue
        if path.read_bytes()[:4] != MRS_MAGIC:
            errors.append(f"{relative(path)}: invalid MRS/Zstandard header")


def validate_srs_files(errors: list[str]) -> None:
    for path in sorted(ROOT.glob("*.srs")):
        if path.stat().st_size <= len(SRS_MAGIC):
            errors.append(f"{relative(path)}: file is empty or truncated")
            continue
        if path.read_bytes()[:4] != SRS_MAGIC:
            errors.append(f"{relative(path)}: invalid Sing-box SRS header")


def main() -> int:
    errors: list[str] = []
    yaml_files = sorted(ROOT.glob("*.yaml")) + sorted(
        (ROOT / ".github" / "workflows").glob("*.yml")
    )

    loaded = {path: load_yaml(path, errors) for path in yaml_files}
    for path in CONFIG_FILES:
        config = loaded.get(path)
        if path.name == "Nodeseek.yaml":
            validate_domain_set(path, config, errors)
        if isinstance(config, dict) and any(
            key in config for key in ("rule-providers", "rules", "dns")
        ):
            validate_rule_references(path, config, errors)
        validate_repository_urls(path, errors)
    validate_mrs_files(errors)
    validate_srs_files(errors)

    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(yaml_files)} YAML files, "
        f"{len(CONFIG_FILES)} Mihomo configs, and "
        f"{len(list(ROOT.glob('*.mrs')))} MRS files, and "
        f"{len(list(ROOT.glob('*.srs')))} SRS files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
