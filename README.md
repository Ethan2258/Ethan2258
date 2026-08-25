# Ethan2258

Mihomo / Egern 规则文件与相关资源。

## 文件

- `Nodeseek.yaml`：由上游 MRS 自动转换的 NodeSeek 域名规则，适用于 Egern。
- `Nodeseek.srs`：由同一上游直接编译的 Sing-box 域名规则。
- `SpeedtestInternational.mrs`：由 Kelee 原始 Loon 规则补充国际测速域名后转换的规则。
- `SpeedtestInternational.srs`：由同一份合并规则转换的 Sing-box 域名规则。
- `SpeedtestInternational_ipcidr.mrs`：国际 Speedtest IP 网段规则。
- `SpeedtestInternational_ipcidr.srs`：国际 Speedtest Sing-box IP 网段规则。
- `TelegramSG.mrs`：Telegram SG IP 网段规则。
- `TelegramSG.srs`：Telegram SG Sing-box IP 网段规则。
- `TelegramNL.mrs`：Telegram NL IP 网段规则。
- `TelegramNL.srs`：Telegram NL Sing-box IP 网段规则。
- `Webrtc_domain.mrs`：WebRTC 域名规则文件。
- `Webrtc_domain.srs`：由 WebRTC 上游直接编译的 Sing-box 域名规则。
- `nodeseek.svg`、`nodeseek.png`：NodeSeek 图标资源。
- `.github/`：校验脚本、转换脚本和 GitHub Actions 工作流。

## 规则链接

- [Nodeseek.yaml](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.yaml)
- [Nodeseek.srs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.srs)
- [SpeedtestInternational.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.mrs)
- [SpeedtestInternational.srs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.srs)
- [SpeedtestInternational_ipcidr.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.mrs)
- [SpeedtestInternational_ipcidr.srs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.srs)
- [TelegramSG.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.mrs)
- [TelegramSG.srs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.srs)
- [TelegramNL.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.mrs)
- [TelegramNL.srs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.srs)
- [Webrtc_domain.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.mrs)
- [Webrtc_domain.srs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.srs)

## 自动更新

GitHub Actions 每 3 小时自动下载以下 Loon 规则，按原始规则类型转换并提交生成文件到 `main`：

- [SpeedtestInternational.lsr](https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr)
- [MetaCubeX speedtest.mrs](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/speedtest.mrs)（仅补充 Kelee 缺少的国际测速域名）
- [TelegramSG.lsr](https://rule.kelee.one/Loon/TelegramSG.lsr)
- [TelegramNL.lsr](https://rule.kelee.one/Loon/TelegramNL.lsr)

同时从 [MetaCubeX meta-rules-dat](https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs) 拉取 NodeSeek MRS，转换并同步到 `Nodeseek.yaml` 和 `Nodeseek.srs`。

每次同步都会从 Sing-box 官方 `releases/latest` API 下载最新版本的编译器，再从各自源文件直接编译 Sing-box `.srs`，包括 Speedtest、Telegram 和 WebRTC。`.srs` 是 Sing-box 原生二进制 rule-set，直接在 Sing-box 中使用，不要把 `.mrs` 改名为 `.srs`。任务会打印实际使用的 Sing-box 版本，并校验生成文件的官方 `SRS` 文件头。

Sing-box 使用 `.srs` 时，远程规则集应指定 `format: binary`，例如：

```json
{
  "route": {
    "rule_set": [
      {
        "tag": "SpeedtestInternational",
        "type": "remote",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.srs",
        "download_detour": "direct",
        "update_interval": "1d"
      }
    ]
  }
}
```

`SpeedtestInternational_ipcidr.srs`、`TelegramSG.srs` 和 `TelegramNL.srs` 是 IP rule-set；`Nodeseek.srs`、`SpeedtestInternational.srs` 和 `Webrtc_domain.srs` 是域名 rule-set。Speedtest 域名和 IP 规则需要分别引用。

Speedtest Loon 源同时包含域名和 IP 网段，因此会拆成两个行为独立的规则文件。域名 `.mrs` 与 `.srs` 均由 Kelee 原始规则、MetaCubeX 官方测速域名差集，以及 `+.fast.com`、`+.fiber.google.com` 生成；大陆测速域名会被排除。IP `.mrs` 与 `.srs` 仍只来自 Kelee 的 IP 规则。所有来源在每次更新时重新下载、去重并转换，保证两种格式的匹配语义一致。Kelee 源站暂时不可用时，任务会自动使用对应的公开镜像继续更新。

Speedtest 域名文件使用 `behavior: domain` 和 `format: mrs`；IP 网段文件使用 `behavior: ipcidr` 和 `format: mrs`。

## 校验

每次推送到 `main` 分支或提交 Pull Request 时，GitHub Actions 会自动检查 YAML、规则引用、仓库链接和 MRS 文件头。
