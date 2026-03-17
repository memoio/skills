# DataDid 签到技能

用于 Agent 的 DataDid 认证与每日签到技能。支持邮箱+验证码登录、DataDID 积分签到和 AliveCheck。

**GitHub**：[memoio/skills](https://github.com/memoio/skills) | [English](../README.md)

---

## 安装

### 环境要求

- Python 3.6+
- Claude-cli

### 克隆并安装

```bash
# 克隆 skills 仓库
git clone https://github.com/memoio/skills.git
cd skills

# 复制 datadid-checkin 到 Claude 技能目录
mkdir -p ~/.claude/skills
cp -r datadid-checkin ~/.claude/skills/
```

若只针对某个项目使用，可复制到 `项目路径/.claude/skills/`。

---

### 通过Claude安装

您可以启动Claude，并直接和Claude对话进行安装

```bash
# 启动Claude
claude

# 直接和Claude对话安装
帮我安装https://github.com/orgs/memoio/skills仓库中的的所有skill
```

## 使用说明

安装成功后，您可以直接和agent对话：

- "帮我使用alice@example.com在DataDid上登陆"
- "展示我的DataDid信息"
- "检查我的AliveCheck状态"
- "帮我在DataDid上签到"
- "帮我完成AliveCheck签到"

### 使用命令行

您也可以使用命令行运行脚本，命令在技能目录（`~/.claude/skills/datadid-checkin/`）下执行。路径均为相对该目录。

### 登录

**邮箱 + 验证码**（推荐）：

```bash
# 1. 发送验证码
python scripts/login.py send_code example@example.com

# 2. 使用验证码登录（收到邮件后）
python scripts/login.py login example@example.com 123456
```

**手动保存 token**（已有 access_token 和 refresh_token 时）：

```bash
python scripts/token_helper.py save <ACCESS_TOKEN> <REFRESH_TOKEN>
```

Token 保存在 `~/.config/datadid/tokens.json`。

### 签到

**DataDID 积分签到**：

```bash
python scripts/checkin.py
```

**AliveCheck 签到**：

```bash
python scripts/alive_checkin.py checkin
# 可选：带坐标
python scripts/alive_checkin.py checkin 31.2304 121.4737
```

### 状态

**检查是否已登录**：

```bash
python scripts/token_helper.py check
```

**AliveCheck 状态**（订阅、今日是否签到、连续签到天数）：

```bash
python scripts/alive_checkin.py status
```

**AliveCheck 资料**（昵称）：

```bash
python scripts/alive_checkin.py profile
```

### DataDid 信息

汇总用户资料、今日积分签到状态和 AliveCheck 状态：

```bash
python scripts/datadid_info.py
```

---

## 脚本说明


| 脚本                         | 用途                                       |
| -------------------------- | ---------------------------------------- |
| `scripts/login.py`         | 邮箱 + 验证码登录（`send_code`、`login`）          |
| `scripts/token_helper.py`  | Token 检查、保存、获取；过期时自动刷新                   |
| `scripts/checkin.py`       | DataDID 积分签到                             |
| `scripts/alive_checkin.py` | AliveCheck：`checkin`、`status`、`profile`  |
| `scripts/datadid_info.py`  | 聚合 DataDid 信息（用户资料、今日积分签到、AliveCheck 状态） |


---

## 环境变量


| 变量                         | 默认值                                               | 说明                         |
| -------------------------- | ------------------------------------------------- | -------------------------- |
| `DATADID_BASE_URL`         | `https://data-be.metamemo.one`                    | DataDID API 基础地址           |
| `DATADID_SOURCE`           | `Agent`                                           | 登录来源标识                     |
| `DATADID_USER_AGENT`       | 类 Chrome UA                                       | 被 Cloudflare 拦截时可覆盖（如 403） |
| `DATADID_CHECKIN_URL`      | `https://data-be.metamemo.one/v2/data/record/add` | 签到接口地址                     |
| `DATADID_RECORD_ACTION_ID` | `70`                                              | 积分签到 action ID             |
| `ALIVECHECK_BASE_URL`      | `http://localhost:8081`                           | AliveCheck 服务地址            |
| `ALIVECHECK_LATITUDE`      | -                                                 | AliveCheck 可选纬度            |
| `ALIVECHECK_LONGITUDE`     | -                                                 | AliveCheck 可选经度            |


---

## API 参考

- [DataDID API Docs](https://memolabs.gitbook.io/datadid-developer-platform/en/api)
- [MemoLabs](https://memolabs.org)
- [Sample Code](https://github.com/memoio/call-datadid-demo)

