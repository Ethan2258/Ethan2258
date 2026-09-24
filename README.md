# Ethan2258 Rules

[![Update generated rules](https://github.com/Ethan2258/Ethan2258/actions/workflows/update-mihomo-rules.yml/badge.svg)](https://github.com/Ethan2258/Ethan2258/actions/workflows/update-mihomo-rules.yml)
[![Validate repository](https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml/badge.svg)](https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml)

为 Mihomo、sing-box 和 Egern 自动维护的精简规则集。

## 规则下载

| 规则集 | 内容 | 类型 | Mihomo | sing-box | Egern |
| --- | --- | --- | --- | --- | --- |
| NodeSeek | NodeSeek 相关域名 | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.srs) | [YAML](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.yaml) |
| Telegram SG | Telegram 新加坡网段 | IP | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.srs) | - |
| Telegram NL | Telegram 荷兰网段 | IP | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramNL.srs) | - |
| WebRTC | WebRTC 相关域名 | 域名 | [MRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.mrs) | [SRS](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Webrtc_domain.srs) | - |

MRS 与 SRS 不能混用。当前规则数、文件大小和 SHA-256 见[产物清单](.github/rule-artifacts.json)。

## Mihomo

```yaml
rule-providers:
  nodeseek:
    type: http
    behavior: domain
    format: mrs
    url: https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.mrs
    path: ./ruleset/Nodeseek.mrs
    interval: 10800

  telegram-sg:
    type: http
    behavior: ipcidr
    format: mrs
    url: https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.mrs
    path: ./ruleset/TelegramSG.mrs
    interval: 10800

rules:
  - RULE-SET,nodeseek,PROXY
  - RULE-SET,telegram-sg,PROXY,no-resolve
```

域名 MRS 使用 `behavior: domain`，IP MRS 使用 `behavior: ipcidr`。

## sing-box

```json
{
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "nodeseek",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.srs",
        "download_detour": "direct",
        "update_interval": "3h"
      },
      {
        "type": "remote",
        "tag": "telegram-sg",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/TelegramSG.srs",
        "download_detour": "direct",
        "update_interval": "3h"
      }
    ]
  }
}
```

在路由规则中引用对应 `tag` 并选择目标出站即可。

## Egern

```yaml
rules:
  - rule_set:
      match: https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/Nodeseek.yaml
      policy: DIRECT
      update_interval: 10800
```

在规则列表或配置中引用对应 `rule_set` 并指定目标策略（如 `DIRECT` 或 `PROXY`）即可。

## 更新与质量

- 每 3 小时检查一次上游，也支持[手动运行](https://github.com/Ethan2258/Ethan2258/actions/workflows/update-mihomo-rules.yml)。
- NodeSeek 跟随 MetaCubeX；Telegram SG/NL 额外对照 Telegram 官方双栈 CIDR；WebRTC 使用通过解码与规模检查的来源。
- 域名和 CIDR 会先规范化、去重；非法记录、异常缩减和来源冲突会中止更新。
- MRS/SRS 生成后会反向解码核对。
- [验证工作流](https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml)检查 YAML、压缩流、产物清单、文件大小和 SHA-256。

## 图标

NodeSeek：[SVG](nodeseek.svg) · [PNG](nodeseek.png)
