# Ethan2258

Mihomo / Egern / sing-box 规则与图标。

## 规则下载

| 规则 | 类型 | Mihomo | sing-box | Egern |
| --- | --- | --- | --- | --- |
| NodeSeek | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.srs) | [YAML](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.yaml) |
| 国际测速 | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.srs) | — |
| 国际测速 | IP 网段 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.srs) | — |
| Telegram SG | IP 网段 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.srs) | — |
| Telegram NL | IP 网段 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.srs) | — |
| WebRTC | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.srs) | — |

- **Mihomo**：`format: mrs`；域名用 `behavior: domain`，IP 用 `behavior: ipcidr`。
- **sing-box**：远程规则设为 `format: binary`；测速域名与 IP 分别引用。

## 图标

NodeSeek：[SVG](nodeseek.svg) · [PNG](nodeseek.png)。

## 更新与校验

[生成工作流](.github/workflows/update-mihomo-rules.yml)每 3 小时运行，支持手动触发并自动提交至 `main`。

- **国际测速**：合并可莉、MetaCubeX、V2Fly、Sukka、Ookla/LibreSpeed、oneclickvirt、blackmatrix7 等来源；排除已知大陆端点和无效 `DOMAIN,http`，去重后做覆盖检查。
- **其他规则**：NodeSeek 跟随 MetaCubeX；WebRTC 使用可解码且规模正常的镜像；Telegram SG/NL 还须属于 Telegram 官方双栈 CIDR 且互不重叠。
- **格式**：MRS/SRS 由最新稳定版 Mihomo 与 sing-box 生成并反向解码核对；测速文件仅在解压内容一致且体积更小时无损重压。
- **完整性**：[产物清单](.github/rule-artifacts.json)记录规则数、编译器、大小与 SHA-256；[校验工作流](.github/workflows/validate.yml)检查完整压缩流、全部产物及仓库引用。
