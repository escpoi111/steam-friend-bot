# Steam 自动加好友程序

一个简单的 Steam 自动加好友工具。支持批量导入好友代码，自动发送好友请求，并可设置排除列表来跳过不需要添加的好友。

**提供图形界面(GUI)版本，可打包为 EXE 直接运行，无需安装 Python！**

## 功能

- ✅ **傻瓜式图形界面** - 无需命令行操作
- ✅ 批量导入多个 Steam 好友代码
- ✅ 自动发送好友请求
- ✅ 支持排除列表（选择哪些好友不需要添加）
- ✅ 自动跳过已是好友的用户
- ✅ 支持好友代码和 SteamID64 两种格式
- ✅ 请求间自动延迟，避免触发 Steam 限制
- ✅ 实时运行日志
- ✅ **一键打包为 EXE**

## 快速开始

### 方式一：图形界面版（推荐，傻瓜式操作）

#### 直接运行

```bash
pip install -r requirements.txt
python steam_friend_bot_gui.py
```

#### 打包为 EXE（Windows）

双击 `build.bat` 即可自动打包，生成的 EXE 在 `dist/SteamFriendBot.exe`。

或手动执行：

```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name SteamFriendBot steam_friend_bot_gui.py
```

打包完成后，直接双击 `dist/SteamFriendBot.exe` 运行，无需安装 Python。

#### GUI 使用步骤

1. 首次可点击「从本地配置加载」自动填入 Steam 配置信息（API Key、SteamID64、Session ID、Cookies）
2. 在「好友代码」区域粘贴好友代码，或点击「从文件导入」
3. (可选) 在「排除列表」区域填入不需要添加的好友
4. 点击「🚀 开始添加好友」
5. 在日志区域实时查看进度

---

### 方式二：命令行版

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置本地配置（推荐）

程序会按以下顺序读取本地配置，后者会覆盖前者：

1. 可选 JSON 配置文件（默认 `steam_friend_bot.local.json`，可通过 `STEAM_CONFIG_PATH` 改路径）
2. `.env`
3. 当前 shell 环境变量

你可以继续只使用 `.env`，也可以把长期复用的内容写进本地 JSON 文件。

#### 方式 A：使用 `.env`

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

需要配置：
- `STEAM_API_KEY` - Steam Web API 密钥（[获取地址](https://steamcommunity.com/dev/apikey)）
- `STEAM_ID` - 你的 SteamID64（[查询地址](https://steamid.io/)）
- `STEAM_SESSION_ID` - 从浏览器 Cookie 中获取的 sessionid
- `STEAM_COOKIES` - 从浏览器中获取的 Steam cookies（至少要包含 `steamLoginSecure`，`sessionid` 会自动复用 `STEAM_SESSION_ID`）

#### 方式 B：使用本地 JSON 文件

复制 `steam_friend_bot.local.example.json` 为 `steam_friend_bot.local.json`，填写后即可被 GUI 和命令行版共同复用：

```bash
cp steam_friend_bot.local.example.json steam_friend_bot.local.json
```

示例：

```json
{
  "api_key": "your_steam_api_key_here",
  "steam_id": "76561198012345678",
  "session_id": "your_session_id_here",
  "cookies": "steamLoginSecure=your_steam_login_secure_cookie_here",
  "add_delay_seconds": 5,
  "friend_codes_file": "friend_codes.txt",
  "exclude_file": "exclude_list.txt"
}
```

说明：
- 本地 JSON 文件已加入 `.gitignore`，不会默认提交
- `cookies` 里只放 `steamLoginSecure` 也可以，程序会自动把 `session_id` 写入请求 cookie
- `friend_codes_file` 与 `exclude_file` 会被 GUI 启动时自动读取

### 3. 准备好友代码文件

创建 `friend_codes.txt` 文件，每行一个好友代码：

```
123456789
1234-5678-9012
76561198012345678
```

### 4. (可选) 设置排除列表

创建 `exclude_list.txt` 文件，将不需要添加的好友代码放入：

```
987654321
```

### 5. 运行程序

```bash
python steam_friend_bot.py
```

## 好友代码格式

支持以下格式：
- 纯数字好友代码: `123456789`
- 带分隔符好友代码: `1234-5678-9012`
- SteamID64: `76561198012345678`

## 如何获取 Cookies

1. 在浏览器中登录 [Steam 社区](https://steamcommunity.com)
2. 按 F12 打开开发者工具
3. 切换到「应用」(Application) 标签
4. 在左侧找到 Cookies -> `https://steamcommunity.com`
5. 复制 `sessionid` 的值填入 `STEAM_SESSION_ID`
6. 复制 `steamLoginSecure` 的值填入 `STEAM_COOKIES`；如果你愿意，也可以写成 `steamLoginSecure=xxx; sessionid=xxx`

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `STEAM_API_KEY` / `api_key` | Steam Web API 密钥 | 必填 |
| `STEAM_ID` / `steam_id` | 你的 SteamID64 | 必填 |
| `STEAM_SESSION_ID` / `session_id` | Steam sessionid | 必填 |
| `STEAM_COOKIES` / `cookies` | Steam cookies（至少含 `steamLoginSecure`） | 必填 |
| `ADD_DELAY_SECONDS` | 添加好友间隔秒数 | 5 |
| `FRIEND_CODES_FILE` | 好友代码文件路径 | friend_codes.txt |
| `EXCLUDE_FILE` | 排除列表文件路径 | exclude_list.txt |
| `STEAM_CONFIG_PATH` | 本地 JSON 配置文件路径 | `steam_friend_bot.local.json` |

## 本地配置校验

- GUI 启动时会自动尝试读取本地配置，并可手动点击「从本地配置加载」
- GUI 和命令行版现在使用同一套本地配置解析逻辑
- 如果缺少 API Key、SteamID64、Session ID、Cookies，或格式不合法，程序会明确提示对应字段
- Cookies 缺少 `steamLoginSecure` 时会直接提示，而不是等到发送请求时才失败

## 注意事项

- Steam 对添加好友有频率限制，建议不要将延迟设置得太低
- 请确保你的 Steam cookies 是有效的（未过期）
- 程序运行日志会保存在 `steam_friend_bot.log` 文件中