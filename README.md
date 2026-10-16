# 夸克网盘自动签到

通过 GitHub Actions 定时运行夸克网盘签到脚本。支持单账号、多账号，以及旧版参数格式和新版完整签到 URL 格式。

## 配置方法

1. 在本仓库的 **Settings → Secrets and variables → Actions** 中创建或更新 Repository secret。
2. Secret 名称必须为 `COOKIE_QUARK`。
3. 将抓取到的夸克签到参数保存到 Secret，切勿写入代码或公开提交。

### 获取签到参数

使用手机抓包工具（例如 [ProxyPin](https://github.com/wanghongenpin/proxypin)）开启 HTTPS 抓包，在夸克 App 中进入网盘签到/领空间页面，搜索：

`https://drive-m.quark.cn/1/clouddrive/act/growth/reward`

复制完整请求 URL，并确认查询参数包含 `kps`、`sign` 和 `vcode`。参数有效期可能变化，签到失败时需要重新抓取。

### COOKIE_QUARK 格式

推荐使用完整 URL 格式：

```text
user=我的账号; url=https://drive-m.quark.cn/1/clouddrive/act/growth/reward?...&kps=示例值&sign=示例值&vcode=示例值;
```

旧格式仍兼容：

```text
user=我的账号; kps=示例值; sign=示例值; vcode=示例值;
```

以上均为格式示例，不可直接用于签到。多账号可按行分隔，也可使用 `&&` 分隔。每个账号都需要独立的一套参数。

## 自动执行与测试

- 工作流每天按北京时间约 09:00 和 13:00 执行；GitHub Actions 可能延迟启动。
- 进入 **Actions → Quark签到 → Run workflow** 可手动测试。
- 脚本会先查询今日签到状态；已签到的账号会跳过重复签到。
- 多账号会逐个执行；某个账号失败不会阻断后续账号，任一账号失败会让工作流标记为失败。
- 查看 Actions 运行日志可判断是参数失效、接口异常还是配置错误。

## 安全提醒

`kps`、`sign`、`vcode` 以及完整请求 URL 均属于敏感凭证。不要将其粘贴到公开 Issue、代码、日志或截图中。若怀疑泄露，请重新获取凭证。

本项目仅供学习交流。夸克接口可能变化，不能保证第三方签到脚本永久可用。脚本基于开源项目修改，请保留原项目署名与许可信息。
