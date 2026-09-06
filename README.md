# Ethan2258

Mihomo / Egern / sing-box 规则、Sub-Store 模板与图标。

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
- **sing-box**：使用 `type: remote`、`format: binary` 并在路由中引用。测速域名与 IP 分别引用，MRS/SRS 不可混用。

## Sub-Store 与图标

- [SubStore-sing-box-template.json](SubStore-sing-box-template.json)：个人 sing-box 配置模板。
- [SubStore-sing-box.js](SubStore-sing-box.js)：配套节点填充脚本，`url` 参数可替换默认个人订阅。
- 须有香港、台湾、新加坡、荷兰（`EU`）、澳门节点，缺失则停止输出。使用前检查核心兼容性、订阅地址、控制接口监听与密钥。
- NodeSeek 图标：[SVG](nodeseek.svg) · [PNG](nodeseek.png)。

## 自动更新与来源

[生成工作流](.github/workflows/update-mihomo-rules.yml)每 3 小时运行，支持手动触发并自动提交至 `main`。

- **国际测速**：合并可莉、MetaCubeX、V2Fly、Sukka、Ookla/LibreSpeed 目录、oneclickvirt、blackmatrix7 及审核后缀；保留多源覆盖。
- **其他规则**：NodeSeek 来自 MetaCubeX，Telegram SG/NL 来自可莉；WebRTC 及完整来源见[生成脚本](.github/scripts/update_lsr_rules.py)。

### 测速合并与压缩

- 排除已知大陆端点，保留港澳台及境外记录；不引入累积历史清单、全球 `+.ooklaserver.net` 或宽泛测速关键词。
- 域名去重与后缀合并须通过覆盖检查；IP 只采用上游明确网段。
- 可莉原站与镜像校验后择新，拒绝回退及同时间戳冲突；镜像不保证原站最新。[来源状态](.github/speedtest-source-state.json)记录时间与 SHA-256。
- MRS/SRS 使用同一规则集；测速 MRS 用 Zstandard 19、SRS 用 Zopfli 无损压缩，仅接受更小且解压一致的结果。

### SRS 格式与校验

SRS 跟随官方最新稳定版编译器与源格式，二进制版本由编译器选择，不强改版本号。

[校验工作流](.github/workflows/validate.yml)检查 YAML、引用、链接及文件头；生成时另查来源规模、规则覆盖和测速格式一致性。
