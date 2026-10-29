# StataImproved 2.0 现代化：审计、架构与交付状态

> 分支 `st4-windows-modernization`，基于 upstream `origin/master`（1502f6e，v1.3.20；2026-10-02 核对，上游无变化）。
> 本文记录这一轮工作的依据、设计取舍、验证证据，以及还需要维护者（或有相应权限/设备的人）完成的事项。
> 本文件和 `tests/`、`tools/` 通过 `.gitattributes export-ignore` 不会进入 Package Control 分发包（已用 `git archive` 生成的发布包实测）。

## 1. 目标与完成定义（DoD）

**目标**：把以 Sublime Text 3 + macOS 为中心的插件，升级为在当前 Sublime Text 4（Python 3.14 插件宿主）下、macOS 与 Windows 都能可靠使用的 Stata 编辑与执行插件；现有 macOS 工作流不明显回归。AI 属于第二阶段（见第 8 节）。

| DoD 项 | 状态 | 证据 / 说明 |
|---|---|---|
| ST4 当前版本（4215）正常加载，运行在 Python 3.14 宿主 | ✅ 已验证 | 真实 ST 4215、**发布包**集成测试 19/19（harness 报告 Python 3.14.6） |
| ST3 / 旧 3.3 宿主仍可用 | ✅ 已验证 | 同一套测试在 3.3.7 宿主下 19/19（真实 ST3 本身未测，见 7.5） |
| 语法高亮、snippets、补全、macro/comment 命令 | ✅ 已验证 | 集成测试：scope、16 个 snippet（与上游逐字节一致，仅修标签笔误）、macro/comment 命令 |
| 当前行 / 选区 / 代码块 / 整个文件 生成正确的 do-file 并执行 | ✅ 已验证 | 单元测试 + 集成测试 + 真 Stata 端到端 |
| **Help / Data Browser 在 Windows 真正打开** | ✅ 已验证（Stata 18） | 真 Stata 中 F1 对应的 `help regress` 弹出查看器窗口，F2 对应的 `browse price mpg` 弹出 `数据编辑器(浏览) - [auto.dta]` |
| 路径、临时文件、未保存文件无平台相关错误（#37 #38 #39） | ✅ 已验证 | 单元测试 + 集成测试；含中文、空格、`é` 的路径用真 Stata 验证 |
| **Windows：代码真正在本机 Stata 中执行** | ✅ 已验证（Stata 18） | 真实 ST 4215 中按命令 → 插件启动 Stata → do-file 约 1 s 内执行；Stata 已运行时直接发送给它 |
| **Windows：Stata 的生命周期不受 Sublime 影响**（不丢数据） | ✅ 已验证 | Sublime 退出 5 s 后 Stata 仍在运行；默认方式不使用 COM（见第 2 节） |
| Windows：无需管理员权限或额外配置 | ✅ | 默认方式不需要 `/Register` |
| macOS：代码真正在 Stata 中执行、无回归 | ⚠️ 已实现，**无 Mac 无法验证** | AppleScript 语义与原版一致（见 7.2 清单） |
| Windows：Stata 18 以外的版本 | ⚠️ 未验证 | 依赖 Stata 窗口结构（见 3 节）；不满足时给出明确提示（见 7.1） |
| Package Control 对 Windows 开放 | ⏳ 外部操作 | 需要向 `wbond/package_control_channel` 提 PR（见 7.3） |
| README / 安装说明 / 新用户安装提示更新到 ST4 + Windows | ✅ | README.md、`messages/install.txt`、`messages/2.0.0.txt` |
| **AI** | ⏳ 第二阶段，未开始 | 只有设计要点（第 8 节），需要维护者定模型服务和数据外发策略 |

## 2. 事实依据（2026-09-26 核验与实测，10-02 复核）

- Sublime Text 稳定版 Build 4215（2026-09-25）；Build 4213（09-21）起内置 Python 3.14 与 3.3，**3.3 默认禁用**。官方 API Environments 文档：禁用 3.3 后“all plugins run under the newer plugin host”，即没有 `.python-version` 的包会自动跑在 3.14 上——不是加载失败。
- `.python-version` 写 `3.8`：4050–4204 选 3.8，4205+ 映射到 3.14（官方文档写明的向后兼容），ST3 忽略该文件用 3.3。写 `3.14` 反而会让 4205 之前的 ST4 退回 3.3。
- 命令名推导：ST 4215 的 `sublime_plugin.split_identifier` 对全部 10 个类名的结果与 keymap 一致（用 4215 自带源码逐一验证）。
- Package Control 频道条目 `"platforms": ["osx"]`，Windows 安装量 0。
- Issue #37–#39（dpc00，2026-09-25）来自对 Package Control 目录的批量审计（同一天向约 35 个仓库提交了 issue），并非 Windows 功能请求；三者均已修复。上游自那之后没有新 issue、PR 或提交。
- **Stata Automation（COM）实测**（本机 Stata 18 MP，以管理员身份执行一次 `/Register` 后测得）：

  | 问题 | 结果 |
  |---|---|
  | 创建对象会启动 Stata；`DoCommand` / `DoCommandAsync`（含带空格和 `é` 的 do-file 路径、`run`、多行 `forvalues`）可用 | 是 |
  | 新对象会连接到用户自己打开的 Stata（不再开第二个） | 是 |
  | **释放对象后，由 COM 启动的 Stata 继续运行** | **否**，立即退出 |
  | **释放对象后，用户自己打开的 Stata 继续运行** | **否**，1 秒内退出；即使数据已修改（`c(changed)=1`）也**不提示保存** |
  | 客户端进程退出但未释放（相当于 Sublime 退出或崩溃） | Stata 约 **11 分钟**后被 Windows 的 COM 垃圾回收关闭 |
  | 用户在持有连接时自己关闭 Stata | 正常退出；插件收到 `RPC_S_SERVER_UNAVAILABLE`，下次发送自动重连 |
  | 官方接口中有“断开但不关闭 Stata”的方法 | 没有 |
  | **创建对象后立刻发送的第一条命令** | **被静默丢弃（8/8）**，不报错；创建后等 3 s 才可靠。线程模型（STA / 加消息循环 / MTA）无关；同步 `DoCommand` 太早调用报 `RPC_E_SERVERFAULT`；`UtilIsStataFree` 轮询不稳定（2/3）；**`UtilStataErrorCode` 由 Stata 主线程应答，轮询到它返回后再发送则 3/3 可靠（0.3 s）**，已采用 |

  结论：**只要通过 COM 连接过，Stata 的生命周期就绑在 Sublime 上**，用户关闭 Sublime 后继续在 Stata 里工作，大约 11 分钟后 Stata 会连同未保存数据一起消失。因此 COM 不能作为默认方式。
- **向 Command 窗口发送输入（默认方式）实测**（Stata 18 MP，中文界面）：

  | 问题 | 结果 |
  |---|---|
  | 正常窗口，连发 12 条 | 12/12，每条约 0.1 s |
  | **最小化窗口，用 `PostMessage` 投递** | **1/12**：只有第一条能用——之前文档里“最小化也可以”的说法是错的（当时只试了一条） |
  | 最小化窗口，改用同步投递（`SendMessageTimeout`） | 12/12；不激活地还原窗口也可以（8/8），但会把用户最小化的 Stata 弹出来，不采用 |
  | **最小化窗口 + 命令里有非 ASCII 字符**（路径含 `é` 或中文） | 只有 1/5、1/5、2/5 能执行（ASCII 路径 5/5；正常窗口含非 ASCII 也是 5/5）。**中文用户名的 Windows 用户，临时目录路径天然含中文，最容易遇到** |
  | 8.3 短路径能否保证纯 ASCII | 不能：实测短名为 `SI中文~1`、`SIÉ5Z~1`，仍含非 ASCII |
  | 用 Stata 宏表达式 ``` `=ustrunescape("\u4e2d\u6587")' ``` 让输入的命令全程 ASCII | 正常/最小化窗口均 5/5（Stata 14+），已采用，只在“最小化且命令含非 ASCII”时启用 |
  | Stata 忙碌时（8 s `sleep` / 8 s 重计算）连发 3 条 | 调用 0.17 s 返回、不阻塞；命令按顺序排队执行 |
  | 焦点 / 半截输入 / Do-file Editor 在最前 | 不抢焦点（用自己控制前台的窗口验证）；Command 窗口里没敲完的内容被 Esc 清空；Do-file Editor 的文本始终为空 |
  | Command 窗口的只读标志 | 空闲、忙碌时都是 0，应答在毫秒级，可用作窗口识别校验 |
  | 用户手动启动 Stata 后约 0.15 s 内发送 | 修复前：判定“没有 Stata”，**再启动第二个 Stata**；修复后：发现进程存在就等它的窗口出现 |
  | 多个 Stata | 命令发给窗口 Z 序最上面的那个：启动后在最上面者拿到命令；用真实激活切换到 A 后 A 拿到命令（第二次切回 B 被系统前台锁拒绝，无法测）。**最小化的窗口在 Z 序里排在后面** |
- Windows 构建系统（Ctrl+B，用系统关联程序打开 `.do`）：路径含空格和 `é` 实测在 Stata 的 Do-file Editor 中打开。

## 3. 架构

```text
StataImproved.py            编辑器命令（只关心“发什么”，不关心平台）
        │  execution.execute(code, kind, mode, activate)
        ▼
stata_improved/execution.py 写唯一的临时 do-file → 组装 `do "path"` / `run "path"` → 选择后端
        │
   ┌────┴──────────────────────────────┐
   ▼                                   ▼
backend_macos.py                    backend_windows.py（后台线程，按顺序发送）
后台线程 + osascript（stdin）        ├─ "window"（默认）→ stata_window.py：向 Command 窗口发送窗口消息
tell application id                 └─ "automation"（可选）→ wincom.py（ctypes IDispatch）
  "com.stata.stataNN"
stata_improved/text.py      纯文本逻辑（macro/comment 切换、代码块边界），无 Sublime 依赖，便于测试
```

关键取舍：

1. **命令名不变**。keymap、菜单、用户自定义快捷键都引用命令名，全部保持（`lines_to_stata`、`piu_sign` 等）。
2. **Windows 默认：把命令“打”进 Stata 的 Command 窗口**（`stata_window.py`）。Stata 18 的 Command 窗口是停靠面板（`XTPDockingPane…`）里的 Scintilla 控件。插件向它同步发送（`SendMessageTimeout`，原因见第 2 节）：Esc（Stata 自己的“清空命令窗口”）、每个 UTF-16 单元一个 `WM_CHAR`、Enter。
   - 选择窗口：Stata 进程用 Toolhelp 枚举（不需要进程句柄，管理员权限的 Stata 也看得到）；只认停靠面板里**可写**的 Scintilla——Do-file Editor 也是 Scintilla，但在独立顶层窗口里，不会被打字进去；多个 Stata 取 Z 序最上面且有 Command 窗口的那个。
   - 没有 Stata：启动已安装的最新版本（或 `stata_path`，支持 `~` 和 `%VAR%`），像双击一样启动并尽量脱离 Sublime 的作业对象，Sublime 退出后 Stata 继续运行（已实测）。**已有 Stata 进程但窗口还没出来**（刚启动）：最多等 20 秒，而不是再启动一个。
   - 错误提示：Stata 以管理员运行（Windows 禁止低权限程序向高权限窗口发输入）、输入队列满、Stata 无响应、找不到 Command 窗口——各有明确文字，不再统一报“窗口消失”。
   - 风险：依赖 Stata 窗口的内部结构，只在 Stata 18 上验证过。
3. **COM（Stata Automation）保留为可选方式**（`"windows_method": "automation"`），用 ctypes 手写的最小 IDispatch 客户端（Sublime 内嵌 Python 没有 pywin32）。因为 single-use 语义（每个新对象就是一个新 Stata），对象只创建一次，放在一个常驻线程上，插件重载后复用；创建后先用 `UtilStataErrorCode` 等 Stata 就绪再发送（否则第一条命令丢失）；Stata 被关闭后下次发送自动重连。README、设置文件注释和本节都写明了第 2 节的数据丢失风险。
4. **每次发送一个新的临时 do-file**（`%TEMP%/StataImproved/selection_xxxx.do`，UTF-8），超过 24 小时的自动清理。原版固定文件名在 Stata 忙时排队的两个命令会互相覆盖。路径统一用正斜杠并加引号，兼容带空格的目录，也避免 Stata 把 `\` + `` ` ``/`$` 当作转义。旧版散落在临时目录上一级的固定名文件在插件加载时清理。
5. **macOS 后端保持原 AppleScript 语义**：`tell application id "com.stata.stataNN"` + `DoCommandAsync "…" with addToReview`，Help/Browse 时 `activate`；`osascript` 的调用方式与原版相同（无参数、脚本走 stdin，只是不经过 shell）。变化：命令字符串做 AppleScript 转义、版本探测扩展到 11–30（避免每出一个新 Stata 版本就要发一次更新，#23 #36 都是这类）并可在设置中固定版本（#34）、删除了无效的 `tell application "Viewer"`；发送改在后台线程按顺序执行（原版在 UI 线程同步等待 osascript，首次授权弹窗或 Stata 启动慢时会卡住编辑器）。
6. **保持 Python 3.3 语法兼容**（无 f-string、无类型注解），ST3 的 macOS 用户继续可用；集成测试在 3.3 宿主下验证。

## 4. 相对 1.3.x 的行为变化（请维护者确认）

| 变化 | 原因 |
|---|---|
| 所有快捷键只在 Stata 文件（`source.stata`）中生效 | #30：在 R 文件中按 Cmd+Enter 也被发到 Stata；原来 Ctrl+S、F5、Ctrl+= 在任何文件里都被占用 |
| `$` 只在有选区时包裹为 `${…}`；无选区时正常输入 `$` | #21 #27 #25：原来空行输入 `$` 没反应、`if $` 变成换行的 `${}`、单字符变量报错 |
| Cmd+/（Windows Ctrl+/）无选区时用 `//` 注释整行；有选区时仍是 `/* */` 切换 | #28 #32；新增 `Comments.tmPreferences` |
| 分隔线文字改为 `(by Stata Improved Editor (piu_sign) )`，旧文字（含 “for macOS”）仍被识别 | 平台中立；识别只依赖 `piu_sign` |
| 代码块执行：最后一个分隔线之后的块可以执行；光标在分隔线上时执行其下方的块 | 原实现依赖 -64/+15 的魔法偏移，最后一块会选错范围 |
| 多个选区之间用换行连接；两个光标在同一行时该行只发一次 | 原来直接拼接，多选区会拼成一行 |
| Help/Browse 不再执行 `tell application "Viewer"` | 该应用不存在，只会产生 AppleScript 错误 |
| Windows：发送代码前 Command 窗口里没敲完的内容会被清空（Esc） | 否则会和发送的命令拼在一起 |
| 旧设置文件 `StataImproved (OSX).sublime-settings`（内容未被使用）改为跨平台的 `StataImproved.sublime-settings` | 设置项：`stata_version`、`temp_directory`、`windows_method`、`stata_path`、`windows_progid` |
| `pictures/`（约 10 MB）不再进入安装包 | README 用 raw.githubusercontent 链接引用，不受影响 |

**Windows 快捷键的取舍**（依据 ST 4215 自带的 `Default (Windows).sublime-keymap` 逐一查冲突）：Ctrl+D / Ctrl+R / Ctrl+Shift+D 与 Stata 自带 Do-file Editor 一致，但在 Stata 文件中会覆盖 Sublime 的 Quick Add Next（多选，正好是 #26 里用户想要的功能）/ Goto Symbol / Duplicate Line——**这是一个需要维护者拍板的取舍**：要么保持与 Stata Do-file Editor 和 macOS 一致，要么让出 Ctrl+D 给多选（可在 Key Bindings 里改，README 已说明）。Ctrl+S 是保存，所以分隔线用 Ctrl+K, Ctrl+S；Ctrl+` 是控制台、Ctrl+= 是放大字体，所以 word→`` `word' `` 用 Alt+`，reindent 在 Windows 上不绑定。F2 在 Stata 文件里仍绑定 Browse，覆盖 Sublime 的 next_bookmark（#29 #19，未改）。

## 5. 意图与问题逐条对照

### 5.1 第一轮仓库审计发现的 8 类问题

| 问题 | 状态 |
|---|---|
| 临时 do-file 路径缺分隔符（#39） | ✅ 已修复（`tempfile.mkstemp` + 独立目录，每次唯一） |
| 未保存的标签页 `os.path.dirname(None)`（#38） | ✅ 已修复（该死代码已删除） |
| 单字符/空词导致 `IndexError`（#37），`[3:-3]` 假设有空格 | ✅ 已修复（纯函数 + 单元测试） |
| `PiuSign` 的 `-64/+15` 魔法偏移、最后一块选错 | ✅ 已修复（`block_bounds`） |
| 多选区拼接 / 无选区只发最后一个光标所在行 | ✅ 已修复（含同行去重） |
| 配置不一致：`.gitignore` 忽略 `*.py`、`messages.json` 只登记到 1.3.3 且 1.1.1 指错文件、`install.txt` 写着 “for mac users”、未使用的设置项、16 个 snippet 的 XML 笔误 | ✅ 全部修复（`messages.json` 登记全部 18 个版本；`install.txt` 改为跨平台） |
| 调试 `print` | ✅ 已删除 |
| 版本选择（#34）、多个 Stata | ✅ macOS `stata_version`；Windows `stata_path` + “最近使用的窗口” |

### 5.2 上游全部 26 个未关闭 issue

| Issue | 主题 | 状态 |
|---|---|---|
| #37 #38 #39 | `IndexError` / 未保存文件 / 临时路径 | ✅ 已修复 |
| #36 | 支持 Stata 19 | ✅ 版本探测 11–30（macOS 无法实机验证） |
| #34 | 选择 Stata 版本 | ✅ `stata_version` 设置 |
| #32 / #28 | Cmd+/ 无选区时用 `//` 注释整行 | ✅ |
| #30 | 在 R 文件中 Cmd+Enter 被发到 Stata | ✅ 快捷键限定在 Stata 文件 |
| #27 / #21 | 单独输入 `$` 无反应；`if $` 变成换行的 `${}` | ✅ 只在有选区时才包裹 |
| #25 | `$m` 单字符失败 + 选中半行也应整行执行 | ✅ 前一半；❌ 后一半（部分选中整行执行）未做 |
| #18 | “doesn’t work with sublime4?”（2020） | ✅ 本次工作的核心：4215 / Python 3.14 实测通过 |
| #8 | ctrl+r 静默执行 | ✅ 早已实现（1.3.3） |
| #35 | 给语法高亮添加新命令 | ❌ 未做（需要改 `Stata.tmLanguage`） |
| #29 / #19 | F2 与 Sublime 书签冲突 | ❌ 未改（仍绑定 F2） |
| #24 | Cmd+` 与 macOS 窗口切换冲突 | ❌ 未改 |
| #20 | 执行整个文件时自动 `cd` 到 do-file 目录 | ❌ 未做 |
| #17 | Atom 版 | ❌ 范围之外 |
| #10 | Linux 支持 | ❌ 未做（执行层已留出后端接口） |
| #9 | 把局部宏当宏而不是字符串高亮 | ❌ 未做 |
| #26 | 多选同名变量 | ℹ️ Sublime 自带功能；注意 Windows 上 Ctrl+D 在 Stata 文件中被占用（见第 4 节） |
| #31 | 自定义 snippet 不生效 | ℹ️ 用户自己的 snippet 问题，非插件缺陷 |
| #16 / #14 | “No version of Stata found” / 如何配置 | ℹ️ macOS 相关，无法实机验证；README 已更新 |
| #3 | 逐行发送时局部宏消失 | ℹ️ 上游维护者已结论：与 Stata 官方 Do-file Editor 行为一致，非缺陷 |

小结：26 个里，已解决 13 个（#37 #38 #39 #36 #34 #32 #28 #30 #27 #21 #18，加上早已实现的 #8，以及只解决了前一半的 #25），明确没做 8 个（#35 #29 #19 #24 #20 #17 #10 #9），其余 5 个是说明性/非缺陷（#26 #31 #16 #14 #3）。

### 5.3 本轮审计（对照意图复查）发现并修复的问题

| # | 问题 | 怎么发现的 | 修复 |
|---|---|---|---|
| 1 | **新用户安装提示仍是 “for mac users … macOS Catalina”** | 静态核对发布信息文件 | `install.txt` 改为跨平台；`messages.json` 补全 |
| 2 | **Windows 最小化的 Stata 只有第一条命令能执行（1/12）**；文档里“最小化也可以”是错的 | 对真 Stata 重复测量 | 改为同步投递（12/12）；回归测试 |
| 3 | **最小化 + 路径含非 ASCII（中文用户名）命令丢失**（1/5） | 路径字符集对照实验 | 只在该情形下用 `ustrunescape()` 让输入全程 ASCII（5/5）；单元测试 + 真 Stata 回归测试 |
| 4 | 用户手动启动 Stata 后立刻发送 → 再启动**第二个 Stata** | 真 Stata 竞态实测 | 发现 Stata 进程就等它的窗口（最多 20 s） |
| 5 | **可选的 automation 方式：连接后第一条命令被静默丢弃（8/8）** | 重构后对真 Stata 再测 | 用 `UtilStataErrorCode` 等 Stata 就绪；真 Stata 回归测试 |
| 6 | Stata 以管理员运行 → 报“窗口消失”（误导） | 独立代码审查 | 明确提示；用 Toolhelp 识别进程 |
| 7 | 启动中的 Stata（只有闪屏）→ 误导性报错并建议改用有数据丢失风险的 automation | 独立代码审查 | 等待；错误提示附带该方式的风险 |
| 8 | 文档与实际不符：“最近使用”（实际是 Z 序，最小化排最后）、“支持 13–19”（Windows 只验证 18）、#25 整体算解决、`Windows (Stata Automation)` 的旧描述、命令面板名称 | 文档逐句核对 | 全部更正 |
| 9 | `start()` 的超时叠加、Python 3.3 下子进程继承句柄、要求提权的 Stata 报裸错误、EnumWindows 回调异常可能吞掉枚举、`stata_path` 不展开 `~`/`%VAR%` 且报错不准 | 独立代码审查 | 全部修复 |
| 10 | 同一行两个光标把该行发两次 | 通读代码 | 去重 + 测试 |
| 11 | macOS `osascript -`（与原版调用形式不同，无法在 Mac 上验证） | 风险评估 | 改回与原版相同的调用形式 |
| 12 | 菜单/命令面板里的 “Register Stata Automation” 太显眼，让人以为必须注册 | 通读 | 标注 `(Windows, optional)` |

## 6. 验证证据

| 层次 | 内容 | 结果 |
|---|---|---|
| 单元测试 `cd tests && python -m unittest` | 文本逻辑、全部命令（含 #37/#38/#39 回归）、临时文件、macOS 后端（osascript 替身，含“不阻塞调用方”）、Windows 两种方式（`send()` 的各种场景、Command 窗口选择、UTF-16 编码、`ascii_command`、错误提示、COM 复用/断线重连/就绪等待）、ctypes COM 客户端 | 77 个，72 个常规 + 5 个需真 Stata |
| 真 Stata 测试 `STATA_IMPROVED_REAL_STATA=1` | 启动并执行（路径含空格与 `é`）、再发给已运行的 Stata、**用户刚启动 Stata 时立刻发送不开第二个**、**最小化 + 中文路径连发 4 条**、**含中文的代码经执行层端到端**、**automation 首条命令**；每个测试结束时关闭它启动的 Stata | 77/77 通过（5 个真机测试均执行，无跳过） |
| 真实 ST 集成 `python tools/run_sublime_integration.py <便携版ST目录> [--host33]` | 插件加载、命令注册名、资源文件、设置、语法 scope、编辑命令、snippet、执行命令产生的 do-file；**在 Sublime 中按命令 → Stata 启动并执行代码 → Sublime 退出后 Stata 仍在运行**（runner 结束时关闭 Stata） | 用 `git archive` 生成的**发布包**：Python 3.14.6 宿主 19/19；Python 3.3.7 宿主 19/19 |
| 真 Stata 行为审计（一次性脚本，不入库） | 焦点、半截输入、忙碌排队顺序、最小化连发、Help/Browse 窗口、Do-file Editor、多实例 | 全部通过（多实例“把 A 提到最前”一项因跨进程重排 Z 序不生效而测不了，改用真实窗口激活验证） |
| 编译 | `python -W error` 全部通过；AST 检查无 3.3 不支持的语法 | 通过 |
| 独立代码审查 | 两轮：第一轮（COM 阶段）5 条，第二轮（窗口消息方案）8 类 | 有效意见全部采纳并补测试；第 2 轮另有一条“最近使用”的文档与实现不符，已更正 |

## 7. 仍需完成的事项

### 7.1 Windows：其他 Stata 版本

默认方式依赖“Command 窗口是停靠面板中的可写 Scintilla 控件”。只在 Stata 18（MP，中文界面）上验证过。有 Stata 16/17/19 的机器时，先关闭所有 Stata，再运行：

```
set STATA_IMPROVED_REAL_STATA=1
cd tests && python -m unittest -v test_windows.RealStataTest
```

（测试会自己启动并关闭 Stata。）若失败，插件会提示找不到 Command 窗口，同时需要为该版本调整 `stata_window.py` 的窗口识别。

开发机上为测试注册过 Stata 18 的 Automation（默认方式用不到它）。如需撤销：以管理员身份运行 `"C:\Program Files\Stata18\StataMP-64.exe" /Unregister`。

### 7.2 macOS 回归测试清单（需要一台装有 Stata 的 Mac）

- [ ] Ctrl+D：当前行、选区、多选区；Stata Review 窗口出现命令
- [ ] Ctrl+R：静默执行
- [ ] Ctrl+Shift+D：第一块 / 中间块 / 最后一块 / 无分隔线时整个文件；旧分隔线文字仍被识别
- [ ] Ctrl+S 插入分隔线；F1 Help 并切到 Stata；F2 Browse
- [ ] 装有多个版本时默认发到最新版本；设置 `"stata_version": 17` 后发到 17；没装 Stata 时提示 “No version of Stata found.”
- [ ] 在 `.R` / `.py` 文件中 Ctrl+D、Cmd+Enter 恢复 Sublime 默认行为
- [ ] 未保存的新标签页可执行；`$TMPDIR/StataImproved/` 下生成临时文件
- [ ] 第一次发送时系统弹出“允许控制 Stata”授权框期间，Sublime 不应卡住（发送已放到后台线程）

（`tools/run_sublime_integration.py` 依赖 Windows/Linux 的便携版数据目录；macOS 版 Sublime 没有便携模式，Mac 上目前以手工清单为准。）

### 7.3 发布（对外操作，需维护者执行或授权）

1. 合并分支，打 tag `v2.0.0`（Package Control 按 tag 发布）。
2. 向 `wbond/package_control_channel` 提 PR，把 `repository/s.json` 中的条目改为：

   ```json
   {
     "name": "Stata Improved Editor",
     "details": "https://github.com/zizhongyan/StataImproved",
     "labels": ["language syntax", "stata"],
     "releases": [
       { "sublime_text": "*", "platforms": ["osx", "windows"], "tags": true }
     ]
   }
   ```
3. GitHub 仓库描述 “Improved Stata Editor for macOS : a sublime text 3 plugin” 改为跨平台描述（Package Control 页面显示的就是它）。
4. 回复并关闭 #37 #38 #39，以及 #21 #27 #28 #32 #30 #34 #36（见 5.2）。

### 7.4 可以后续再做（未纳入本轮，见 5.2）

- #20：执行整个文件时自动 `cd` 到 do-file 所在目录（可做成设置项）。
- #25 后一半：部分选中一行时按整行执行（与 Stata Do-file Editor 行为一致）。
- #24：Cmd+` 与 macOS 窗口切换冲突（考虑换键）；#29/#19：F2 与书签冲突；#9 / #35：语法高亮。
- `temp_directory` 设置成含 `"` 的路径时 `do "…"` 会失败（可改用 Stata 复合引号 `` `"…"' ``）。
- Windows 上 F1/F2 不会把 Stata 窗口切到前台（Windows 不允许后台进程可靠地把别的程序切到前台）。
- Linux 支持（执行层已留出后端接口；Linux 上可用 `xdotool` 或 Stata console 方案）。

### 7.5 已知但没有条件验证的部分（诚实清单）

- **macOS 的全部执行路径**（无设备）。
- **Stata 18 以外的 Windows 版本**，包括 Stata 13 上“最小化 + 非 ASCII 路径”会因缺少 `ustrunescape()` 报 Stata 错误。
- **以管理员运行的 Stata**：只用替身测了错误提示，没有真的提权运行 Stata。
- 窗口在其他虚拟桌面、被系统托盘隐藏等状态；Stata 弹出模态对话框时的行为。
- **Windows 10**（只在 Windows 11 上测）、**真正的 Sublime Text 3**（只测了 ST 4215 里的旧 Python 3.3 宿主）。
- 同一机器上杀毒软件对 `SendMessage`/`CREATE_BREAKAWAY_FROM_JOB` 的反应。

## 8. AI（第二阶段）设计要点

AI 接入建议在本轮合并、双平台验证之后再启动。与本轮架构的衔接点：

- **复用执行层**：AI 生成或修改的代码，经 `execution.execute()` 发送，无需关心平台。
- **读取 Stata 输出是前提**：窗口消息、AppleScript 都拿不到结果窗口内容（COM 的 `MacroValue` 等只能取宏和返回值）。可行做法是在临时 do-file 外包一层 `log using "<tmp>.log", text replace` … `log close`，插件读取日志文件，用于“解释结果 / 诊断报错 / 修复后重跑”的闭环。
- **建议的最小可用版本**：选中代码 →“AI Explain / AI Fix”命令 → 结果显示在 Sublime 输出面板；API Key 放在用户设置中，默认关闭，并明确告知代码会发送到外部服务。
- 需要维护者决定：使用哪家模型服务、是否允许把数据或输出内容发送出去（研究数据的保密要求）。
