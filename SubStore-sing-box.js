// Sub-Store script for Ethan2258's official sing-box profile template.
// By default, nodes are pulled directly from Ethan2258's Sub-Store URL.
// Optional argument: url=<encoded replacement subscription URL>.

const { url, includeUnsupportedProxy } = $arguments;
const parser = ProxyUtils.JSON5 || JSON;
const config = parser.parse($content ?? $files[0]);
const subscriptionURL =
  url || "https://sub.110726.com/download/collection/Sub";

const response = await $substore.http.get({
  url: subscriptionURL,
  headers: { "user-agent": "sing-box" },
  timeout: 30000,
});
if (response.statusCode < 200 || response.statusCode >= 300) {
  throw new Error(`远程订阅请求失败：HTTP ${response.statusCode}`);
}
const produced = parser.parse(response.body);
const nodeOutbounds = Array.isArray(produced)
  ? produced
  : produced.outbounds || [];
const endpoints = Array.isArray(produced?.endpoints) ? produced.endpoints : [];
const nodes = [...nodeOutbounds, ...endpoints];

if (nodes.length === 0) {
  throw new Error("订阅没有生成任何 sing-box 节点，已停止输出配置");
}

const requiredGroups = [
  "Proxy",
  "Speedtest",
  "TG DC5",
  "TG DC4",
  "AI",
  "NodeSeek",
  "YouTube",
  "Google",
  "Discord",
  "HK",
  "TW",
  "SG",
  "EU",
  "MO",
];
const businessGroups = [
  "Speedtest",
  "TG DC5",
  "TG DC4",
  "AI",
  "NodeSeek",
  "YouTube",
  "Google",
  "Discord",
];
const regionPatterns = {
  HK: /🇭🇰|香港|\b(?:hk|hong\s*kong)\b/i,
  TW: /🇹🇼|台湾|台灣|\b(?:tw|taiwan)\b/i,
  SG: /🇸🇬|新加坡|\b(?:sg|singapore)\b/i,
  EU: /🇳🇱|荷兰|荷蘭|\b(?:nl|netherlands|holland)\b/i,
  MO: /🇲🇴|澳门|澳門|\b(?:mo|macao|macau)\b/i,
};

if (!Array.isArray(config.outbounds)) {
  throw new Error("模板缺少 outbounds 数组");
}

const groups = new Map(config.outbounds.map((outbound) => [outbound.tag, outbound]));
for (const tag of requiredGroups) {
  if (!groups.has(tag)) {
    throw new Error(`模板缺少策略组：${tag}`);
  }
}

const staticTags = new Set(config.outbounds.map((outbound) => outbound.tag));
const seenNodeTags = new Set();
for (const node of nodes) {
  if (!node || typeof node.tag !== "string" || node.tag.length === 0) {
    throw new Error("订阅包含没有 tag 的节点");
  }
  if (seenNodeTags.has(node.tag)) {
    throw new Error(`订阅包含重复节点标签：${node.tag}`);
  }
  if (staticTags.has(node.tag)) {
    throw new Error(`节点标签与模板出站重名：${node.tag}`);
  }
  seenNodeTags.add(node.tag);
}

const nodeTags = nodes.map((node) => node.tag);
const unique = (values) => [...new Set(values)];
const fixedBusinessMembers = ["Proxy", "HK", "TW", "SG", "EU", "MO"];

groups.get("Proxy").outbounds = ["HK", "TW", "SG", "EU", "MO"];
for (const tag of businessGroups) {
  groups.get(tag).outbounds = unique([...fixedBusinessMembers, ...nodeTags]);
}

for (const [tag, pattern] of Object.entries(regionPatterns)) {
  const matches = nodes
    .filter((node) => pattern.test(node.tag))
    .map((node) => node.tag);
  if (matches.length === 0) {
    throw new Error(`${tag} 没有匹配到任何节点，已停止输出配置`);
  }
  groups.get(tag).outbounds = unique(matches);
}

config.outbounds.push(...nodeOutbounds);
if (endpoints.length > 0) {
  config.endpoints = [...(config.endpoints || []), ...endpoints];
}

$content = JSON.stringify(config, null, 2);
