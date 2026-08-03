<h1 align="center">Hi, I'm Ethan</h1>

<p align="center">Android 系统折腾、Magisk / LSPosed 与 Mihomo 网络配置</p>

<p align="center">
  <a href="https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml"><img alt="Validate repository" src="https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml/badge.svg"></a>
  <a href="https://github.com/Ethan2258/Ethan2258/actions/workflows/sync-file.yml"><img alt="Sync Mihomo rules" src="https://github.com/Ethan2258/Ethan2258/actions/workflows/sync-file.yml/badge.svg"></a>
</p>

## 关于我

- 关注 Android、Magisk、LSPosed、透明代理与 IPv4 / IPv6。
- 这个仓库也是我的 Mihomo 配置与规则文件分发地址。

## Mihomo 配置

两份配置均启用 IPv6、Fake-IP、域名嗅探、TCP 并发和 Zashboard，包含 AI、Telegram、GitHub、Google、YouTube 等服务策略组，以及香港、台湾、新加坡和欧洲地区组。

| 平台 | 配置 | 本地订阅服务 | 主要差异 |
| --- | --- | --- | --- |
| Android | [`查看`](./config%28Android%29.yaml) · [`Raw`](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/config%28Android%29.yaml) | `127.0.0.1:3000` | 使用本地 DNS `127.0.0.1:1451`，按进程分流 YouTube |
| Windows | [`查看`](./config%28Windows%29.yaml) · [`Raw`](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/config%28Windows%29.yaml) | `127.0.0.1:38324` | 使用 AliDNS / DNSPod DoH，按规则集分流 YouTube |

分流顺序大致为：私有网络直连，广告与 WebRTC 拒绝，常用服务进入各自策略组，中国大陆流量直连，其余流量交给 `Proxy`。

## 仓库文件

根目录路径保持稳定，避免破坏已有的 Raw 和 jsDelivr 链接。

| 文件 | 用途 | 当前配置直接引用 |
| --- | --- | --- |
| [`config(Android).yaml`](./config%28Android%29.yaml) / [`config(Windows).yaml`](./config%28Windows%29.yaml) | Android / Windows 主配置 | 是 |
| [`Webrtc_domain.mrs`](./Webrtc_domain.mrs) | WebRTC 域名拦截规则 | 是 |
| [`telegram_nl.yaml`](./telegram_nl.yaml) / [`telegram_sg.yaml`](./telegram_sg.yaml) | Telegram DC4 / DC5 IP 与 ASN | 是 |
| [`nodeseek.svg`](./nodeseek.svg) | NodeSeek 策略组图标 | 是 |
| [`ai_domain.mrs`](./ai_domain.mrs) / [`ai_ipcidr.mrs`](./ai_ipcidr.mrs) | AI 规则镜像，供独立使用 | 否 |
| [`Nodeseek.yaml`](./Nodeseek.yaml) / [`nodeseek.png`](./nodeseek.png) | NodeSeek 备用规则与图标 | 否 |

> 当前配置的 AI 与 NodeSeek 规则来自外部 MRS；仓库内的 `ai_*.mrs` 和 `Nodeseek.yaml` 是独立镜像或备用文件。

## 使用提醒

1. 把两个 `proxy-providers` 的本地 URL 换成自己的 Sub-Store 或订阅地址。
2. 确认节点名称能匹配配置中的地区旗帜、`0x`、`seed` 等过滤条件。
3. Android 用户需确保 `127.0.0.1:1451` 有可用 DNS，或自行替换相关设置。
4. 不要向公开仓库提交私人订阅、Token 或控制器密钥；正式使用前请先用近期 Mihomo 版本测试。

## 自动维护

- [`Sync Mihomo rules`](./.github/workflows/sync-file.yml) 每天北京时间 `10:00` 从 [`milangree/rules`](https://github.com/milangree/rules) 同步三个 MRS 文件，并检查下载结果。
- [`Validate repository`](./.github/workflows/validate.yml) 检查 YAML、规则引用、仓库链接与 MRS 文件头。

配置还使用了 [`MetaCubeX/meta-rules-dat`](https://github.com/MetaCubeX/meta-rules-dat)、[`DustinWin/ruleset_geodata`](https://github.com/DustinWin/ruleset_geodata)、[`xndeye/rule-merger`](https://github.com/xndeye/rule-merger) 等上游规则。
