# 企信查 更新日志

## v1.4.0（2026-07-20）

### 👤 作者署名统一
- 全部作者署名统一为 **文强哥 / Johnny520**（GitHub: Johnny520）：README 作者/版权段落、各 `.py` 文件顶部署名注释、设置/关于界面开发者署名、`config.json` 的 `author` 字段。
- 新建 `LICENSE`（MIT License，版权人 文强哥 (Johnny520)，年份 2026）。
- 包名 `com.qxx.johnny`、模块名、应用标识性字符串保持不变（Buildozer 兼容）。

### 🔧 修复 / 健壮
- 网络请求加入**超时 + 指数退避重试**：`data_sources._get`（配置类 API，默认重试 2 次）、`scraper._get`（兜底抓取，默认重试 1 次，快速失败），瞬时网络故障自动重试，避免单次超时直接失败。
- 修复设置页「请求超时 / 缓存有效期」默认值与配置不一致的问题（超时 10→12、缓存天数 30→3，与 `DEFAULT_CONFIG` 对齐）。
- 强化 `main.py` 中 `legal` 模块导入失败时的兜底对象（补充 `GITHUB` / 统一署名），避免关于页崩溃。

### 📐 合规 / 文档
- `legal.py` 免责声明新增**「合规使用限制」**专章：明确禁止商业牟利、批量抓取、侵犯权益、严肃场景滥用、规避反爬、违规频率等，并强调数据仅供参考、不构成专业意见。
- README 重构为清晰结构（作者/版权、功能、用法、数据来源、自定义 API、爬虫兜底、合规与免责、打包说明、工程结构），修正「粉系 UI」为实际「蓝系 UI」表述。

### 📦 构建
- 版本号 1.3.0 → 1.4.0（buildozer.spec 与关于页同步）。

---

## v1.3.0（2026-07-15）

### 功能补齐与稳定性
- 补齐「修复中心 / 关注 / 对比」页面。
- 修复安装后闪退：移除 `ScreenManager` 中正在显示 Screen 的 `remove_widget`，改为 `clear_widgets()` + 重建 UI。
- 修复字体缺失时 `font_name=None` 导致的初始化崩溃（`_font_kw()` 安全处理）。
- 全自适应布局与空状态引导；Release 自动附带更新描述。

---

## v1.2.0（2026-07-09）

### 🔧 修复
- **修复 APP 安装后闪退问题**：移除 ProfileScreen 中的 `self.manager.remove_widget(self)` 调用（正在显示的 Screen 不能被 ScreenManager 移除，会导致 Kivy 崩溃），改为 `clear_widgets()` + `_build_ui()` 安全重建 UI
- **修复 font_name=None 导致崩溃**：当字体文件不存在时，`CuteButton`/`CuteInput` 的 `font_name` 会被设为 None，导致 Button 初始化异常。新增 `_font_kw()` 安全函数，仅在字体文件存在时才设置 `font_name`

### 📐 布局自适应
- **所有弹窗自适应屏幕尺寸**：信息弹窗、确认弹窗、编辑弹窗、首次启动弹窗等，全部改为 `size_hint=(None, None)` + 动态计算 `size`，根据 `Window.width/height` 自动适配不同手机屏幕
- **所有 Label 文字自适应宽度**：使用 `text_size` + `bind(width)` 让文字自动换行，不会溢出或截断
- **搜索页/关注页/对比页空状态**：添加空状态引导提示，界面不再显示空白

### 🎨 UI 改进
- **蓝系配色方案**：全局统一为蓝色系配色，视觉风格一致
- **底部 4Tab 导航栏**：搜索、关注、对比、设置四个 Tab 页，安全触摸事件处理
- **设置页列表式布局**：ProfileScreen 改为清晰的列表式设置项
- **独立配置页**：ApiConfigScreen 和 CustomConfigScreen 作为独立 Screen，配置更清晰
- **新增 `edit_popup()` 组件**：单字段编辑弹窗，复用性强

### 📦 构建
- **构建模式改为 debug**：`buildozer android release` 只生成 AAB（无法直接安装），改回 `buildozer android debug` 确保 APK 可直接安装到手机
- **APK 文件名去除 debug 标记**：构建后自动重命名，去掉 `-debug` 后缀
- **Release 自动附带更新描述**：从 CHANGELOG.md 读取对应版本说明，自动写入 GitHub Release

---

## v1.1.0（2026-07-08）

### 初始版本
- 企业搜索、关注、对比基本功能
- 基础 UI 布局
