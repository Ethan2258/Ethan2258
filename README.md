# Ethan2258

Mihomo / Egern 规则文件与相关资源。

## 文件

- `Nodeseek.yaml`：由上游 MRS 自动转换的 NodeSeek 域名规则，适用于 Egern。
- `SpeedtestInternational.mrs`：国际 Speedtest 域名规则。
- `SpeedtestInternational_ipcidr.mrs`：国际 Speedtest IP 网段规则。
- `TelegramSG.mrs`：Telegram SG IP 网段规则。
- `TelegramNL.mrs`：Telegram NL IP 网段规则。
- `telegram_nl.yaml`、`telegram_sg.yaml`：Telegram IP/ASN YAML 规则。
- `Webrtc_domain.mrs`：WebRTC 域名规则文件。
- `nodeseek.svg`、`nodeseek.png`：NodeSeek 图标资源。
- `.github/`：校验脚本、转换脚本和 GitHub Actions 工作流。

## 规则链接

- [Nodeseek.yaml](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.yaml)
- [SpeedtestInternational.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.mrs)
- [SpeedtestInternational_ipcidr.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.mrs)
- [TelegramSG.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.mrs)
- [TelegramNL.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.mrs)
- [telegram_nl.yaml](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/telegram_nl.yaml)
- [telegram_sg.yaml](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/telegram_sg.yaml)
- [Webrtc_domain.mrs](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.mrs)

## 自动更新

GitHub Actions 每天北京时间 `10:17` 自动下载以下 Loon 规则，并转换为 Mihomo `.mrs` 文件后提交到 `main`：

- [SpeedtestInternational.lsr](https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr)
- [TelegramSG.lsr](https://rule.kelee.one/Loon/TelegramSG.lsr)
- [TelegramNL.lsr](https://rule.kelee.one/Loon/TelegramNL.lsr)

同时从 [MetaCubeX meta-rules-dat](https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs) 拉取 NodeSeek MRS，将其转换并同步到 `Nodeseek.yaml`。

Speedtest 源同时包含域名和 IP 网段，因此会拆成两个行为独立的 MRS 文件；源站暂时不可用时，任务会自动使用对应的公开镜像继续更新。

## 校验

每次推送到 `main` 分支或提交 Pull Request 时，GitHub Actions 会自动检查 YAML、规则引用、仓库链接和 MRS 文件头。
