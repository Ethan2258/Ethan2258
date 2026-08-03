<h1 align="center">Hi, I'm Ethan</h1>

<p align="center">Android 系统折腾、Magisk / LSPosed 与 Mihomo 网络配置</p>

<p align="center">
  <a href="https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml"><img alt="Validate repository" src="https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml/badge.svg"></a>
  <a href="https://github.com/Ethan2258/Ethan2258/actions/workflows/sync-file.yml"><img alt="Sync Mihomo rules" src="https://github.com/Ethan2258/Ethan2258/actions/workflows/sync-file.yml/badge.svg"></a>
</p>

## 关于我

- 关注 Android 系统行为、Magisk、LSPosed 与 Xposed 生态。
- 正在实践透明代理、IPv4 / IPv6、DNS 与 Mihomo 分流方案。
- 这个仓库既是我的 GitHub 个人主页，也是个人配置与规则文件的稳定分发地址。

## 配置概览

两份配置都启用了 IPv6、Fake-IP、域名嗅探、TCP 并发、策略选择与 Fake-IP 持久化和 Zashboard，并使用两个本地订阅提供器。主要差异如下：

| 平台 | 配置 | 本地订阅服务 | 直连 / 订阅 DNS | YouTube 分流 |
| --- | --- | --- | --- | --- |
| Android | [`config(Android).yaml`](./config%28Android%29.yaml) · [Raw](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/config%28Android%29.yaml) | `127.0.0.1:3000` | 本地 DNS `127.0.0.1:1451` | Android 进程名 |
| Windows | [`config(Windows).yaml`](./config%28Windows%29.yaml) · [Raw](https://raw.githubusercontent.com/Ethan2258/Ethan2258/main/config%28Windows%29.yaml) | `127.0.0.1:38324` | AliDNS / DNSPod DoH | YouTube 规则集 |

共同的基础端口与功能：

| 项目 | 当前值 |
| --- | --- |
| Mixed / Redir / TProxy | `7890` / `9797` / `9898` |
| DNS 监听 | `0.0.0.0:1053` |
| 外部控制器 | `127.0.0.1:9090` |
| DNS 模式 | Fake-IP，IPv4 `198.18.0.1/16`，IPv6 `fc00::/18` |
| 订阅提供器 | `🌋`、`☄️`，每 30 分钟更新并定期健康检查 |
| 地区策略组 | Hong Kong、Taiwan、Singapore、Europe |
| 服务策略组 | AI、Speedtest、Telegram、Discord、NodeSeek、GitHub、YouTube、Google |

## 分流顺序

规则按照从上到下的顺序匹配，当前逻辑可以概括为：

1. 劫持 `53` 端口的 DNS 请求。
2. 私有域名和私有 IP 直连。
3. 广告、广告 IP 与 WebRTC 规则拒绝连接。
4. Google FCM 直连；AI、Discord、GitHub、NodeSeek、测速、YouTube、Google 和 Telegram 进入对应策略组。
5. 中国大陆域名与 IP 直连。
6. 其余流量交给 `Proxy`。

Android 使用 `PROCESS-NAME,com.google.android.youtube` 识别 YouTube；Windows 使用独立的 YouTube MRS 规则集。Telegram DC4 与 DC5 分别使用本仓库的荷兰、新加坡 IP/ASN 规则。

## 文件说明

根目录路径有意保持稳定，避免破坏已有的 GitHub Raw 和 jsDelivr 地址。

| 文件 | 作用 | 是否被当前配置直接引用 | 更新方式 |
| --- | --- | --- | --- |
| [`config(Android).yaml`](./config%28Android%29.yaml) | Android Mihomo 模板 | 主配置 | 手动维护 |
| [`config(Windows).yaml`](./config%28Windows%29.yaml) | Windows Mihomo 模板 | 主配置 | 手动维护 |
| [`Webrtc_domain.mrs`](./Webrtc_domain.mrs) | WebRTC 域名拦截规则 | 是 | 每日自动同步 |
| [`telegram_nl.yaml`](./telegram_nl.yaml) | Telegram DC4 荷兰 IP / ASN | 是 | 手动维护 |
| [`telegram_sg.yaml`](./telegram_sg.yaml) | Telegram DC5 新加坡 IP / ASN | 是 | 手动维护 |
| [`nodeseek.svg`](./nodeseek.svg) | NodeSeek 策略组图标 | 是 | 手动维护 |
| [`ai_domain.mrs`](./ai_domain.mrs) | AI 域名规则镜像 | 否，供独立使用 | 每日自动同步 |
| [`ai_ipcidr.mrs`](./ai_ipcidr.mrs) | AI IP-CIDR 规则镜像 | 否，供独立使用 | 每日自动同步 |
| [`Nodeseek.yaml`](./Nodeseek.yaml) | NodeSeek 备用域名列表 | 否，当前使用上游 MRS | 手动维护 |
| [`nodeseek.png`](./nodeseek.png) | NodeSeek PNG 备用图标 | 否 | 手动维护 |

> 当前配置中的 AI 策略使用 `xndeye/rule-merger` 的 AI MRS；NodeSeek 策略使用 `MetaCubeX/meta-rules-dat` 的 NodeSeek MRS。仓库内的 `ai_*.mrs` 和 `Nodeseek.yaml` 是独立镜像或备用文件，不应误认为当前模板的直接依赖。

## 使用前检查

这些是个人模板，不是导入后即可通用的成品配置。至少需要检查以下内容：

1. 将两个 `proxy-providers` 的本地 URL 替换为自己的 Sub-Store 或订阅转换地址。
2. 确认节点名称能够匹配配置里的过滤条件，例如 `0x`、地区旗帜、`seed`、`🇳🇱` 和 `🇩🇪`。
3. Android 用户需要确保 `127.0.0.1:1451` 上确实有可用的本地 DNS；否则应替换 `direct-nameserver` 和 `proxy-server-nameserver`。
4. 检查外部规则提供器、DNS 服务和 Zashboard 下载地址在当前网络中可访问。
5. 不要把私人订阅链接、Token 或控制器密钥提交到公开仓库。
6. 使用近期 Mihomo 版本测试配置语法、DNS 解析和常用服务后，再设为默认配置。

## 自动化维护

- [`Sync Mihomo rules`](./.github/workflows/sync-file.yml) 每天北京时间 `10:00` 从 [`milangree/rules`](https://github.com/milangree/rules) 同步 AI 域名、AI IP-CIDR 和 WebRTC 三个 MRS 文件，也支持手动运行。
- 同步流程带连接超时、失败重试、并发保护和 MRS/Zstandard 文件头检查，下载异常时不会覆盖现有规则。
- [`Validate repository`](./.github/workflows/validate.yml) 在 push 和 pull request 时检查 YAML 语法与重复键、Mihomo 规则引用、本仓库 jsDelivr 链接以及 MRS 文件头。

## 上游项目

配置与规则依赖或参考了以下开源项目：

- [`MetaCubeX/mihomo`](https://github.com/MetaCubeX/mihomo)
- [`MetaCubeX/meta-rules-dat`](https://github.com/MetaCubeX/meta-rules-dat)
- [`DustinWin/ruleset_geodata`](https://github.com/DustinWin/ruleset_geodata)
- [`xndeye/rule-merger`](https://github.com/xndeye/rule-merger)
- [`217heidai/adblockfilters`](https://github.com/217heidai/adblockfilters)
- [`Koolson/Qure`](https://github.com/Koolson/Qure)
- [`musiyun124/zashboard`](https://github.com/musiyun124/zashboard)

使用或分发规则文件前，请同时遵守相应上游项目的许可与更新策略。
