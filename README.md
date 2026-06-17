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

1. 填写 Steam 配置信息（API Key、SteamID64、Session ID、Cookies）
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

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

需要配置：
- `STEAM_API_KEY` - Steam Web API 密钥（[获取地址](https://steamcommunity.com/dev/apikey)）
- `STEAM_ID` - 你的 SteamID64（[查询地址](https://steamid.io/)）
- `STEAM_SESSION_ID` - 从浏览器 Cookie 中获取的 sessionid
- `STEAM_COOKIES` - 从浏览器中获取的 Steam cookies

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
6. 复制 `steamLoginSecure` 和 `sessionid` 的值，格式为 `steamLoginSecure=xxx; sessionid=xxx` 填入 `STEAM_COOKIES`

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `STEAM_API_KEY` | Steam Web API 密钥 | 必填 |
| `STEAM_ID` | 你的 SteamID64 | 必填 |
| `STEAM_SESSION_ID` | Steam sessionid | 必填 |
| `STEAM_COOKIES` | Steam cookies | 必填 |
| `ADD_DELAY_SECONDS` | 添加好友间隔秒数 | 5 |
| `FRIEND_CODES_FILE` | 好友代码文件路径 | friend_codes.txt |
| `EXCLUDE_FILE` | 排除列表文件路径 | exclude_list.txt |

## 注意事项

- Steam 对添加好友有频率限制，建议不要将延迟设置得太低
- 请确保你的 Steam cookies 是有效的（未过期）
- 程序运行日志会保存在 `steam_friend_bot.log` 文件中