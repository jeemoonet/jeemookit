# 飞书文档下载配置参考（feishu-to-md）

## 1. 需要的凭证

在 `~/.jeemoo/secrets.env` 配置：

```env
FEISHU_APP_ID=cli_xxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
# 可选，默认 open.feishu.cn
# FEISHU_DOMAIN=open.feishu.cn
# 可选，默认 http://127.0.0.1:8765/callback
# FEISHU_REDIRECT_URI=http://127.0.0.1:8765/callback
```

## 2. 建议开通权限

在飞书开放平台应用中开通并发布：

- `docs:document:readonly`
- `wiki:wiki:readonly`（如果要传入 wiki 链接）
- `offline_access`

> 若你已配置 `md-to-feishu`，可复用同一套应用与 token 存储。

## 3. 首次授权

```bash
python ~/.cursor/skills/feishu-to-md/scripts/feishu2md.py login
```

成功后 token 保存到：`~/.jeemoo/feishu_user_token.json`

## 4. 常见问题

| 问题 | 处理 |
|------|------|
| 提示未授权/token 过期 | 重新执行 `login` |
| `scope` 或权限不足 | 在应用后台补齐权限并发布版本 |
| wiki 链接无法解析 | 补开 `wiki:wiki:readonly` 并确认链接有效 |
| 图片下载失败 | 文档会保留远程 URL，不影响主文内容（成功下载的图片保存在输出目录 `assets/`） |
