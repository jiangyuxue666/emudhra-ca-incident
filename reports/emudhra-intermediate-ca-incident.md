# eMudhra 中间 CA 弱私钥事件（2026-10）技术说明与处置指南

> 文档版本：2026-10-22
> 性质：基于公开信息的整理，非官方文档。官方立场以 eMudhra 声明及各大根证书计划公告为准。
> 适用读者：系统管理员、开发人员、安全运维人员及关注本事件的终端用户。

---

## 目录

1. [摘要](#1-摘要)
2. [事件来源与权威链接](#2-事件来源与权威链接)
3. [受影响对象](#3-受影响对象)
4. [根本原因](#4-根本原因)
5. [危害评估](#5-危害评估)
6. [时间线](#6-时间线)
7. [如何检测是否受影响](#7-如何检测是否受影响)
8. [修复与加固](#8-修复与加固)
9. [残余风险与长期注意事项](#9-残余风险与长期注意事项)
10. [常见误区（FAQ）](#10-常见误区faq)
11. [参考资料](#11-参考资料)
12. [附录 A：受影响中间 CA 指纹全表](#附录-a受影响中间-ca-指纹全表)
13. [附录 B：涉及根证书指纹](#附录-b涉及根证书指纹)
14. [附录 C：常用 OpenSSL 命令](#附录-c常用-openssl-命令)

---

## 1. 摘要

2026 年 10 月 17 日，安全研究者公开披露：印度证书颁发机构 **eMudhra** 在 2025 年 4 月 30 日的密钥生成仪式中，因脚本缺陷额外生成了一批**强度严重不足的 P-384 私钥**，并错误地将其用于 8 个中间 CA 证书。这些私钥的数值小于 256（公开报道中出现的值包括 4、56、66、115、155、156、230、237），任何人都能从公开证书中通过暴力枚举在极短时间内还原。

受影响对象包括 **6 个 TLS 中间 CA** 和 **2 个代码签名中间 CA**，每个中间 CA 又存在两种签发路径（eMudhra 自签根与 Sectigo/AAA 交叉签名），合计 16 张证书。它们通过交叉签名链到被主流信任库收录的 `emSign ECC Root CA - G3` 和 `AAA Certificate Services`。

事件披露后，Chrome、Firefox 在当天完成封禁，苹果于 10 月 19 日、微软于 10 月 20 日完成封禁；eMudhra 于 10 月 18 日以 `ca_compromise` 原因吊销全部 8 个中间 CA，Sectigo 于 10 月 19 日吊销其交叉签名副本。截至 2026 年 10 月 21 日，**没有公开证据表明这些私钥在披露前被恶意利用**。

核心风险集中在**不检查证书透明度（CT）、不检查吊销状态**的客户端，包括部分命令行工具、旧版运行时、容器镜像、CI/CD 环境、嵌入式/IoT 设备，以及自带旧信任库的桌面应用（如旧版 Electron 应用）。

---

## 2. 事件来源与权威链接

### 2.1 公开披露页

- 事件主页：<https://emudhra.we-have-a-problem.com/>
- 源码仓库（Dennis Jackson 维护）：<https://github.com/galadran/we-have-a-problem.com>
- 受影响中间 CA 清单：<https://emudhra.we-have-a-problem.com/impacted-intermediates.json>
- 涉及根证书清单：<https://emudhra.we-have-a-problem.com/roots.json>
- 私钥持有证明（签名文件包）：<https://emudhra.we-have-a-problem.com/proof.zip>
- 各测试主机的证书链（离线验证用）：<https://emudhra.we-have-a-problem.com/chains.zip>

> 说明：该披露页由研究者维护，不是 eMudhra 官方站点。它的价值在于提供可复现的技术证据和持续的软件修复状态跟踪。

### 2.2 官方与权威渠道

- Mozilla Bugzilla #2083449（私钥泄露跟踪）：<https://bugzilla.mozilla.org/show_bug.cgi?id=2083449>
- Mozilla Bugzilla #1970728（同一批 P-384 中间 CA 签发无效 CRL 的关联问题）：<https://bugzilla.mozilla.org/show_bug.cgi?id=1970728>
- Google Security Blog（Chrome/Android 防护说明）：<https://blog.google/security/protecting-chrome-and-android-users-from-compromised-emudhra-intermediate-ca-certificates/>
- eMudhra 官方声明（根/中间 CA 不再受信任）：<https://emudhra.com/en/press-release/emudhra-statement-distrust-global-tls-intermediate-root-ca>
- eMudhra 官方声明（证书安全事件更新）：<https://emudhra.com/en/post/certificate-security-incident>
- oss-security 邮件列表讨论：<https://www.openwall.com/lists/oss-security/2026/10/20/19>
- Debian Bug #1151413（发行版信任库更新跟踪）：<https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1151413>

### 2.3 媒体与技术分析（供交叉参考）

- Help Net Security：<https://www.helpnetsecurity.com/2026/10/21/emudhra-certificates-private-keys-compromised/>
- CSO Online：<https://www.csoonline.com/article/4238338/google-mozilla-revoke-emudhra-intermediates-after-private-key-compromise.html>
- Simon Willison 的技术摘要：<https://simonwillison.net/2026/Oct/20/emudhra-certificates/>
- Cloudflare 关于"修复不止于浏览器"的警告：<https://www.itnews.com.au/news/cloudflare-warns-fixing-botched-emudhra-certs-goes-beyond-browsers-629804>
- Indian Express（专家称"潜在灾难性"）：<https://indianexpress.com/article/technology/tech-news-technology/cert-in-emudhra-certificate-compromise-catastrophic-say-experts-10930785/>
- CNBC TV18（eMudhra 股价单日下跌约 20%）：<https://www.cnbctv18.com/market/emudhra-share-price-here-is-why-the-stock-fell-20-percent-cybersecurity-incident-20015881.htm/amp>
- Korben（英文分析）：<https://korben.info/en/https-connections-at-risk-eight-weak-emudhra-keys.html>

---

## 3. 受影响对象

### 3.1 八个中间 CA

以下 8 个中间 CA 的私钥可被还原。每个名称对应两张证书：一张由 eMudhra 的 `emSign Root TLS CA - G3` / `emSign Root CS CA - G3` 签发，另一张由 Sectigo 的 `AAA Certificate Services` 交叉签名。

| 中间 CA 名称 | 用途 | 直接签发者（eMudhra 路径） | 交叉签名者（Sectigo 路径） |
|---|---|---|---|
| `EM DV TLS CA - G3B` | TLS（DV） | emSign Root TLS CA - G3 | AAA Certificate Services |
| `EM DV TLS CA - G3C` | TLS（DV） | emSign Root TLS CA - G3 | AAA Certificate Services |
| `EM OV TLS CA - G3B` | TLS（OV） | emSign Root TLS CA - G3 | AAA Certificate Services |
| `EM OV TLS CA - G3C` | TLS（OV） | emSign Root TLS CA - G3 | AAA Certificate Services |
| `EM EV TLS CA - G3B` | TLS（EV） | emSign Root TLS CA - G3 | AAA Certificate Services |
| `EM EV TLS CA - G3C` | TLS（EV） | emSign Root TLS CA - G3 | AAA Certificate Services |
| `EM OV CS CA - G3B` | 代码签名 | emSign Root CS CA - G3 | AAA Certificate Services |
| `EM OV CS CA - G3C` | 代码签名 | emSign Root CS CA - G3 | AAA Certificate Services |

- 唯一中间 CA 名称：8 个
- 证书总数：16 张（每个名称 2 个签发版本）
- 全部证书的密钥类型：EC `secp384r1`，名义位数 384
- eMudhra 侧吊销时间：2026-10-18（约 09:24–09:38 UTC）
- Sectigo 交叉签名侧吊销时间：2026-10-19 10:35 UTC
- 吊销原因：`ca_compromise`

精确指纹见[附录 A](#附录-a受影响中间-ca-指纹全表)。

### 3.2 涉及的根证书与信任路径

| 根证书 | 运营方 | 角色 | Apple | Chrome | Microsoft | Mozilla |
|---|---|---|---|---|---|---|
| `emSign Root TLS CA - G3` | eMudhra | 直接签发者（TLS） | 未收录 | 未收录 | 已收录 | 未收录 |
| `emSign Root CS CA - G3` | eMudhra | 直接签发者（代码签名） | 未收录 | 未收录 | 已收录 | 未收录 |
| `AAA Certificate Services` | Sectigo | 交叉签名者 | 已收录 | 已移除 | 已收录 | 已移除 |
| `emSign ECC Root CA - G3` | eMudhra | 交叉签名者 | 已收录 | 已收录 | 已收录 | 已收录 |

> 表中"已移除"指事件披露后的根计划处置状态，具体以各根计划公告为准。Chrome 对 `emSign ECC Root CA - G3` 的移除预计在 2026-10-27（PDT）前后覆盖到全部设备。

消费者的信任路径可以归纳为：

```
路径 1（微软生态）：
  leaf → 被攻破的中间 CA → emSign Root TLS/CS CA - G3（微软根库）

路径 2（Sectigo 交叉签名）：
  leaf → 被攻破的中间 CA（AAA 交叉签名版）→ AAA Certificate Services

路径 3（主流消费级信任库）：
  leaf → 被攻破的中间 CA → emSign Root TLS CA - G3（被 emSign ECC Root CA - G3 交叉签名）
       → emSign ECC Root CA - G3
```

因此，处置时需要关注的信任锚是 `emSign ECC Root CA - G3`、`AAA Certificate Services`，以及在微软根库中的 `emSign Root TLS CA - G3` / `emSign Root CS CA - G3`。

### 3.3 官方测试域名

披露页提供两个用于验证客户端是否仍信任这些证书链的测试主机：

- `dv-g3b-emudhra.we-have-a-problem.com`（走 eMudhra 根路径）
- `dv-g3b-aaa-emudhra.we-have-a-problem.com`（走 AAA 交叉签名路径）

判定逻辑：**如果客户端报证书错误，说明它不信任被攻破的中间 CA（安全）；如果能正常建立连接，说明它仍然信任（存在风险）。**

注意：这两个主机只能验证 TLS 信任路径，不能覆盖代码签名、自带信任库的应用或其他协议场景。

---

## 4. 根本原因

### 4.1 技术原理

P-384（secp384r1）私钥本应是一个接近 384 位的随机整数 `d`。椭圆的公开点 `Q = d × G`。只要 `d` 的取值空间足够大，从 `Q` 反推 `d` 在计算上不可行。

本次事件中，受影响的 8 个私钥实际是**小于 256 的整数**。这意味着：

- `d` 只有最多 256 种可能，逐一计算 `d × G` 并与证书公钥比对即可在毫秒级还原私钥；
- 公开报道中出现的值包括 4、56、66、115、155、156、230、237（不同来源列出的具体数值略有差异）；
- 不需要入侵 HSM、不需要窃取密钥、不需要内部人员——**任何能看到公开证书的人都能完成还原**。

这是"密钥生成缺陷"，不是"密钥被窃取"。

### 4.2 缺陷是如何产生的

根据 eMudhra 向 Mozilla 及媒体提供的说明：

1. 2025-04-30 的密钥生成仪式（Key Generation Ceremony）批量生成 24 个中间 CA，覆盖 A/B/C 三个系列、RSA-4096 与 P-384 两种算法、DV/OV/EV/代码签名等用途。
2. 仪式流程中的 wrap/unwrap 环节存在脚本缺陷，在预期密钥之外额外生成了一套**弱密钥**。
3. 这套弱密钥的标签与正确密钥相似，后续人工选择时发生错误，导致弱密钥被用于签发 B 系列和 C 系列的 P-384 中间 CA。
4. 受影响的正好是 B/C 系列的全部 P-384 密钥；RSA 密钥以及 A 系列 P-384 密钥未被 Mozilla 成功还原，但 Mozilla 曾要求 eMudhra 说明其是否同样受影响。完整根因分析报告尚未公开。

关联问题：Mozilla Bug #1970728 显示，同一批 P-384 中间 CA 曾签发**签名无效的 CRL**，说明该批次的生成/签发流程本身存在系统性问题。

### 4.3 各方立场

- **eMudhra**：基础设施未被入侵，无数据泄露，物理与逻辑安全控制保持有效；本事件与其印度 DSC/eSign 业务（运行在独立基础设施上）无关；受影响的 8 个中间 CA 未签发过终端实体证书，其中 7 个从未部署到生产环境，1 个部署但未用于签发；已知约 30,000 张证书需要迁移；全球 TLS 业务约占其营收 1%。
- **Mozilla / Google**：在数小时内独立还原了密钥，确认问题出在密钥生成环节而非签名环节；要求 eMudhra 就 HSM/FIPS 合规性、设备映射、A 系列与 RSA 密钥是否受影响等问题作出说明；两机构均在评估 eMudhra 在各自根计划中的后续资格。
- **研究界**：Scott Helme 等人独立复现了密钥还原过程；Cloudflare 等基础设施厂商在事件披露后部署了缓解措施。

---

## 5. 危害评估

### 5.1 理论影响

持有被攻破的中间 CA 私钥的攻击者可以：

- 为**任意域名**签发在受影响客户端看来"合法"的 TLS 证书，实施中间人攻击、解密和篡改 HTTPS 流量；
- 使用两把代码签名中间 CA 为可执行文件签名，使恶意软件在特定条件下显示为"可信发布者"；
- 配合 DNS 劫持、恶意 Wi-Fi、企业代理等 on-path 位置，对未修复客户端实现完全透明的流量劫持。

这是 CA 体系中最严重的一类失败：信任锚之下的签发权完全失控。

### 5.2 实际风险与缓解因素

以下因素显著降低了实际危害：

1. **披露与响应速度快**：Chrome/Firefox 当天封禁，苹果 2 天、微软 3 天内完成封禁；eMudhra 在报告次日吊销全部中间 CA。
2. **证书透明度（CT）构成硬约束**：Chrome、Safari、Firefox 等强制要求证书具备 CT 日志证明。攻击者为浏览器伪造证书必须提交到公开 CT 日志，等于自曝；披露页也指出这些中间 CA 在此期间没有 CT 记录，因此强制 CT 的客户端不可能被此类伪造证书攻击。
3. **未见公开利用证据**：Google 表示封禁前 CT 日志中没有来自这 6 个 TLS 中间 CA 的证书；eMudhra 表示未发现披露前密钥被还原或利用的证据。
4. **受影响中间 CA 几乎未签发真实证书**：据 eMudhra 声明，8 个中间 CA 未签发终端实体证书，这大幅降低了"合法证书被吊销"的附带影响。媒体报道的约 30,000 张待迁移证书，指的是同一根层级下**其他中间 CA** 签发的证书，而非这 8 个中间 CA 直接签发的证书。
5. **主流浏览器与操作系统已封禁**：当前版本的 Chrome、Edge、Firefox、Safari 以及 Windows/macOS 均已拒绝这些证书链。

### 5.3 仍然高风险的场景

- **不检查 CT、不检查吊销的客户端**：旧版 curl/OpenSSL、旧容器镜像、CI/CD 环境、自带 CA 库的 CLI 工具、旧版 Java 运行时；
- **嵌入式与 IoT 设备**：固件中的信任库通常多年不更新；
- **旧版 Electron 桌面应用**：Electron 将 Node/Chromium 的根证书库静态打包进应用，应用未升级则无法通过系统封禁获益；
- **代码签名**：Windows Authenticode 在部分配置下不强制在线检查吊销；离线或旧系统可能接受用被攻破密钥签名的恶意程序。macOS Gatekeeper 依赖 Apple 的 Developer ID 与公证体系，受此类证书影响较小；
- **定向攻击**：不使用 CT 的客户端在 2025-04 至 2026-10 的窗口期内理论上可被定向中间人攻击，且不会留下 CT 记录。"没有证据"不等于"绝对没发生"。

### 5.4 生态与商业影响

- 主流 Linux 发行版、语言运行时、包管理器在数日内集中更新 CA 信任库；
- eMudhra 被 Mozilla、Chrome 移除根信任，全球 TLS 业务受重创；
- 公开报道显示其股价在 2026-10-21 单日下跌约 20%；
- 事件暴露了 CA 密钥仪式、审计与监管流程中的系统性风险，其治理层面的影响可能比单次攻击更深远。

---

## 6. 时间线

| 时间（UTC） | 事件 |
|---|---|
| 2025-04-30 | eMudhra 密钥生成仪式，批量生成 24 个中间 CA；脚本缺陷产生弱密钥 |
| 2025-05-14 | Sectigo 使用 `AAA Certificate Services` 对相关中间 CA 完成交叉签名 |
| 2026-10-17 18:05 | Chrome Root Program 收到研究者 "Wayne" 的报告 |
| 2026-10-17 19:45 | Chrome 通过 CRLSet 封禁相关证书（无需重启浏览器） |
| 2026-10-17 20:06 | Mozilla 收到报告；约 2 小时内独立还原私钥 |
| 2026-10-17 ~22:59 | Mozilla OneCRL 封禁推送至 Firefox |
| 2026-10-18 09:24–09:38 | eMudhra 以 `ca_compromise` 吊销 8 个中间 CA（eMudhra 签发版本） |
| 2026-10-19 | Apple 封禁相关证书 |
| 2026-10-19 10:35 | Sectigo 吊销 AAA 交叉签名版本 |
| 2026-10-19 | Android 通过 Google Play Services 推送更新 |
| 2026-10-20 | Microsoft 封禁相关证书 |
| 2026-10-20 | NSS 3.131.1、Firefox 158.0.1 发布；Mozilla 移除对 `emSign ECC Root CA - G3` 的信任 |
| 2026-10-21 | eMudhra 发布第三版官方声明；各大发行版与运行时集中更新 |
| 2026-10-27（预计） | Chrome Root Store 对 `emSign ECC Root CA - G3` 的移除覆盖到全部设备 |

---

## 7. 如何检测是否受影响

### 7.1 在线快速测试

使用待检测的客户端访问两个测试主机：

```bash
curl -v https://dv-g3b-emudhra.we-have-a-problem.com/ -o /dev/null
curl -v https://dv-g3b-aaa-emudhra.we-have-a-problem.com/ -o /dev/null
```

判定：

- **出现证书验证错误**（如 `unable to get local issuer certificate`、`certificate is revoked`）→ 该客户端不信任被攻破的证书链，安全；
- **返回 HTTP 200** → 该客户端仍信任该链，存在风险。

浏览器中打开同一地址：若显示证书警告/拦截页 → 安全；若正常加载 → 需检查浏览器版本与更新状态。

注意：

- 不要使用 `curl -k` / `--insecure`，那会跳过验证，测试失去意义；
- 该方法只测试该客户端当前使用的信任库，不能代表其他客户端；
- 测试主机的证书链覆盖两条路径，但无法覆盖代码签名和自带信任库的应用。

### 7.2 检查本地信任库

#### Linux

```bash
# p11-kit 系统（Fedora、Arch、部分 Debian 配置）
trust list | grep -iE 'emSign|AAA Certificate Services'

# Debian/Ubuntu：查看已启用的 CA 配置
grep -iE 'emSign|AAA' /etc/ca-certificates.conf

# 直接在合并后的 bundle 中查找
awk 'BEGIN{RS="-----END CERTIFICATE-----"} /emSign ECC Root CA - G3|AAA Certificate Services/ {print}' \
  /etc/ssl/certs/ca-certificates.crt
```

更可靠的做法是按指纹核对（见 7.3）。

#### macOS

```bash
# 系统钥匙串中是否存在
security find-certificate -a -c "emSign ECC Root CA - G3" \
  /System/Library/Keychains/SystemRootCertificates.keychain
security find-certificate -a -c "AAA Certificate Services" \
  /System/Library/Keychains/SystemRootCertificates.keychain

# 命令行工具使用的 PEM bundle
openssl crl2pkcs7 -nocrl -certfile /etc/ssl/cert.pem \
  | openssl pkcs7 -print_certs -noout \
  | grep -iE 'emSign|AAA Certificate Services'
```

需要分别检查：

- 浏览器/系统钥匙串（Safari、系统原生应用）；
- `/etc/ssl/cert.pem`（系统自带 curl、git、python、perl、ruby、openssl）；
- 第三方包管理器/运行时各自的 bundle（如包管理器安装的 Python、Node、Electron 应用）。

#### Windows

```cmd
certutil -store Root | findstr /i "emSign AAA"
```

```powershell
Get-ChildItem Cert:\LocalMachine\Root |
  Where-Object { $_.Subject -match 'emSign|AAA Certificate Services' } |
  Format-List Subject, Thumbprint, NotAfter
```

> 提示：信任库中存在某张根证书，并不必然意味着客户端可被利用——还要看该客户端是否检查吊销、是否使用 CT。反过来，如果客户端使用的 bundle 中**没有**相关根证书，该路径就已被关闭。

### 7.3 指纹核对

对可疑证书计算 SHA-256 指纹并与附录比对：

```bash
openssl x509 -in suspect.pem -noout -subject -fingerprint -sha256
```

关键根证书指纹：

| 根证书 | SHA-256 指纹 |
|---|---|
| `emSign ECC Root CA - G3` | `86:A1:EC:BA:08:9C:4A:8D:3B:BE:27:34:C6:12:BA:34:1D:81:3E:04:3C:F9:E8:A8:62:CD:5C:57:A3:6B:BE:6B` |
| `AAA Certificate Services` | `D7:A7:A0:FB:5D:7E:27:31:D7:71:E9:48:4E:BC:DE:F7:1D:5F:0C:3E:0A:29:48:78:2B:C8:3E:E0:EA:69:9E:F4` |
| `emSign Root TLS CA - G3` | `7DD78D5F4F13459A83DFF9ABBBA62EDBAF6F2D102BF257FD712F4D9F2746ED8D` |
| `emSign Root CS CA - G3` | `F2EDAAFF3D9B701FB4D14C9F285F8C0BAD90FC3BCC1FA07D47F4718EDABA34A5` |

### 7.4 离线证据验证

`proof.zip` 包含研究者用每个被攻破私钥签名的消息（"We have a problem here - Wayne"）、每个中间 CA 的证书、公钥和签名。验证方法：

```bash
# 从证书导出公钥
openssl x509 -in intermediate.pem -pubkey -noout > pubkey.pem

# 验证 SHA-384 签名（ECDSA P-384）
openssl dgst -sha384 -verify pubkey.pem -signature signature.bin message.txt
```

输出 `Verified OK` 即证明签名由该证书对应私钥生成。

`chains.zip` 包含 12 台测试主机的完整证书链，可用于离线复现各客户端的验证结果：

```bash
openssl verify -CAfile trusted-roots.pem -untrusted chain.pem leaf.pem
```

### 7.5 软件版本自查

对照披露页的修复版本表，重点检查实际运行的程序而非应用外壳版本。常见项目：

| 组件 | 已修复版本（最低） |
|---|---|
| NSS | 3.131.1 |
| Go | 1.27.3 / 1.26.10 |
| Node.js | 22.23.4 / 24.22.1 / 26.12.1 |
| Python certifi | 2026.10.19 |
| pip | 26.2.2 |
| uv | 0.13.4 |
| Rust rustls-webpki | 0.103.16 |
| Rust webpki-roots / webpki-root-certs | 1.0.10 |
| rustup | 1.29.2 |
| Electron | 44.9.1 / 43.8.1 / 42.11.16 |
| Composer ca-bundle | 1.4.16 / 1.6.0 |
| Elixir castore | 1.0.22 |
| Perl Mozilla::CA | 20261020 |
| curl CA bundle | 2026-10-20 |
| Cloudflare CFSSL trust store | 2026.10.1 |
| Homebrew ca-certificates | 2026-09-25_1 |

Linux 发行版修复版本（示例）：

| 发行版 | 已修复版本 |
|---|---|
| Ubuntu ca-certificates | 20260816ubuntu 系列 |
| Debian ca-certificates | 20250419~deb12u2 / 20250419+deb13u1 / 20260816+nmu1 |
| Arch ca-certificates-mozilla | 3.131.1-1 |
| Gentoo ca-certificates | 20260816.3.125 |
| Fedora ca-certificates | 2026.2.92_v9.0.319 |
| Alpine ca-certificates | 20261020-r0 |
| Chainguard ca-certificates | 20260909-r3 |
| GNU Guix | commit 7608a99 |
| FreeBSD ca_root_nss | 待发布 |
| Java | 待发布 |
| Bun | 待发布 |
| Erlang certifi | 待发布 |

完整列表及最新状态以披露页为准。

### 7.6 服务器与证书持有者自查

如果运营 HTTPS 服务，需要确认服务器证书是否链到受影响的中间 CA：

```bash
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer -subject
```

若签发者 CN 为 `EM DV TLS CA - G3B/G3C`、`EM OV TLS CA - G3B/G3C`、`EM EV TLS CA - G3B/G3C`、`EM OV CS CA - G3B/G3C` 之一，则该证书需要更换。也可通过 CT 日志（如 crt.sh）按签发者名称检索。

对于代码签名证书持有者，需检查签名链是否经过 `EM OV CS CA - G3B/G3C`，并重新签名/更换证书。

---

## 8. 修复与加固

### 8.1 通用原则

1. **优先使用厂商更新**：浏览器、操作系统、发行版、语言运行时的官方更新是最安全的修复方式。
2. **先备份再手工修改**：任何信任库编辑都应保留原始文件，便于回滚。
3. **区分信任库**：浏览器、系统钥匙串、命令行 PEM bundle、运行时内置根库、应用自带根库是相互独立的，需要分别处理。
4. **修复后必须复测**：用第 7 节的方法验证，同时确认正常站点仍可访问。
5. **注意副作用**：移除老根（尤其是 `AAA Certificate Services`）可能导致遗留系统、内网设备、旧中间证书的 TLS 校验失败。若非必要，优先依赖发行版/厂商的精确更新。

### 8.2 Linux

各发行版的标准做法如下（具体文件名和目录以当前系统版本为准）：

**Debian / Ubuntu**

```bash
# 方式一：交互式取消勾选相关根证书
sudo dpkg-reconfigure ca-certificates

# 方式二：在 /etc/ca-certificates.conf 中给对应行加 "!" 前缀后更新
sudo update-ca-certificates --fresh
```

**Fedora / RHEL / CentOS Stream / Rocky / AlmaLinux / Amazon Linux 2023**

```bash
# 将待禁用的根证书 PEM 放入黑名单目录（目录名可能是 blacklist/ 或 blocklist/）
sudo cp emsign-g3.pem /etc/pki/ca-trust/source/blacklist/
sudo update-ca-trust extract
```

**openSUSE / SLES**

```bash
sudo cp emsign-g3.pem /etc/pki/trust/blacklist/
sudo update-ca-certificates
```

**Arch Linux**

```bash
# 使用 p11-kit 的 trust 工具移除，或放入 blocklist 后重建
sudo trust anchor --remove /path/to/emsign-g3.pem
sudo update-ca-trust
```

**Alpine Linux**

```bash
# 在 /etc/ca-certificates.conf 中给对应条目加 "!"，然后
sudo update-ca-certificates
```

**NixOS**

```nix
security.pki.caCertificateBlacklist = [
  "emSign ECC Root CA - G3"
  "AAA Certificate Services"
];
```

**FreeBSD 14+**

```bash
sudo cp <hashed>.0 /usr/share/certs/untrusted/
sudo certctl rehash
```

**NetBSD 10+**

```bash
sudo certctl untrust /etc/openssl/certs/<root-file>
```

> 再次提醒：是否同时移除 `AAA Certificate Services` 需要结合业务评估。该根自 2004 年起被广泛使用，移除可能影响遗留服务。

### 8.3 macOS

macOS 的系统层（钥匙串、Safari、系统原生应用）已通过系统更新封禁相关中间 CA。但内置的 `curl`、`git`、`python3`、`perl`、`ruby`、`openssl` 使用的是 `/etc/ssl/cert.pem`，**不做吊销检查**，需要单独处理。

**步骤 1：备份**

```bash
sudo cp -p /etc/ssl/cert.pem /etc/ssl/cert.pem.bak-$(date +%Y%m%d)
```

**步骤 2：移除相关根证书段**

下面脚本按 Subject 精确匹配，只删除指定根证书的 PEM 块，其余内容原样保留：

```python
#!/usr/bin/env python3
"""Remove certificate blocks whose subject matches given names from a PEM bundle."""
import re
import subprocess
import sys

src, out = sys.argv[1], sys.argv[2]
targets = [
    "emSign ECC Root CA - G3",
    # "AAA Certificate Services",   # 视业务需要启用
]

data = open(src, encoding="utf-8", errors="surrogateescape").read()
block_re = re.compile(
    r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----\s*", re.S
)

pieces, last, removed = [], 0, 0
for m in block_re.finditer(data):
    pem = m.group(0)
    subj = subprocess.run(
        ["openssl", "x509", "-noout", "-subject"],
        input=pem.encode(), capture_output=True
    ).stdout.decode()
    if any(t in subj for t in targets):
        pieces.append(data[last:m.start()])
        removed += 1
    else:
        pieces.append(data[last:m.end()])
    last = m.end()
pieces.append(data[last:])

if removed == 0:
    sys.exit("no matching certificate found; nothing written")
open(out, "w", encoding="utf-8", errors="surrogateescape").write("".join(pieces))
print(f"removed {removed} certificate block(s)")
```

```bash
python3 filter_bundle.py /etc/ssl/cert.pem /tmp/cert.pem.filtered
sudo install -m 644 -o root -g wheel /tmp/cert.pem.filtered /etc/ssl/cert.pem
```

**步骤 3：处理其他 bundle**

第三方包管理器和自编译工具可能使用独立的 bundle。用第 7.2 节的方法定位其 `CAfile`：

```bash
curl -v https://example.com/ 2>&1 | grep -i CAfile
```

对每个实际使用的 bundle 重复步骤 1–2。

**步骤 4：Python 虚拟环境与 pip**

系统 Python 或虚拟环境可能使用独立的根证书副本。可在 `sitecustomize.py` 中设置：

```python
import os
os.environ.setdefault("PIP_CERT", "/etc/ssl/cert.pem")
```

**步骤 5：Electron / 自带根库的应用**

这类应用无法通过系统 bundle 修复，必须升级到使用已修复 Electron 版本的发行版（见 8.5）。

### 8.4 Windows

- 安装 Windows Update 与 Microsoft 根证书更新；
- 使用 `certutil -store Root` 或 PowerShell 确认相关根/中间证书状态；
- 企业环境可通过组策略/证书吊销列表分发；
- 对代码签名验证敏感的环境，确保吊销检查（CRL/OCSP）可用，不要长期离线；
- 一般不建议手工删除系统根证书，优先依赖微软的封禁更新。

### 8.5 语言运行时、包管理器与桌面应用

| 组件 | 修复动作 |
|---|---|
| Go | 升级到 1.27.3 / 1.26.10 或更高 |
| Node.js | 升级到 22.23.4 / 24.22.1 / 26.12.1 或更高；npm/pnpm/yarn 随 Node 生效 |
| Python | `pip install -U certifi pip`（certifi ≥ 2026.10.19，pip ≥ 26.2.2） |
| uv | 升级到 ≥ 0.13.4 |
| Rust | `rustup update`（rustup ≥ 1.29.2；关注 rustls-webpki / webpki-roots 版本） |
| Java | 等待厂商更新；检查 `cacerts` 信任库 |
| Electron 应用 | 升级到内置 Electron ≥ 44.9.1 / 43.8.1 / 42.11.16 的版本；无法升级的旧应用应限制使用或改用网页版 |
| 容器镜像 | 重新拉取/重建基础镜像，确保 `ca-certificates` 为修复版本 |
| CI/CD | 更新构建镜像与缓存，清理旧的 CA bundle |
| Bun / Erlang / FreeBSD 等 | 关注上游修复状态 |

> 检查 Electron 应用实际使用的 Electron 版本（macOS 示例）：
>
> ```bash
> /usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' \
>   "/Applications/App.app/Contents/Frameworks/Electron Framework.framework/Versions/A/Resources/Info.plist"
> ```

### 8.6 服务器运营者

1. 清点所有证书，识别签发者 CN 属于上述 8 个中间 CA 的证书；
2. 通过 eMudhra 或原签发渠道申请替换证书；
3. 更新服务器证书链，确保不再发送受影响的中间证书；
4. 对代码签名证书执行同样的清点与更换；
5. 关注 eMudhra 公布的迁移指引与约 30,000 张证书的迁移进度；
6. 若使用固定证书（pinning）或私有信任库，同步更新。

### 8.7 修复后验证

```bash
# 应失败（证书错误）
curl -v https://dv-g3b-emudhra.we-have-a-problem.com/ -o /dev/null
curl -v https://dv-g3b-aaa-emudhra.we-have-a-problem.com/ -o /dev/null

# 应成功
curl -sS -o /dev/null -w '%{http_code}\n' https://example.com/
curl -sS -o /dev/null -w '%{http_code}\n' https://github.com/
```

同时验证：

- 浏览器访问正常站点无警告；
- 业务系统、内网服务、遗留设备仍可正常建立 TLS 连接（尤其是移除 AAA 后）；
- 语言运行时、包管理器可正常下载依赖；
- Electron/桌面应用已升级且可正常联网。

### 8.8 回滚

所有手工修改前均应备份，回滚即恢复备份文件：

```bash
# 示例
sudo cp -p /etc/ssl/cert.pem.bak-YYYYMMDD /etc/ssl/cert.pem
```

注意：操作系统更新、包管理器升级、应用重装可能重新写入旧的信任库，修复后需定期复测。

---

## 9. 残余风险与长期注意事项

1. **未修复的客户端仍是暴露面**：嵌入式设备、IoT、OT 网络、离线系统、旧容器镜像、自带根库的桌面应用不会自动获得更新。
2. **代码签名风险具有滞后性**：即使 TLS 侧已修复，用被攻破密钥签名的恶意软件仍可能在未检查吊销的旧系统上生效。建议对来源不明的可执行文件保持警惕，尤其是 Windows 平台。
3. **CT 只保护强制 CT 的客户端**：不查 CT 的客户端在理论上仍可被定向攻击；"CT 日志里没有记录"不等于"绝对没有被利用"。
4. **根移除的附带影响**：移除 `AAA Certificate Services` 可能破坏依赖旧 Comodo/Sectigo 中间证书的服务；移除 `emSign ECC Root CA - G3` 可能影响仍在使用该层级其他中间 CA 的站点。
5. **根计划与监管后续**：Mozilla、Google 正在评估 eMudhra 的根计划资格；CA/Browser Forum 可能进一步处置。相关决定可能影响更多 eMudhra 层级证书。
6. **更新可能回写旧 bundle**：系统更新、`port upgrade`、镜像重建、应用升级都可能恢复旧文件，建议将 7.1 的在线测试纳入例行检查。
7. **证据的局限性**：目前没有公开的恶意利用证据，但这主要说明"未被公开发现"，不能排除针对特定目标的、未进入 CT 日志的攻击。

---

## 10. 常见误区（FAQ）

**Q1：私钥公开，是不是意味着攻击者可以直接入侵设备？**
不是。私钥只赋予"签发可信证书"的能力。攻击者仍需处于网络路径上（恶意 Wi-Fi、被控路由器/ISP、企业代理），或诱导客户端连接到其控制的服务器。它不会凭空获得设备访问权限。

**Q2：浏览器访问正常，是否说明设备没有问题？**
不一定。浏览器、系统钥匙串、命令行工具、语言运行时、Electron 应用各自使用独立的信任库。浏览器安全不代表 `curl`、Python、Node 或桌面应用安全。

**Q3：证书已经被吊销，是否就绝对安全？**
只有当客户端**实际检查吊销状态**（CRL/OCSP/CRLSet/OneCRL）或接收了更新后的信任库时才成立。很多命令行工具和嵌入式客户端默认不检查吊销。

**Q4：CT 日志里没有恶意证书，是否说明从未被利用？**
不能完全排除。强制 CT 的客户端（主流浏览器）确实受到保护；但非 CT 客户端可被定向攻击且不留下公开记录。

**Q5：直接把 AAA 根删掉是否没有代价？**
有代价。`AAA Certificate Services` 是 2004 年的老根，大量遗留设备、内网服务和旧中间证书仍依赖它。移除前应评估业务影响，并准备回滚方案。

**Q6：需要重装系统、修改所有密码吗？**
在没有发现实际入侵迹象的情况下，不需要。此次事件是 CA 侧的密钥生成缺陷，不涉及终端设备被植入恶意软件。若存在被定向中间人攻击的具体迹象，则应另行开展应急响应。

**Q7：升级浏览器就够了吗？**
不够。还需检查操作系统信任库、命令行工具、语言运行时、包管理器、容器镜像和自带根库的桌面应用。

---

## 11. 参考资料

1. eMudhra Intermediate CA Compromise（披露主页）：<https://emudhra.we-have-a-problem.com/>
2. 披露页源码：<https://github.com/galadran/we-have-a-problem.com>
3. 受影响中间 CA JSON：<https://emudhra.we-have-a-problem.com/impacted-intermediates.json>
4. 涉及根证书 JSON：<https://emudhra.we-have-a-problem.com/roots.json>
5. 私钥持有证明：<https://emudhra.we-have-a-problem.com/proof.zip>
6. 测试主机证书链：<https://emudhra.we-have-a-problem.com/chains.zip>
7. Mozilla Bug 2083449：<https://bugzilla.mozilla.org/show_bug.cgi?id=2083449>
8. Mozilla Bug 1970728：<https://bugzilla.mozilla.org/show_bug.cgi?id=1970728>
9. Google Security Blog：<https://blog.google/security/protecting-chrome-and-android-users-from-compromised-emudhra-intermediate-ca-certificates/>
10. eMudhra 官方声明（根/中间 CA 不再受信任）：<https://emudhra.com/en/press-release/emudhra-statement-distrust-global-tls-intermediate-root-ca>
11. eMudhra 官方声明（事件更新）：<https://emudhra.com/en/post/certificate-security-incident>
12. oss-security 讨论：<https://www.openwall.com/lists/oss-security/2026/10/20/19>
13. Debian Bug 1151413：<https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1151413>
14. Help Net Security 报道：<https://www.helpnetsecurity.com/2026/10/21/emudhra-certificates-private-keys-compromised/>
15. CSO Online 报道：<https://www.csoonline.com/article/4238338/google-mozilla-revoke-emudhra-intermediates-after-private-key-compromise.html>
16. Simon Willison 技术摘要：<https://simonwillison.net/2026/Oct/20/emudhra-certificates/>
17. Cloudflare 相关警告：<https://www.itnews.com.au/news/cloudflare-warns-fixing-botched-emudhra-certs-goes-beyond-browsers-629804>
18. Indian Express 报道：<https://indianexpress.com/article/technology/tech-news-technology/cert-in-emudhra-certificate-compromise-catastrophic-say-experts-10930785/>
19. CNBC TV18 股价报道：<https://www.cnbctv18.com/market/emudhra-share-price-here-is-why-the-stock-fell-20-percent-cybersecurity-incident-20015881.htm/amp>
20. Korben 分析：<https://korben.info/en/https-connections-at-risk-eight-weak-emudhra-keys.html>

---

## 附录 A：受影响中间 CA 指纹全表

| 名称 | 签发者 | SHA-256 | 吊销时间（UTC） |
|---|---|---|---|
| EM DV TLS CA - G3B | emSign Root TLS CA - G3 | `42C4ACCD12C4F59597925E1A08A7A90102608543809308D50EC427E118BA1493` | 2026-10-18 09:24:32 |
| EM DV TLS CA - G3B | AAA Certificate Services | `45A883F349AEDFD5F3A649B5498FFB121712BA8B448F3F2A91DBC5A766FCDDBE` | 2026-10-19 10:35:36 |
| EM OV TLS CA - G3B | emSign Root TLS CA - G3 | `98B896625C0C230ADEEC3EB2CF6AAD5001ECF9156A68644E82374CE5833BC25B` | 2026-10-18 09:37:19 |
| EM OV TLS CA - G3B | AAA Certificate Services | `5F1DED4DD590AF74631290CF073B122A2AAC6A1FA479778A0BD43579BD832699` | 2026-10-19 10:35:36 |
| EM EV TLS CA - G3B | emSign Root TLS CA - G3 | `E7568FE6E12331F4FD7DE61DA4C7559D0F8EB192A218D4741A3BA75184333838` | 2026-10-18 09:28:53 |
| EM EV TLS CA - G3B | AAA Certificate Services | `579480AEA166290BD3C643589E795FC0D0E54E86505D180F1DFF99EFD3199512` | 2026-10-19 10:35:36 |
| EM DV TLS CA - G3C | emSign Root TLS CA - G3 | `0164D7CEAE5BB909C272AF151FF44B1177AE9B47D9424B94F1D9558C30934D19` | 2026-10-18 09:27:07 |
| EM DV TLS CA - G3C | AAA Certificate Services | `62B7F9868263F72F6911FC78CEAF72C1979158B7368BF648683BB2AA39B02E72` | 2026-10-19 10:35:36 |
| EM OV TLS CA - G3C | emSign Root TLS CA - G3 | `CB6E15165AC802E9B3F993F16C25D41F4E81C21EBDE71AE1B012AC00BF9C7C3F` | 2026-10-18 09:38:46 |
| EM OV TLS CA - G3C | AAA Certificate Services | `7485B51C0ED192878FA1D2F948FB529AE1842CC5086C4B67F7BE5B2039DE9489` | 2026-10-19 10:35:36 |
| EM EV TLS CA - G3C | emSign Root TLS CA - G3 | `432EC25F0D28DE9006D97BF752F17BBB2CD41F669933FCB072D9A1148D0261F3` | 2026-10-18 09:30:49 |
| EM EV TLS CA - G3C | AAA Certificate Services | `FD9D5C2DBBD4995AB69B8D50C439D9527B00529199C2FD01B2174EB58F07021F` | 2026-10-19 10:35:36 |
| EM OV CS CA - G3B | emSign Root CS CA - G3 | `9E39DE2881273ACC225A149C72BA3E0F51424963669AB633EE1DC7DF5DB067B4` | 2026-10-18 09:33:37 |
| EM OV CS CA - G3B | AAA Certificate Services | `A496E23AC0CAB8155FC9B117B97EAE368EFCBB9041AEC8804D5A308D2D01C2D8` | 2026-10-19 10:35:36 |
| EM OV CS CA - G3C | emSign Root CS CA - G3 | `4B2460A466F95FD40113BCDCCA2CEB29B3B093921DE45474DA7DF48874C630B1` | 2026-10-18 09:35:24 |
| EM OV CS CA - G3C | AAA Certificate Services | `84112972B8E59D14560AE7E7119654474AAD119990CF3722BFC1E3B91615E1FD` | 2026-10-19 10:35:36 |

## 附录 B：涉及根证书指纹

| 根证书 | SHA-256 | 有效期 |
|---|---|---|
| `emSign ECC Root CA - G3` | `86:A1:EC:BA:08:9C:4A:8D:3B:BE:27:34:C6:12:BA:34:1D:81:3E:04:3C:F9:E8:A8:62:CD:5C:57:A3:6B:BE:6B` | 2018-02-18 → 2043-02-18 |
| `AAA Certificate Services` | `D7:A7:A0:FB:5D:7E:27:31:D7:71:E9:48:4E:BC:DE:F7:1D:5F:0C:3E:0A:29:48:78:2B:C8:3E:E0:EA:69:9E:F4` | 2004-01-01 → 2028-12-31 |
| `emSign Root TLS CA - G3` | `7DD78D5F4F13459A83DFF9ABBBA62EDBAF6F2D102BF257FD712F4D9F2746ED8D` | 2024-02-08 → 2049-02-07 |
| `emSign Root CS CA - G3` | `F2EDAAFF3D9B701FB4D14C9F285F8C0BAD90FC3BCC1FA07D47F4718EDABA34A5` | 2024-02-08 → 2049-02-07 |

## 附录 C：常用 OpenSSL 命令

```bash
# 查看服务器证书链与验证结果
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null

# 查看某张证书的 Subject / Issuer / 有效期 / 指纹
openssl x509 -in cert.pem -noout -subject -issuer -dates -fingerprint -sha256

# 验证证书链（trusted-roots.pem 为受信任根集合）
openssl verify -CAfile trusted-roots.pem -untrusted chain.pem leaf.pem

# 从证书导出公钥
openssl x509 -in cert.pem -pubkey -noout > pubkey.pem

# 验证 SHA-384 签名
openssl dgst -sha384 -verify pubkey.pem -signature signature.bin message.txt

# 列出 PEM bundle 中所有证书的 Subject
openssl crl2pkcs7 -nocrl -certfile bundle.pem \
  | openssl pkcs7 -print_certs -noout

# 检查 bundle 是否包含特定根证书
openssl crl2pkcs7 -nocrl -certfile bundle.pem \
  | openssl pkcs7 -print_certs -noout \
  | grep -iE 'emSign|AAA Certificate Services'
```

---

*本文档基于 2026-10-22 之前的公开信息整理。事件仍在发展中，修复版本、根计划处置与官方结论可能更新，请以文首所列官方链接的最新内容为准。*
