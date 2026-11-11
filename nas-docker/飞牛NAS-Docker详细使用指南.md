# 飞牛 NAS（fnOS）Docker 部署与使用指南

> 适用项目：`nas-docker/`  
> Git 分支：`feature/nas-docker-dashboard`  
> 本指南针对飞牛 NAS 的 Docker「项目／Compose」部署方式编写。飞牛不同 fnOS 版本的菜单名称可能略有差异；如界面没有「项目」入口，可使用 SSH 终端执行同样的 Docker Compose 命令。

## 0. 先了解它做什么，以及不做什么

本项目在 NAS 上运行一个轻量网页管理程序，并在同一容器中调用官方 CLI：

- Claude：通过 Claude Code CLI，使用 Claude Pro OAuth Token，固定发送一条 `hi`，指定 Haiku。
- Codex：通过 Codex CLI，在 NAS 容器中使用 ChatGPT 设备授权登录，发送一条最小化请求。
- 代理：两个 CLI 的请求可经由你已经运行的 Clash/Mihomo 容器转发。
- 管理：网页可配置启停、执行间隔、Codex 模型、推理强度，查看最近一次执行状态。

**重要边界：**

1. 这不是额度破解工具，也不会增加订阅总额度。
2. 一次成功的模型请求不代表五小时窗口一定被重置。只有在原窗口已经结束、服务商确实以新请求开启新窗口时，才可能达到预期效果。
3. 每次手动测试和定时调用都会消耗订阅用量。
4. NAS 本地保存的 OAuth 凭据仍然是敏感信息。NAS 被入侵、Docker 管理权限被滥用或数据目录被他人读取，仍可能导致账号被盗用。
5. 当前版本尚未在你的飞牛 NAS 实机上完成构建和登录验收。请先按本指南小规模测试，不要一开始就启用两个定时任务。

## 1. 部署前准备

### 1.1 检查 NAS 环境

建议准备：

- 已正常运行的飞牛 fnOS。
- 已安装并启用 Docker 应用。
- Docker Compose 项目功能可用。
- NAS 可以访问 npm、GitHub 及 Claude／OpenAI 服务（必要时经 Clash 代理）。
- 至少预留 2 GB 可用空间用于构建镜像、缓存和运行数据。
- NAS CPU 架构为项目依赖支持的架构。当前基础镜像为 Node.js 22 Debian Bookworm；Codex CLI 的预编译二进制是否支持你的 CPU 架构，需要在构建时验证。

建议先在飞牛「系统信息」中确认 CPU 架构。常见的 x86_64 和 aarch64 不代表所有 npm CLI 版本都必然提供对应二进制。

### 1.2 下载项目文件

进入你的 GitHub 仓库：

`https://github.com/wangzhen704/ai-usage-refresh/tree/feature/nas-docker-dashboard/nas-docker`

下载整个 `nas-docker` 文件夹，不能只下载 `compose.yaml`。目录中至少应有：

```text
nas-docker/
├── Dockerfile
├── compose.yaml
├── .env.example
├── .gitignore
├── app.py
├── README.md
├── CLASH-EXAMPLE.yaml
└── scripts/
    ├── codex-login.sh
    └── codex-status.sh
```

如果通过 Git 下载整个分支，也可以在 NAS 上使用 Git 克隆后切换到 `feature/nas-docker-dashboard`。请不要把 `data/` 目录上传到 GitHub。

### 1.3 在飞牛文件管理器创建目录

例如，在 NAS 的 Docker 应用目录下创建：

```text
/vol1/1000/docker/ai-usage-refresh/
```

将上一步下载的 `nas-docker` 目录内容放入该目录。这里的 `/vol1/1000` 仅为示例，请替换成你 NAS 实际的数据卷路径。

最终目录应类似：

```text
/vol1/1000/docker/ai-usage-refresh/
├── Dockerfile
├── compose.yaml
├── .env.example
├── app.py
├── scripts/
└── data/                 # 首次启动前创建，保存认证和配置
```

在飞牛文件管理器中创建 `data` 文件夹。它用于持久化保存管理员密码、Claude Token、Codex 登录状态和运行配置。不要将该目录映射到公开共享链接。

## 2. 网络模式：Dashboard 与 Mihomo 均使用 Host

你已经在飞牛 NAS 上将 Mihomo 配置为：

```yaml
container_name: mihomo
restart: unless-stopped
network_mode: host
```

本项目也采用 `network_mode: host`，与 Mihomo 共用 NAS 的网络命名空间。这样 Dashboard 可以直接通过 NAS 本机回环地址访问 Clash，不需要额外创建 Docker bridge 网络。

**注意：Host 网络模式下不要同时配置 `ports:` 或 `networks:`。** Docker 会忽略端口映射概念；如果同时写入网络别名或自定义网络配置，就可能出现你之前遇到的 `network-scoped alias is supported only for containers in user defined networks` 错误。

### 2.1 检查 Mihomo 代理监听

确认 Mihomo 的 HTTP/Mixed 代理端口，例如 7890，正在 NAS 本机监听。建议 Mihomo 配置使用：

```yaml
mixed-port: 7890
allow-lan: false
bind-address: 127.0.0.1
```

如果你的 Mihomo 配置已使用其他端口，以实际端口为准。这里使用 `127.0.0.1` 是因为 Dashboard 与 Mihomo 共用 host 网络；不需要为了 Dashboard 将代理开放到局域网。

在 NAS SSH 中检查：

```bash
ss -lntp | grep 7890
```

正常情况下应能看到 NAS 本机的 7890 端口处于监听状态。若你的 Mihomo 只启用了 SOCKS 端口，请额外启用 HTTP/Mixed 端口，当前网页代理设置接受 HTTP/HTTPS 代理 URL。

### 2.2 测试 NAS 本机代理

如果 NAS 安装了 curl，可以执行：

```bash
curl -I -x http://127.0.0.1:7890 https://www.google.com
```

此命令用于确认代理端口可用。具体能否访问目标网站取决于你的 Clash 规则和节点状态。

## 3. 配置 Docker Compose 项目

### 3.1 创建 .env 文件

在项目目录中，将 `.env.example` 复制为 `.env`。飞牛文件管理器可以复制并重命名；也可在 SSH 中执行：

```bash
cd /vol1/1000/docker/ai-usage-refresh
cp .env.example .env
```

示例内容：

```dotenv
CODEX_VERSION=0.167.1
CLAUDE_VERSION=2.1.322
DASHBOARD_PORT=8787
DASHBOARD_PORT=8787
```

版本号是当前仓库示例中记录的固定候选版本，不是自动更新标签。构建前应检查 npm 对应版本是否存在、是否支持 NAS 架构。不要将版本改成 `latest`。

### 3.2 数据目录权限

当前容器以非 root 用户 UID 10001 运行。需要让它对 `data` 目录具有读写权限。

如果飞牛文件管理器支持高级权限，可以将该目录所有者设置为 UID 10001 并授予该用户读写权限。也可以通过 SSH 执行：

```bash
cd /vol1/1000/docker/ai-usage-refresh
sudo chown -R 10001:10001 data
sudo chmod 700 data
```

如果 fnOS 的 ACL 与传统 Linux 权限同时生效，请确认没有额外 ACL 拒绝容器 UID 访问。不要通过 `chmod 777` 解决权限问题。

### 3.3 在飞牛 Docker 中创建项目

1. 打开飞牛「Docker」应用。
2. 进入「项目」或「Compose 项目」页面。
3. 选择「新增项目」。
4. 项目名称填写：`ai-usage-refresh`。
5. 路径选择刚才创建的 `/vol1/1000/docker/ai-usage-refresh`。
6. Compose 文件选择该目录中的 `compose.yaml`。
7. 确认项目环境变量从同目录 `.env` 读取。
8. 选择构建并启动。

如果飞牛界面要求直接填写 Compose 内容，可复制 `compose.yaml`，但必须同时确保 Dockerfile、app.py、scripts 目录在 Compose 的 build context（项目目录）内。

也可以通过 SSH 执行：

```bash
cd /vol1/1000/docker/ai-usage-refresh
docker compose config
docker compose up -d --build
```

先运行 `docker compose config` 检查配置是否成功解析。若提示 `CODEX_VERSION` 或 `CLAUDE_VERSION` 未设置，说明 .env 文件未放在 Compose 项目目录或没有被项目加载。

### 3.4 端口与访问方式

Compose 默认将网页端口绑定到 NAS 的 `127.0.0.1:8787`，这是有意的安全设置。不要直接把管理页面暴露到公网。

推荐使用 SSH 隧道：

```bash
ssh -L 8787:127.0.0.1:8787 NAS用户名@NAS局域网IP
```

然后在个人电脑浏览器打开：

`http://127.0.0.1:8787`

如果你只通过飞牛反向代理或 VPN 访问，需要另外规划 HTTPS 和访问控制。不要仅依赖网页密码保护后就将管理端口映射到公网。

## 4. 首次登录网页管理页面

容器第一次启动时会自动生成管理员密码，并保存在：

`data/admin-password.txt`

在飞牛 Docker 容器终端或 SSH 中读取：

```bash
docker compose exec dashboard cat /data/admin-password.txt
```

将密码保存在密码管理器中，不要发给他人。然后通过上一节的 SSH 隧道打开网页并登录。

默认状态：

- Claude 定时任务：关闭。
- Codex 定时任务：关闭。
- 执行间隔：300 分钟。
- Claude 模型：固定 Haiku。
- Codex 模型：留空，使用 CLI 默认模型。
- Codex 推理强度：low。
- 代理：空，即不使用代理。

## 5. 配置代理，连接独立 Clash 容器

登录网页，在「Clash HTTP / mixed 代理（NAS 本机地址）」填写：

`http://127.0.0.1:7890`

其中：

- `clash` 是 Docker 网络内的服务名称，不是 NAS IP。
- `7890` 是 Clash 的 HTTP/Mixed 代理端口，必须与实际配置一致。
- 如果你的 Clash 使用其他端口或服务名，请据实修改。
- 不要填写 `127.0.0.1:7890`：在 dashboard 容器中，127.0.0.1 指向 dashboard 自身。

保存后，代理配置会应用到 Codex 登录辅助脚本和两个 CLI 的模型请求。当前版本不提供网页代理连通性测试按钮；可先检查 Clash 日志和 Docker 网络，再执行一次手动请求。

若代理需要用户名密码，当前版本不支持在网页中配置认证代理。不要把带密码的代理 URL 填入页面；应使用只对 Docker 私有网络开放、无需认证的 Clash 内部监听端口，并通过网络隔离控制访问范围。

## 6. 配置 Codex（ChatGPT 订阅）

### 6.1 设备授权登录

在 NAS 的项目目录执行：

```bash
docker compose exec dashboard sh /opt/app/scripts/codex-login.sh
```

命令会在终端中显示设备授权网址和一次性代码。使用自己的电脑或手机浏览器打开终端显示的网址，登录你要使用的 ChatGPT 账号并完成授权。

如果 NAS 无法直连 OpenAI，先在网页配置代理，再重新执行登录命令。

### 6.2 检查登录状态

```bash
docker compose exec dashboard sh /opt/app/scripts/codex-status.sh
```

确认 CLI 显示已登录。登录数据保存在：

`data/home-codex/`

这是敏感凭据目录，禁止上传 GitHub、分享给其他人或放在公开共享目录。建议为 NAS 的备份设置访问控制。

如果出现 device login 不支持、浏览器授权失败或地区网络错误，不要改用复制浏览器 Cookie、抓取网页 Token 或第三方 Token 中转。先核对所安装 Codex CLI 的官方登录说明及该账号的支持情况。

### 6.3 Codex 模型设置

网页中的 Codex 模型默认留空，使用当前 CLI 的默认模型。建议先保持留空，不要把未经验证的模型昵称写进去。模型名称应以你当前 Codex CLI 和订阅实际支持的模型列表为准。

推理强度先保持 low。手动测试成功后，再考虑是否调整。

## 7. 配置 Claude Pro

### 7.1 生成 OAuth Token

在一台可信的个人电脑上，使用已登录 Claude Pro 订阅的 Claude Code CLI 执行：

```bash
claude setup-token
```

按照官方流程完成授权。命令会生成用于 Claude Code 的 OAuth Token。它相当于密码，不能发给 ChatGPT、不能写入 Git 仓库、不能放在网页表单或截图中。

### 7.2 将 Token 写入 NAS

在 NAS 项目目录中，通过 SSH 执行：

```bash
umask 077
cat > data/claude-oauth-token
```

终端等待输入时粘贴 Token，按回车后按 Ctrl-D 结束输入。然后执行：

```bash
sudo chown 10001:10001 data/claude-oauth-token
sudo chmod 600 data/claude-oauth-token
```

不要使用 `echo TOKEN` 或把 Token 放进命令参数，因为这些内容可能出现在 Shell 历史或进程列表中。

当前脚本会从该文件读取 Token，网页不显示 Token。Token 过期或撤销后，需要重新生成并替换该文件。

### 7.3 防止意外 API 计费

不要在容器中配置 `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN`。当前应用会在执行 Claude 命令时清除这两个环境变量，避免误走 Console API 计费路径。

如果 Claude 账号启用了额外用量或超额付费功能，建议在 Claude 账号用量设置中关闭，避免订阅限额耗尽后产生额外费用。

## 8. 第一次手动测试

**不要先打开定时任务。**

建议按以下顺序：

1. 检查 Mihomo 容器运行状态和 NAS 本机 7890 代理监听。
2. 在 NAS 终端检查 Codex 登录状态。
3. 检查 Claude Token 文件是否存在，权限是否为 600。
4. 在网页中先点击 Claude 的「手动请求一次」。
5. 查看状态是否变为 success。
6. 到 Claude 官方 Usage 页面检查是否确实计入 Pro 订阅。
7. 再手动触发 Codex，并到 ChatGPT/Codex 用量页面核对。
8. 如果确认认证路径正确、没有发生 API 额外计费，再考虑开启定时任务。

状态中的 success 只表示 CLI 返回成功且有输出，不代表服务商确认重置了五小时窗口。请结合官方 Usage 页面观察窗口时间变化。

## 9. 开启定时任务

网页设置区分别有 Claude 和 Codex 的定时任务开关。建议先只开启一个服务，间隔先保持 300 分钟。

注意当前调度器是容器内的简单轮询：

- 容器必须持续运行。
- 容器重启后，已启用的任务可能在启动后很快执行一次。
- 定时精度约为 20 秒轮询粒度，实际请求还受网络与服务商响应影响。
- 它不读取官方剩余额度，也无法判断服务商当前窗口是否已结束。
- 如果窗口尚未结束，额外请求会消耗额度，却未必开启新的窗口。

因此，如果你希望减少不必要消耗，建议手动控制开关，而不是长期无条件同时启用两个任务。

## 10. 更新、备份与迁移

### 10.1 备份哪些内容

至少备份：

- `data/config.json`：网页配置。
- `data/state.json`：运行状态。
- `data/admin-password.txt`：管理密码。
- `data/home-codex/`：Codex 登录状态，属于高敏感凭据。
- `data/claude-oauth-token`：Claude OAuth Token，属于高敏感凭据。

备份应加密并限制访问。不要把 data 目录提交到 GitHub。

### 10.2 更新代码

1. 先关闭网页中的两个定时任务。
2. 备份 data 目录。
3. 获取经过审查的新代码。
4. 检查版本号与 Dockerfile 变更。
5. 执行：

```bash
docker compose down
docker compose up -d --build
```

6. 检查容器日志和网页状态，再分别手动测试。

不要使用未知来源的预构建镜像替代本地构建。不要盲目更新到 latest。

### 10.3 迁移到新 NAS

迁移前停止容器，将 data 目录安全复制到新 NAS，并保留目录权限。新 NAS 上确认 Mihomo 的本机代理端口可用、调整 UID 10001 的目录所有权，再启动项目。迁移后检查 Codex 登录状态；若认证文件与设备绑定或失效，按官方流程重新登录。

## 11. 常见问题

### 11.1 构建失败：找不到 npm 版本

检查 `.env` 中的版本号是否存在，是否误把 GitHub Release 标签当作 npm 包版本。可在有网络的终端检查：

```bash
npm view @openai/codex@0.167.1 version
npm view @anthropic-ai/claude-code@2.1.322 version
```

如果 NAS 架构不受支持，可能在安装原生 Codex CLI 包时失败。应先确认官方包对目标架构的支持，不要随意改用来源不明的二进制。

### 11.2 页面打不开

检查：

```bash
docker compose ps
docker compose logs --tail=100 dashboard
```

确认容器健康、NAS 本机 8787 端口未被占用，并通过 SSH 隧道访问。由于 Dashboard 在 host 网络下仅监听 127.0.0.1，直接访问 NAS 局域网 IP 的 8787 端口通常不会成功，这是预期的安全行为。

### 11.3 提示 data 权限错误

检查 UID 10001 是否对 data 有读写权限：

```bash
ls -ld data
ls -l data
sudo chown -R 10001:10001 data
sudo chmod 700 data
sudo chmod 600 data/claude-oauth-token
```

不要对整个项目目录执行 777。

### 11.4 Codex 无法登录或请求失败

- 确认设备授权使用正确的 ChatGPT 账号。
- 确认 Clash 容器与 dashboard 在同一个 `ai_proxy_net`。
- 确认代理服务名、端口和监听地址。
- 执行 `docker compose exec dashboard sh /opt/app/scripts/codex-status.sh` 检查登录。
- 确认 CLI 版本和设备登录能力匹配。
- 不要把 Codex 的认证目录复制到公开 GitHub。

### 11.5 Claude 提示认证失败

确认 Token 是 Claude Pro 账号通过官方 `claude setup-token` 流程生成的；检查 `data/claude-oauth-token` 是否存在、是否为空、权限是否正确。Token 被撤销或过期时重新授权。

### 11.6 代理连接失败

- 页面代理地址应类似 `http://clash:7890`，不能填 localhost。
- 当前 host 网络方案下，Mihomo 绑定 127.0.0.1 正是推荐方式。
- 容器必须接入共享网络 `ai_proxy_net`。
- Clash 的端口要与网页填写一致。
- 若使用 SOCKS-only 端口，请在 Clash 中启用 HTTP/Mixed 端口；当前网页配置仅接受 HTTP/HTTPS 代理 URL。

### 11.7 显示 success，但五小时窗口没变化

这并不必然是程序故障。success 只代表命令成功结束。可能原因包括：当前窗口本来还未结束、请求被服务商按不同规则计入、该套餐没有对应窗口、或请求使用的账号与预期账号不一致。请以官方 Usage 页面为准，必要时关闭定时任务，避免重复消耗。

## 12. 安全检查清单

- [ ] 只从自己的 GitHub Fork 和指定分支获取代码。
- [ ] 使用经过核实的 CLI 版本，不使用 latest。
- [ ] Docker 管理权限只授予可信管理员。
- [ ] data 目录不对公网共享、不提交 Git、不随意复制。
- [ ] Claude Token 和 Codex 登录状态仅保存在 NAS。
- [ ] 网页管理端口不直接暴露公网，优先 SSH 隧道或 VPN。
- [ ] Mihomo 代理只监听 NAS 本机回环地址，不暴露公网。
- [ ] 首次手动测试成功后再启用定时任务。
- [ ] 定期检查 Claude 和 ChatGPT 官方用量页面及异常登录记录。
- [ ] Token 泄露时立即撤销并重新授权。

---

## 项目文件

- Docker Compose：`compose.yaml`
- 镜像构建：`Dockerfile`
- 网页程序：`app.py`
- Codex 登录：`scripts/codex-login.sh`
- Codex 状态：`scripts/codex-status.sh`
- Clash 网络示例：`CLASH-EXAMPLE.yaml`

本项目首版尚未在目标飞牛 NAS 上完成实机验收。部署、登录、代理及额度窗口效果均应逐项验证。
