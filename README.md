# Ethan2258

个人维护的 Mihomo / Egern / sing-box 分流规则、Sub-Store 模板与图标资源。

## 规则下载

| 规则 | 类型 | Mihomo | sing-box | Egern |
| --- | --- | --- | --- | --- |
| NodeSeek | 域名 | — | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.srs) | [YAML](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.yaml) |
| 国际测速 | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.srs) | — |
| 国际测速 | IP 网段 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.srs) | — |
| Telegram SG | IP 网段 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.srs) | — |
| Telegram NL | IP 网段 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.srs) | — |
| WebRTC | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.srs) | — |

- **Mihomo**：设置 `format: mrs`；域名规则用 `behavior: domain`，IP 规则用 `behavior: ipcidr`。
- **sing-box**：远程规则集使用 `type: remote`、`format: binary`，并在路由规则中引用对应标签。测速域名与 IP 文件需分别引用，MRS 不能改名当作 SRS。

## Sub-Store 与图标

- [SubStore-sing-box-template.json](SubStore-sing-box-template.json)：个人 sing-box 配置模板。
- [SubStore-sing-box.js](SubStore-sing-box.js)：配合模板使用的 Sub-Store 脚本，拉取 sing-box 订阅并填充节点及策略组；可通过 `url` 参数覆盖默认个人订阅地址。
- 脚本要求香港、台湾、新加坡、荷兰（`EU` 组）、澳门均有匹配节点，缺少任一地区会停止输出。使用前检查核心兼容性、订阅地址、控制接口监听与密钥。
- NodeSeek 图标：[SVG](nodeseek.svg) · [PNG](nodeseek.png)。

## 自动更新与来源

[生成工作流](.github/workflows/update-mihomo-rules.yml)每 3 小时运行，也可手动触发；生成文件自动提交至 `main`。

- **国际测速**：合并可莉、MetaCubeX、V2Fly、Sukka 静态规则及实时 Ookla 目录、LibreSpeed 官方及镜像、oneclickvirt、blackmatrix7 与人工复核的平台后缀。可莉只是其中一个上游，更新不会替换整套多源规则。
- **其他规则**：NodeSeek 来自 MetaCubeX；Telegram SG/NL 来自可莉；WebRTC 按脚本配置的上游及回退源同步。完整来源见[生成脚本](.github/scripts/update_lsr_rules.py)。

### 测速合并与压缩

- 按地区标签、已知大陆域名和 `.cn` 排除大陆测速端点，保留港澳台及其他境外记录；不引入 Sukka 累积历史清单、全球 `+.ooklaserver.net` 或宽泛的 `DOMAIN-KEYWORD,speedtest`。
- 去重并合并已覆盖的域名规则，仅在审核范围内提升测速专用子域后缀；检查原有覆盖不丢失。IP 仅采用上游明确网段，不解析域名凑 IP。
- 可莉原站与镜像按时间、条数和格式校验后择新；镜像可用不等于原站已确认最新。[来源状态](.github/speedtest-source-state.json)记录时间和 SHA-256，拒绝版本倒退及同时间戳内容冲突。
- MRS/SRS 由同一最终集合生成并校验一致性；测速 MRS 使用 Zstandard level 19，SRS 使用 Zopfli 无损压缩，仅在更小且解压字节一致时采用。

### SRS 格式与校验

SRS 使用官方最新稳定版 sing-box 编译，并自动探测最新源格式；二进制版本由官方编译器按规则内容选择，不手改文件头，也不添加无关字段强制升版。源格式版本与二进制版本不同不代表规则过期。

[校验工作流](.github/workflows/validate.yml)在推送、Pull Request 或手动触发时检查 YAML、配置规则引用、仓库链接及 MRS/SRS 文件头；生成阶段另有来源规模、规则覆盖和测速格式一致性检查。
