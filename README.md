# Ethan2258

Mihomo / Egern 规则文件与相关资源。

## 文件

- `Nodeseek.yaml`：由上游 MRS 自动转换的 NodeSeek 域名规则，适用于 Egern。
- `Nodeseek.srs`：由同一上游直接编译的 Sing-box 域名规则。
- `SpeedtestInternational.mrs`：国际 Speedtest 域名规则。
- `SpeedtestInternational.srs`：国际 Speedtest Sing-box 域名规则。
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
- [telegram_nl.yaml](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/telegram_nl.yaml)
- [telegram_sg.yaml](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/telegram_sg.yaml)
- [Webrtc_domain.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.mrs)
- [Webrtc_domain.srs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.srs)

## 自动更新

GitHub Actions 每天北京时间 `10:17` 自动下载以下 Loon 规则，并转换为 Mihomo `.mrs` 文件后提交到 `main`：

- [SpeedtestInternational.lsr](https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr)
- [TelegramSG.lsr](https://rule.kelee.one/Loon/TelegramSG.lsr)
- [TelegramNL.lsr](https://rule.kelee.one/Loon/TelegramNL.lsr)

同时从 [MetaCubeX meta-rules-dat](https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs) 拉取 NodeSeek MRS，转换并同步到 `Nodeseek.yaml` 和 `Nodeseek.srs`。

每次同步也会从各自源文件直接编译 Sing-box `.srs`，包括 Speedtest、Telegram 和 WebRTC。`.srs` 是 Sing-box 原生二进制 rule-set，直接在 Sing-box 中使用，不要把 `.mrs` 改名为 `.srs`。

Speedtest 源同时包含域名和 IP 网段，因此会拆成两个行为独立的 MRS 文件；源站暂时不可用时，任务会自动使用对应的公开镜像继续更新。

Speedtest 域名文件使用 `behavior: domain` 和 `format: mrs`；IP 网段文件使用 `behavior: ipcidr` 和 `format: mrs`。

## 校验

每次推送到 `main` 分支或提交 Pull Request 时，GitHub Actions 会自动检查 YAML、规则引用、仓库链接和 MRS 文件头。
