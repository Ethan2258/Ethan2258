<h1 align="center">Hi, I'm Ethan</h1>

<p align="center">Android systems, Magisk / LSPosed, and Mihomo networking.</p>

<p align="center">
  <a href="https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml"><img alt="Validate repository" src="https://github.com/Ethan2258/Ethan2258/actions/workflows/validate.yml/badge.svg"></a>
  <a href="https://github.com/Ethan2258/Ethan2258/actions/workflows/sync-file.yml"><img alt="Sync Mihomo rules" src="https://github.com/Ethan2258/Ethan2258/actions/workflows/sync-file.yml/badge.svg"></a>
</p>

## About me

- Interested in Android system behavior, Magisk, LSPosed, and the Xposed ecosystem.
- Exploring transparent proxy solutions and practical IPv4 / IPv6 networking.
- Learning from open-source Android projects and refining Mihomo configurations.

## Repository contents

This profile repository also hosts the configurations and rule files I use for testing. Public file paths are intentionally kept at the repository root so existing raw and jsDelivr links continue to work.

| File | Purpose | Update method |
| --- | --- | --- |
| [`config(Android).yaml`](./config%28Android%29.yaml) | Mihomo template for Android | Manual |
| [`config(Windows).yaml`](./config%28Windows%29.yaml) | Mihomo template for Windows | Manual |
| [`ai_domain.mrs`](./ai_domain.mrs) | AI domain rules | Daily sync |
| [`ai_ipcidr.mrs`](./ai_ipcidr.mrs) | AI IP-CIDR rules | Daily sync |
| [`Webrtc_domain.mrs`](./Webrtc_domain.mrs) | WebRTC domain rules | Daily sync |
| [`telegram_nl.yaml`](./telegram_nl.yaml) | Telegram DC4 routing rules | Manual |
| [`telegram_sg.yaml`](./telegram_sg.yaml) | Telegram DC5 routing rules | Manual |
| [`Nodeseek.yaml`](./Nodeseek.yaml) | NodeSeek domain list | Manual |
| [`nodeseek.svg`](./nodeseek.svg) / [`nodeseek.png`](./nodeseek.png) | NodeSeek group icons | Manual |

## Before using the configs

These files are personal templates, not drop-in universal configurations. Review them before use:

- Replace the local subscription-provider URLs with your own endpoints. The Android and Windows templates currently expect local services on ports `3000` and `38324` respectively.
- Check proxy names, region filters, DNS servers, and rule-provider URLs against your environment.
- Keep credentials and private subscription URLs out of commits.
- Test configuration changes with a recent Mihomo build before making them your default.

## Automation

The [rule sync workflow](./.github/workflows/sync-file.yml) runs every day at 10:00 China Standard Time and can also be started manually. Downloads use retries and basic MRS format checks before replacing tracked files.

The [validation workflow](./.github/workflows/validate.yml) checks YAML syntax and duplicate keys, local rule references, repository-hosted URLs, and MRS file headers on every push and pull request.

Upstream rule data currently comes from [`milangree/rules`](https://github.com/milangree/rules). Please follow the upstream project's terms and update policy when redistributing or using these generated files.
