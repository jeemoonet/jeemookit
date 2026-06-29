# 飞书应用配置参考

## 两种上传模式

| 模式 | 命令 | 身份 | 是否需要机器人 |
|------|------|------|----------------|
| **用户账号（推荐）** | 默认 / `--mode user` | 你自己的飞书账号 | **否** |
| 应用身份 | `--mode app` | 企业自建应用 | 是（需文件夹授权） |

用户模式下：浏览器 OAuth 授权 → 文档导入到**你的**云空间；指定 `FEISHU_FOLDER_TOKEN` 时，只要**你**对该文件夹有编辑权限即可。

---

## 1. 创建自建应用（两种模式共用）

1. 打开 [飞书开放平台](https://open.feishu.cn/app) → 创建企业自建应用
2. 记录 **App ID**、**App Secret**
3. 在「权限管理 → API 权限」开通：
   - `docs:document:import` — 云文档导入（用户模式必需）
   - `offline_access` — 离线刷新 token（用户模式必需）
4. **发布版本**并等待管理员审批

> 用户模式**不需要**在「应用能力」里启用机器人。

---

## 2. 用户模式：浏览器 OAuth 配置

### 2.1 重定向 URL

在应用后台 **安全设置 → 重定向 URL** 添加：

```
http://127.0.0.1:8765/callback
```

（若自定义 `FEISHU_REDIRECT_URI`，须与此处配置完全一致。）

### 2.2 开启 token 刷新

在 **安全设置** 中开启「刷新 user_access_token」（部分租户默认已开）。

### 2.3 填写凭证

```bash
cp /path/to/jeemookit/templates/secrets.env.example ~/.jeemoo/secrets.env
```

```env
FEISHU_APP_ID=cli_xxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
# 可选：导入到你自己的某个文件夹
# FEISHU_FOLDER_TOKEN=fldcnxxxxxxxx
# 可选：自定义 OAuth 回调（默认 http://127.0.0.1:8765/callback）
# FEISHU_REDIRECT_URI=http://127.0.0.1:8765/callback
```

### 2.4 首次授权

```bash
python ~/.cursor/skills/md-to-feishu/scripts/md2feishu.py login
```

浏览器打开 → 用你的飞书账号登录并同意授权 → Token 保存到 `~/.jeemoo/feishu_user_token.json`。

之后上传会自动刷新 token，一般 **365 天内**无需重新授权。

---

## 3. 应用模式（备选，需机器人）

仅在 `--mode app` 时使用：

1. 启用应用 **机器人** 能力
2. 将目标文件夹分享给含该机器人的群组，授予 **可编辑**
3. 开通 `docs:document:import` 或 `drive:drive`

---

## 4. 获取文件夹 token

云文档中打开目标文件夹，URL 中 `folder/` 后的字符串即为 token：

`https://xxx.feishu.cn/drive/folder/fldcnqquW1svRIYVT2Np6Iabcef` → `fldcnqquW1svRIYVT2Np6Iabcef`

---

## 5. 限制与已知问题

| 项 | 说明 |
|----|------|
| 格式同步（默认） | 经 md-to-word 转 DOCX 再导入，支持 Mermaid / SVG / 本地图片 |
| 原始 MD（`--no-sync`） | 直接导入 .md，Mermaid 为代码块，本地图片通常不显示 |
| 文件大小 | 同步模式 DOCX ≤ **600MB**；原始 MD ≤ **20MB** |
| 扩展名 | `.md` / `.markdown` / `.mark` |
| 缓存 | 项目 `.cache/md2feishu/` 存放中间 DOCX |
| 内容截断 | 超出 docx 上限时 `extra` 字段会有提示码 |

---

## 6. 常见错误

| 错误 | 处理 |
|------|------|
| 尚未完成用户授权 | 运行 `md2feishu.py login` |
| `20027` scope 未开通 | 在应用后台开通 `docs:document:import` 和 `offline_access` 并发布 |
| `20071` redirect_uri 不匹配 | 检查安全设置中的重定向 URL 与 `FEISHU_REDIRECT_URI` |
| `1069908` 文件夹无权限（用户模式） | 确认**你的账号**对该文件夹有编辑权限 |
| `1069908` 文件夹无权限（应用模式） | 将文件夹分享给应用机器人 |
| `20037` refresh_token 过期 | 重新运行 `login` |
