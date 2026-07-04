# CI/CD 使用说明

## 目标

- Pull Request 和 `main` 分支提交自动执行单元测试、脚本编译、数据集校验、敏感凭据扫描和 Docker 健康检查。
- 生产部署只能从 GitHub Actions 手动触发，并要求输入 `DEPLOY`、通过 `production` Environment 审批。
- CD 仅更新 `cloudorder-ops-api`，不重启 Onyx、PostgreSQL、OpenSearch 或其他知识库组件。
- 新容器未达到 `healthy` 时自动恢复上一版源码并重新启动旧版本。

## 本机验证

```powershell
py -3.13 -m venv .venv
$env:HTTP_PROXY=''
$env:HTTPS_PROXY=''
$env:ALL_PROXY=''
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r cloudorder-ops-api\requirements-dev.txt
powershell -ExecutionPolicy Bypass -File scripts\run_ci.ps1
```

## GitHub 仓库设置

创建远程仓库并推送后，在 `Settings → Environments` 新建 `production` 环境，启用 Required reviewers。随后配置以下 Actions Secrets：

| Secret | 用途 |
|---|---|
| `DEPLOY_HOST` | 服务器域名或弹性公网 IP |
| `DEPLOY_USER` | SSH 用户，本项目为 `ubuntu` |
| `DEPLOY_SSH_KEY` | 专用于 CI/CD 的部署私钥，不应复用个人管理密钥 |
| `DEPLOY_KNOWN_HOSTS` | 预先核验的服务器 SSH host key，避免运行时盲目信任 |

不要把 `.env`、Onyx PAT、DeepSeek API Key、GitHub Token 或 SSH 私钥提交到仓库。服务器 `/home/ubuntu/cloudorder-ops-api/.env` 由人工创建并保留，CD 不上传该文件。

## 流水线

### CI

`.github/workflows/ci.yml`：

1. 安装锁定依赖；
2. 执行 5 个 FastAPI 单元测试；
3. 编译 API 与评测脚本；
4. 验证 50 道 CloudOrder 和 20 道 Mall 黄金问题；
5. 扫描可能泄露的 PAT、GitHub Token、模型 Key 和私钥；
6. 构建只读、无额外 Linux capability 的容器并验证 `/health`。

### CD

`.github/workflows/deploy.yml`：

1. 手动输入 `DEPLOY`；
2. 再次执行测试与安全校验；
3. 通过 `production` 环境审批；
4. 在 GitHub Runner 构建并导出 Linux 容器镜像；
5. 上传镜像、代码包和部署脚本，服务器只加载已验证镜像，不现场访问 PyPI；
6. 等待 Docker 健康检查，失败则恢复上一版。

## 当前状态与边界

代码已推送到公开仓库，`main` Push 与 Dependabot Pull Request 的两个 CI Job 均已通过。CD 工作流尚未执行，因为仍需在仓库中配置 `production` Environment、Required reviewers 和四个部署 Secrets。不要扩大 Mall Connector 只读 Token 的权限，也不要将个人 SSH 管理密钥直接复用为长期部署凭据。
