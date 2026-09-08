# Ethan2258 Rules

[![Update generated rules](https://github.com/Ethan2258/Ethan2258/actions/workflows/update-mihomo-rules.yml/badge.svg)](https://github.com/Ethan2258/Ethan2258/actions/workflows/update-mihomo-rules.yml)
[![Validate repository](https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml/badge.svg)](https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml)

为 Mihomo、sing-box 和 Egern 自动维护的精简规则集。

## 规则下载

| 规则集 | 内容 | 类型 | Mihomo | sing-box | Egern |
| --- | --- | --- | --- | --- | --- |
| NodeSeek | NodeSeek 相关域名 | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.srs) | [YAML](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.yaml) |
| SpeedtestInternational | 境外测速服务 | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.srs) | - |
| SpeedtestInternational IP | 境外测速服务器网段 | IP | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.srs) | - |
| Telegram SG | Telegram 新加坡网段 | IP | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.srs) | - |
| Telegram NL | Telegram 荷兰网段 | IP | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.srs) | - |
| WebRTC | WebRTC 相关域名 | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.srs) | - |

测速规则应同时引用域名集和 IP 集；MRS 与 SRS 不能混用。当前规则数、文件大小和 SHA-256 见[产物清单](.github/rule-artifacts.json)。

## Mihomo

```yaml
rule-providers:
  speedtest-domain:
    type: http
    behavior: domain
    format: mrs
    url: https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.mrs
    path: ./ruleset/SpeedtestInternational.mrs
    interval: 10800

  speedtest-ip:
    type: http
    behavior: ipcidr
    format: mrs
    url: https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.mrs
    path: ./ruleset/SpeedtestInternational_ipcidr.mrs
    interval: 10800

rules:
  - RULE-SET,speedtest-domain,PROXY
  - RULE-SET,speedtest-ip,PROXY,no-resolve
```

域名 MRS 使用 `behavior: domain`，IP MRS 使用 `behavior: ipcidr`。

## sing-box

```json
{
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "speedtest-domain",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational.srs",
        "download_detour": "direct",
        "update_interval": "3h"
      },
      {
        "type": "remote",
        "tag": "speedtest-ip",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/SpeedtestInternational_ipcidr.srs",
        "download_detour": "direct",
        "update_interval": "3h"
      }
    ]
  }
}
```

在路由规则中引用对应 `tag` 并选择目标出站即可。

## 更新与质量

- 每 3 小时检查一次上游，也支持[手动运行](https://github.com/Ethan2258/Ethan2258/actions/workflows/update-mihomo-rules.yml)。
- NodeSeek 跟随 MetaCubeX；国际测速合并多个有效来源；Telegram SG/NL 额外对照 Telegram 官方双栈 CIDR；WebRTC 使用通过解码与规模检查的来源。
- 域名和 CIDR 会先规范化、去重并检查语义覆盖；非法记录、异常缩减和来源冲突会中止更新。
- MRS/SRS 生成后会反向解码核对；测速产物仅在内容完全一致且体积更小时进行无损重压。
- [验证工作流](https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml)检查 YAML、压缩流、产物清单、文件大小和 SHA-256。

## 图标

NodeSeek：[SVG](nodeseek.svg) · [PNG](nodeseek.png)
