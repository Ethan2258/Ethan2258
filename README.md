# Ethan2258

Mihomo / Egern 规则文件与相关资源。

## 文件

- `Nodeseek.yaml`：由上游 MRS 自动转换的 NodeSeek 域名规则，适用于 Egern。
- `Nodeseek.srs`：由同一上游直接编译的 Sing-box 域名规则。
- `SpeedtestInternational.mrs`：多上游交叉合并并精简的国际测速域名规则。
- `SpeedtestInternational.srs`：由同一份最终规则转换的 Sing-box 域名规则。
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

GitHub Actions 每 3 小时自动下载以下规则与服务器目录，交叉合并后按原始规则类型转换并提交生成文件到 `main`：

- [SpeedtestInternational.lsr](https://kelee.one/Tool/Loon/Lsr/SpeedtestInternational.lsr)
- [MetaCubeX speedtest.mrs](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/speedtest.mrs)
- [V2Fly category-speedtest](https://github.com/v2fly/domain-list-community/blob/master/data/category-speedtest)（使用 `@cn` / `@!cn` 地区标签）
- [SukkaW Speedtest](https://github.com/SukkaW/Surge/blob/master/Source/domainset/speedtest.conf)（人工维护的平台后缀）
- Sukka 实时 Ookla 服务器目录与 LibreSpeed 镜像
- [LibreSpeed 官方服务器清单](https://github.com/librespeed/speedtest/blob/master/server-list.json)
- [oneclickvirt Speedtest 快照](https://github.com/oneclickvirt/speedtest/blob/main/model/snapshot/speedtest-servers.json)
- [blackmatrix7 Speedtest](https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/Clash/Speedtest/Speedtest.list)
- [TelegramSG.lsr](https://rule.kelee.one/Loon/TelegramSG.lsr)
- [TelegramNL.lsr](https://rule.kelee.one/Loon/TelegramNL.lsr)

同时从 [MetaCubeX meta-rules-dat](https://fastly.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@meta/geo/geosite/nodeseek.mrs) 拉取 NodeSeek MRS，转换并同步到 `Nodeseek.yaml` 和 `Nodeseek.srs`。

每次同步都会从 Sing-box 官方 `releases/latest` API 下载最新版本的编译器，再从各自源文件直接编译 Sing-box `.srs`，包括 Speedtest、Telegram 和 WebRTC。`.srs` 是 Sing-box 原生二进制 rule-set，直接在 Sing-box 中使用，不要把 `.mrs` 改名为 `.srs`。任务会打印实际使用的 Sing-box 版本，并校验生成文件的官方 `SRS` 文件头。编译前通过该官方核心的 `rule-set upgrade` 探测最新源格式，不再固定为 JSON v3；所有 SRS 都用探测到的最新源格式生成，并记录源格式和编译器实际选择的二进制版本。截至 2026-09-06，官方稳定版 1.14.0 的最新源格式为 v5，但官方编译器会将仅包含域名、域名后缀、关键词或 IP 网段的规则自动编译为兼容的二进制 v2。这是官方的格式选择逻辑，不代表使用旧编译器；不会手动抬高 SRS 文件头版本，也不会添加无关字段强制生成 v5。

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

Speedtest Loon 源同时包含域名和 IP 网段，因此会拆成两个行为独立的规则文件。域名 `.mrs` 与 `.srs` 使用 Kelee 大规模国际服务器清单作为主体，再与 MetaCubeX、V2Fly、SukkaW 人工维护清单、Sukka 实时 Ookla 目录、LibreSpeed 官方清单、oneclickvirt、blackmatrix7 和人工复核的国际测速平台后缀取并集。不会纳入 Sukka 自动累积的冷门历史服务器清单，避免已经不常用的备用记录持续增大文件。中国大陆服务器会依据上游 `cc: CN`、V2Fly `@cn` 标签、明确的大陆域名和 `.cn` 后缀排除；`cc: HK`、`@!cn`、台湾及其他境外记录保留。为了避免共享服务器域造成大陆误匹配，不发布全球 `+.ooklaserver.net` 后缀，而是每 3 小时从带国家代码的实时目录枚举境外 Ookla 主机。经过审核的域名后缀会替代其已经覆盖的精确主机；同一个明确命名为 `speedtest`、`ookla`、`librespeed`、`st` 或 `myspeed` 等测速专用子域下达到安全数量门槛时，也会提升为该专用子域的后缀规则。这样既覆盖原始国际规则和当前已验证的境外服务器，又不会把运营商的整个普通主域名纳入测速规则。脚本会逐条验证压缩前的每条保留规则仍被最终集合覆盖，不使用宽泛的 `DOMAIN-KEYWORD,speedtest`。IP `.mrs` 与 `.srs` 只收录上游明确提供的测速 IP 规则，不把动态域名强行解析成容易过期或误匹配的 IP。下载会自动重试，每个来源都有格式和最小规模检查；补充源临时失效时会保留上一版已验证规则，避免更新后丢失服务器。两种格式始终由同一个最终集合生成并进行语义一致性校验。

可莉测速源会同时核对原站、`ClaraCora/ege`、`linnux-x/surge` 和旧版 `mihoyo-typ/KeleeOne` 镜像，验证 `UpdateTime`、声明条数及域名/IP 最小规模后选择时间最新的有效版本；同一时间戳的规则集合不一致会停止发布。镜像可用不代表原站已确认最新，日志会明确标注回退来源，避免旧镜像的成功下载掩盖长期未同步。`.github/speedtest-source-state.json` 保存已采用版本的时间和 SHA-256，后续来源时间倒退会拒绝发布。新可莉版本仍与以上其他上游合并，不替换整套多源规则。

最终 Speedtest 域名和 IP 的 MRS/SRS 都会进一步无损压缩：MRS 使用 Zstandard level 19；SRS 在官方编译后保留原始文件头和规则集版本，仅将 zlib 数据流用 Zopfli 重新编码。只有文件确实变小且解压字节完全一致时才采用，域名、后缀、IP 匹配语义和客户端格式均不变；较大的结果不会覆盖原文件。工作流使用 Python 3.14，并固定安装 `zopfli==0.4.3`；压缩只发生在 GitHub Actions 生成阶段，客户端不需要安装额外组件。

Speedtest 域名文件使用 `behavior: domain` 和 `format: mrs`；IP 网段文件使用 `behavior: ipcidr` 和 `format: mrs`。

## 校验

每次推送到 `main` 分支或提交 Pull Request 时，GitHub Actions 会自动检查 YAML、规则引用、仓库链接和 MRS 文件头。
