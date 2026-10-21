# eMudhra 中间 CA 弱密钥事件（2026-10）：技术说明与处置指南

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

2026 年 10 月，安全研究者公开披露 eMudhra 的 8 个中间 CA 使用了可被公开还原的弱 P-384 私钥。相关证书可链入 Apple、Chrome、Microsoft 和 Mozilla 信任的根证书，影响 TLS 与代码签名。本仓库用中文整理事件经过、受影响证书清单、检测方法与各平台修复步骤，供系统管理员、开发人员和应急响应人员参考。

> 非官方整理，基于公开信息，不构成任何形式的保证。证书状态、软件版本和根证书计划处置请以官方公告为准。

## 内容概览

- 事件来源、时间线与受影响证书清单
- 弱密钥的成因与技术分析
- 客户端信任状态检测
- Linux、macOS、Windows 及语言运行时的修复与验证
- 残余风险、常见问题与参考资料

## 目录结构

```
.
├── LICENSE
├── README.md
├── reports/
│   └── emudhra-intermediate-ca-incident.md   # 完整技术说明与处置指南
├── data/
│   ├── impacted-intermediates.json           # 受影响中间 CA 元数据
│   └── roots.json                            # 涉及根证书元数据
└── tools/
    └── filter_bundle.py                      # 通用 PEM bundle 过滤脚本
```

## 文件说明

| 路径 | 说明 |
|---|---|
| `reports/emudhra-intermediate-ca-incident.md` | 事件来源、根因、检测方法、各平台修复步骤、残余风险、FAQ 与指纹附录。 |
| `data/*.json` | 从公开披露页获取的原始元数据，包含 16 张受影响证书的 SHA-256、吊销时间和签发关系。 |
| `tools/filter_bundle.py` | 按证书 Subject 从 PEM bundle 中移除指定根证书；接受输入/输出路径参数。 |

## 使用方式

1. 阅读 `reports/emudhra-intermediate-ca-incident.md`，了解事件背景、受影响证书和风险范围。
2. 按报告第 7 节检测客户端是否仍信任受影响证书链。
3. 按报告第 8 节执行修复，并完成复测。
4. 需要重新生成过滤后的 bundle 时，使用 `tools/filter_bundle.py`：

   ```bash
   python3 tools/filter_bundle.py /etc/ssl/cert.pem /tmp/cert.pem.filtered
   ```

## 快速验证

```bash
# 应因证书错误而失败（表示已不信任受影响证书链）
curl -v https://dv-g3b-emudhra.we-have-a-problem.com/ -o /dev/null

# 应正常返回 200（表示普通站点不受影响）
curl -sS -o /dev/null -w '%{http_code}\n' https://example.com/
```

判定方式：

| 输出 | 含义 |
|---|---|
| `unable to get local issuer certificate (20)`，退出码 60，`%{http_code}` 为 `000` | 预期结果：证书链无法在本地信任库中落到受信任的根。 |
| HTTP 200 | 该客户端仍然信任受影响证书链，修复未生效。 |
| 连接超时、DNS 失败等 | 与证书无关的网络问题，需单独排查。 |

> `OpenSSL verify result: 14` 中的 `14` 是十六进制，等于十进制 20，与下一行括号里的 `(20)` 是同一个错误码，只是打印进制不同。

> `dv-g3b-aaa-emudhra.we-have-a-problem.com` 的证书链以 `AAA Certificate Services` 为根。许多发行版和 MacPorts 的 CA bundle 原本就不包含该根，使用这些客户端时，无论是否完成修复都会验证失败，因此它不适合作为通用判据；只有在仍信任 AAA 根的客户端（例如使用系统 bundle 或 macOS 钥匙串的场景）上，它才反映修复状态。

> 系统更新、包管理器升级或应用重装后，旧的 CA bundle 可能被写回，建议定期复测。

## 免责声明

- 本仓库为非官方资料整理，内容基于公开信息，不构成任何形式的保证。
- `tools/` 下的脚本仅作为示例，未覆盖所有操作系统、运行时和应用场景。
- 执行任何系统级修改前，请自行备份原始文件并评估兼容性影响。

## 许可

- 本仓库的原创内容（报告、README、脚本）采用 [MIT License](LICENSE)。
- `data/*.json` 来自公开披露页，不属于本许可证的授权范围；公开再分发前请确认原始来源的授权，或直接链接原始 URL。
