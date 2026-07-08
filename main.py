# -*- coding: utf-8 -*-
"""企信查 - 天眼查风格企业信息查询 App (Kivy)。
蓝系配色 + 底部4Tab导航 + 列表式设置页 + 空状态引导 + 文字自适应。
"""
import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label

from config import load_config, set_key, save_config
from data_sources import search_company, get_company_detail, JUHE_DIMENSIONS
import legal
import ui
from ui import (FONT, PALETTE, C, CuteButton, CuteCard, CuteInput,
                CuteLabel, SettingRow, NavTab,
                info_popup, confirm_popup)

WW = Window.width  # 全局窗口宽度，避免 self.width=0 截断

# ---- 可点击圆角卡片 ----
class TapCard(ButtonBehavior, CuteCard):
    def __init__(self, **kw):
        super().__init__(**kw)


def lab(text, **kw):
    kw.setdefault("font_name", FONT)
    kw.setdefault("color", C(PALETTE["text"]))
    kw.setdefault("halign", "left")
    kw.setdefault("valign", "top")
    return Label(text=text, **kw)


EMOJI = {
    "basic": "🏢", "shareholders": "👥", "changes": "📝",
    "key_persons": "🧑‍💼", "investments": "🌿", "branches": "🏬",
    "abnormal": "⚠️", "penalty": "🚫", "serious": "❗", "dishonest": "👮",
    "equity": "💠", "mortgage": "🏦", "license": "📜", "tax": "💰",
    "owe_tax": "💸", "lawsuit": "⚖️", "court_notice": "📢",
    "court_doc": "📄", "court": "🕒", "trademark": "™️", "patent": "🔬",
    "copyright": "©️", "software": "💻", "icp": "🌐", "bid": "🔨",
    "bond": "📈", "job": "💼", "news": "📰", "wechat": "💬",
    "annual": "📅", "financing": "💵", "competitor": "🥊",
    "product": "🛍️", "import_export": "✈️", "land": "🌾",
    "qualification": "🏅", "random_check": "🔍",
}

HOT_KEYWORDS = ["腾讯", "阿里巴巴", "华为", "字节跳动", "百度", "京东", "美团", "小米", "比亚迪", "中国平安"]

def _mark_agreed():
    set_key("agreed_disclaimer", True)


# ──────────────────────────
#  搜索页 (Tab 1)
# ──────────────────────────
class SearchScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "search"
        root = BoxLayout(orientation="vertical", padding=[8, 10, 8, 0], spacing=6)

        # 顶部蓝色标题栏
        hdr = BoxLayout(size_hint_y=None, height=50, padding=[12, 8])
        hdr_lbl = lab("🔍 企信查", font_size=22, bold=True,
                       color=C(PALETTE["primary_d"]), halign="left", valign="middle")
        hdr_lbl.bind(texture_size=lambda i, s: setattr(i, "height", max(s[1], 40)))
        hdr.add_widget(hdr_lbl)
        sub_lbl = lab("企业信息查询", font_size=12,
                       color=C(PALETTE["sub"]), halign="right", valign="middle")
        hdr.add_widget(sub_lbl)
        root.add_widget(hdr)

        # 搜索条（蓝底卡片）
        bar = BoxLayout(size_hint_y=None, height=52, spacing=8)
        self.inp = CuteInput(hint_text="输入企业名称，如：腾讯",
                             size_hint_x=0.7, multiline=False)
        self.inp.bind(on_text_validate=lambda x: self.do_search())
        sbtn = CuteButton(text="🔍", size_hint_x=0.3, height=46,
                          bg=C(PALETTE["primary"]), radius=14)
        sbtn.bind(on_press=lambda x: self.do_search())
        bar.add_widget(self.inp)
        bar.add_widget(sbtn)
        root.add_widget(bar)

        self.status = lab("", font_size=13, color=C(PALETTE["sub"]),
                          size_hint_y=None, height=20)
        root.add_widget(self.status)

        # 内容区（ScrollView）
        self.sv = ScrollView()
        self.results = BoxLayout(orientation="vertical", size_hint_y=None,
                                 spacing=8, padding=2)
        self.results.bind(minimum_height=self.results.setter("height"))
        self.sv.add_widget(self.results)
        root.add_widget(self.sv)

        # 空状态引导（未搜索时显示热门搜索）
        self.empty_guide = BoxLayout(orientation="vertical", spacing=10, padding=[10, 8])
        guide_lbl = lab("💡 热门搜索", font_size=16, bold=True,
                        color=C(PALETTE["primary_d"]), halign="center", valign="middle",
                        size_hint_y=None, height=28)
        self.empty_guide.add_widget(guide_lbl)
        # 热门搜索标签（2列网格）
        tag_grid = BoxLayout(orientation="vertical", spacing=6, size_hint_y=None)
        tag_grid.bind(minimum_height=tag_grid.setter("height"))
        row1 = BoxLayout(spacing=6, size_hint_y=None, height=38)
        row2 = BoxLayout(spacing=6, size_hint_y=None, height=38)
        for i, kw in enumerate(HOT_KEYWORDS):
            chip = CuteButton(text=kw, font_size=13,
                              bg=C(PALETTE["chip"]), radius=12, height=34,
                              color=C(PALETTE["primary_d"]))
            chip.bind(on_press=lambda x, k=kw: self._quick_search(k))
            if i < 5:
                row1.add_widget(chip)
            else:
                row2.add_widget(chip)
        tag_grid.add_widget(row1)
        tag_grid.add_widget(row2)
        self.empty_guide.add_widget(tag_grid)
        tip = lab("搜索企业名称即可查看工商/股东/变更等31维度信息",
                  font_size=12, color=C(PALETTE["sub"]), halign="center",
                  size_hint_y=None, height=22)
        tip.bind(width=lambda i, w: setattr(tip, "text_size", (w, None)))
        self.empty_guide.add_widget(tip)
        self.sv.add_widget(self.empty_guide)

        self.add_widget(root)

    def _quick_search(self, kw):
        self.inp.text = kw
        self.do_search()

    def do_search(self):
        kw = self.inp.text.strip()
        if not kw:
            return
        self.sv.remove_widget(self.empty_guide)
        self.status.text = "🔄 查询中…"
        self.clear_results()
        threading.Thread(target=self._search, args=(kw,), daemon=True).start()

    def clear_results(self):
        self.results.clear_widgets()

    def _search(self, kw):
        try:
            items = search_company(kw)
            err = None
        except Exception as e:
            items, err = [], str(e)
        Clock.schedule_once(lambda dt: self._show(items, err))

    def _show(self, items, err):
        self.clear_results()
        if err:
            self.status.text = f"😢 错误：{err}"
            return
        if not items:
            self.status.text = "未找到结果。可在「我的」配置 API key，或确认企业名称。"
            return
        self.status.text = f"🎉 共 {len(items)} 条结果"
        for it in items:
            self.results.add_widget(self._result_card(
                it.get("name", ""), it.get("credit_code", "")))

    def _result_card(self, name, code):
        card = TapCard(padding=[14, 10], spacing=4, size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        n_lbl = lab(f"🏢 {name}", font_size=16, bold=True,
                    color=C(PALETTE["text"]),
                    size_hint_y=None, height=26)
        n_lbl.bind(width=lambda i, w: setattr(n_lbl, "text_size", (w, None)))
        card.add_widget(n_lbl)
        if code:
            c_lbl = lab(f"统一信用代码：{code}", font_size=13,
                        color=C(PALETTE["sub"]),
                        size_hint_y=None, height=20)
            c_lbl.bind(width=lambda i, w: setattr(c_lbl, "text_size", (w, None)))
            card.add_widget(c_lbl)
        card.bind(on_press=lambda x: self.goto_detail(name))
        return card

    def goto_detail(self, name):
        self.manager.get_screen("detail").show(name)


# ──────────────────────────
#  关注页 (Tab 2) - 空状态
# ──────────────────────────
class FollowScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "follow"
        root = BoxLayout(orientation="vertical", padding=[0, 10, 0, 0])
        # 标题栏
        hdr = BoxLayout(size_hint_y=None, height=46, padding=[16, 8])
        hdr.add_widget(lab("⭐ 关注企业", font_size=20, bold=True,
                           color=C(PALETTE["text"]), halign="left", valign="middle"))
        count = lab("0/50", font_size=13, color=C(PALETTE["sub"]),
                    halign="right", valign="middle")
        hdr.add_widget(count)
        root.add_widget(hdr)
        # 空状态
        empty = BoxLayout(orientation="vertical", padding=[30, 40])
        star = lab("⭐", font_size=48, halign="center", valign="middle",
                   color=C(PALETTE["sun"]), size_hint_y=None, height=70)
        empty.add_widget(star)
        tip1 = lab("暂无关注企业", font_size=18, bold=True,
                   color=C(PALETTE["text"]), halign="center", size_hint_y=None, height=30)
        empty.add_widget(tip1)
        tip2 = lab("在企业详情页点击收藏按钮，即可加入关注列表",
                   font_size=13, color=C(PALETTE["sub"]), halign="center",
                   size_hint_y=None, height=26)
        tip2.bind(width=lambda i, w: setattr(tip2, "text_size", (w, None)))
        empty.add_widget(tip2)
        gbtn = CuteButton(text="🔍 去搜索企业", bg=C(PALETTE["primary"]),
                          size_hint=(0.6, None), height=44, radius=14)
        gbtn.bind(on_press=lambda x: setattr(self.manager, "current", "search"))
        empty.add_widget(gbtn)
        root.add_widget(empty)
        self.add_widget(root)


# ──────────────────────────
#  对比页 (Tab 3) - 空状态
# ──────────────────────────
class CompareScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "compare"
        root = BoxLayout(orientation="vertical", padding=[0, 10, 0, 0])
        hdr = BoxLayout(size_hint_y=None, height=46, padding=[16, 8])
        hdr.add_widget(lab("📊 企业对比", font_size=20, bold=True,
                           color=C(PALETTE["text"]), halign="left", valign="middle"))
        count = lab("0/5", font_size=13, color=C(PALETTE["sub"]),
                    halign="right", valign="middle")
        hdr.add_widget(count)
        root.add_widget(hdr)
        empty = BoxLayout(orientation="vertical", padding=[30, 40])
        chart = lab("📊", font_size=48, halign="center", valign="middle",
                    color=C(PALETTE["lavender"]), size_hint_y=None, height=70)
        empty.add_widget(chart)
        tip1 = lab("暂无对比企业", font_size=18, bold=True,
                   color=C(PALETTE["text"]), halign="center", size_hint_y=None, height=30)
        empty.add_widget(tip1)
        tip2 = lab("最多同时对比5家企业，在企业详情页点击「加入对比」",
                   font_size=13, color=C(PALETTE["sub"]), halign="center",
                   size_hint_y=None, height=26)
        tip2.bind(width=lambda i, w: setattr(tip2, "text_size", (w, None)))
        empty.add_widget(tip2)
        gbtn = CuteButton(text="🔍 去搜索企业", bg=C(PALETTE["primary"]),
                          size_hint=(0.6, None), height=44, radius=14)
        gbtn.bind(on_press=lambda x: setattr(self.manager, "current", "search"))
        empty.add_widget(gbtn)
        root.add_widget(empty)
        self.add_widget(root)


# ──────────────────────────
#  我的页 (Tab 4) - 天眼查风格列表式
# ──────────────────────────
class ProfileScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "profile"
        root = BoxLayout(orientation="vertical", padding=0, spacing=0)
        # 标题栏
        hdr = BoxLayout(size_hint_y=None, height=46, padding=[16, 8])
        hdr.add_widget(lab("👤 我的", font_size=20, bold=True,
                           color=C(PALETTE["text"]), halign="left", valign="middle"))
        root.add_widget(hdr)

        sv = ScrollView()
        inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=0)
        inner.bind(minimum_height=inner.setter("height"))

        cfg = load_config()

        # ── 数据源配置 ──
        src_section = self._section_title("📡  数据源配置")
        inner.add_widget(src_section)
        inner.add_widget(self._setting_row("API密钥管理", "配置6个免费数据源key", ">", self._go_api))
        inner.add_widget(self._setting_row("自定义数据源", "接入你自己的API接口", ">", self._go_custom))
        inner.add_widget(self._setting_row("免费爬虫兜底", "开启" if cfg.get("enable_scrape", True) else "关闭", ">", self._toggle_scrape_row))
        inner.add_widget(self._divider())

        # ── 缓存与高级 ──
        adv_section = self._section_title("🛠  缓存与高级")
        inner.add_widget(adv_section)
        inner.add_widget(self._setting_row("清空本地缓存", "删除所有已缓存的企业数据", ">", self._clear_cache))
        inner.add_widget(self._setting_row("请求超时", f"{cfg.get('timeout', 10)}秒", ">", self._go_timeout))
        inner.add_widget(self._setting_row("缓存有效期", f"{cfg.get('cache_days', 30)}天", ">", self._go_cache_days))
        inner.add_widget(self._divider())

        # ── 协议与关于 ──
        about_section = self._section_title("📜  协议与关于")
        inner.add_widget(about_section)
        inner.add_widget(self._setting_row("关于企信查", f"v1.1.0  com.qxx.johnny", ">", self._show_about))
        inner.add_widget(self._setting_row("用户协议", "", ">", self._show_agreement))
        inner.add_widget(self._setting_row("隐私政策", "", ">", self._show_privacy))
        inner.add_widget(self._setting_row("免责声明", "数据来源说明", ">", self._show_disclaimer))
        inner.add_widget(self._divider())

        # ── 开发者信息 ──
        dev_section = self._section_title("👨‍💻  开发者")
        inner.add_widget(dev_section)
        inner.add_widget(self._setting_row("开发者", legal.AUTHOR, ""))
        inner.add_widget(self._setting_row("微信", legal.WECHAT, ""))
        inner.add_widget(self._setting_row("邮箱", legal.EMAIL, ""))
        inner.add_widget(self._setting_row("版权", f"© {legal.COPYRIGHT_YEAR} 企信查", ""))
        inner.add_widget(BoxLayout(size_hint_y=None, height=20))  # 底部间距

        sv.add_widget(inner)
        root.add_widget(sv)
        self.add_widget(root)

        self.scrape_on = bool(cfg.get("enable_scrape", True))

    # ── UI 工具 ──
    def _section_title(self, text):
        bl = BoxLayout(size_hint_y=None, height=38, padding=[16, 10])
        lbl = lab(text, font_size=14, bold=True, color=C(PALETTE["primary_d"]),
                  halign="left", valign="middle")
        bl.add_widget(lbl)
        return bl

    def _divider(self):
        bl = BoxLayout(size_hint_y=None, height=10, padding=[16, 5])
        bl.canvas.before.clear()  # 不画背景，纯间距
        return bl

    def _setting_row(self, title, subtitle="", right="", on_tap=None):
        bl = BoxLayout(orientation="horizontal", size_hint_y=None, height=50,
                       padding=[16, 6, 16, 6])
        # 左侧
        left = BoxLayout(orientation="vertical", size_hint_x=0.65)
        t = lab(title, font_size=15, color=C(PALETTE["text"]),
                halign="left", valign="middle", size_hint_y=None, height=24)
        t.bind(texture_size=lambda i, s: setattr(i, "height", s[1]))
        left.bind(width=lambda i, w: setattr(t, "text_size", (w, None)))
        left.add_widget(t)
        if subtitle:
            s = lab(subtitle, font_size=12, color=C(PALETTE["sub"]),
                    halign="left", valign="middle", size_hint_y=None, height=20)
            s.bind(texture_size=lambda i, v: setattr(i, "height", v[1]))
            left.bind(width=lambda i, w: setattr(s, "text_size", (w, None)))
            left.add_widget(s)
        bl.add_widget(left)
        # 右侧
        r = lab(right, font_size=13, color=C(PALETTE["sub"]),
                halign="right", valign="middle", size_hint_x=0.35)
        r.bind(texture_size=lambda i, v: None)
        bl.add_widget(r)
        # 点击
        if on_tap:
            def _on_touch(inst, touch):
                if inst.collide_point(*touch.pos):
                    on_tap()
            bl.bind(on_touch_down=_on_touch)
        return bl

    # ── 导航 ──
    def _go_api(self):
        self.manager.current = "api_config"

    def _go_custom(self):
        self.manager.current = "custom_config"

    def _go_timeout(self):
        self._edit_field_popup("请求超时(秒)", "timeout")

    def _go_cache_days(self):
        self._edit_field_popup("缓存有效期(天)", "cache_days")

    def _edit_field_popup(self, title, key):
        cfg = load_config()
        cur = str(cfg.get(key, ""))
        lay = BoxLayout(orientation="vertical", spacing=12, padding=14)
        inp = CuteInput(text=cur, multiline=False, size_hint_y=None, height=46)
        lay.add_widget(inp)
        btn_row = BoxLayout(size_hint_y=None, height=46, spacing=10)
        cancel = CuteButton(text="取消", bg=C(PALETTE["sub"]), radius=14)
        save_btn = CuteButton(text="保存", bg=C(PALETTE["primary"]), radius=14)
        btn_row.add_widget(cancel)
        btn_row.add_widget(save_btn)
        lay.add_widget(btn_row)
        popup = Popup(title=title, content=lay, size_hint=(0.85, 0.45),
                      auto_dismiss=False, title_font=FONT,
                      title_color=C(PALETTE["text"]),
                      background_color=C(PALETTE["bg"]))
        popup.separator_color = C(PALETTE["line"])
        cancel.bind(on_press=lambda x: popup.dismiss())
        def _save(*a):
            v = inp.text.strip()
            if v.isdigit():
                set_key(key, int(v))
            popup.dismiss()
            info_popup("保存成功", f"✅ {title} 已更新为 {v}", emoji="✅")
            # 刷新当前页
            self.manager.remove_widget(self)
            self.manager.add_widget(ProfileScreen())
            self.manager.current = "profile"
        save_btn.bind(on_press=_save)
        popup.open()

    # ── 爬虫开关 ──
    def _toggle_scrape_row(self):
        self.scrape_on = not self.scrape_on
        set_key("enable_scrape", self.scrape_on)
        info_popup("爬虫兜底",
                   f"免费网页抓取兜底：{'开启' if self.scrape_on else '关闭'}",
                   emoji="🕷")
        self.manager.remove_widget(self)
        self.manager.add_widget(ProfileScreen())
        self.manager.current = "profile"

    # ── 缓存清空 ──
    def _clear_cache(self):
        def _do():
            try:
                from cache import clear_all
                clear_all()
                info_popup("提示", "🧹 本地缓存已清空。", emoji="🧹")
            except Exception as e:
                info_popup("提示", f"清空失败：{e}", emoji="😢")
        confirm_popup("清空缓存", "确定要清空全部本地缓存吗？",
                      yes_text="确定清空", on_yes=_do, emoji="🧹")

    # ── 弹窗 ──
    def _show_about(self):
        info_popup("关于企信查",
                   f"企信查 v1.1.0\n包名：com.qxx.johnny\n目标：Android 12–16\n\n"
                   f"类「天眼查」风格企业信息检索学习作品。\n\n"
                   f"开发者：{legal.AUTHOR}\n微信：{legal.WECHAT}\n"
                   f"邮箱：{legal.EMAIL}\n版权所有 © {legal.COPYRIGHT_YEAR}",
                   emoji="💡")

    def _show_agreement(self):
        info_popup("用户协议", legal.USER_AGREEMENT, emoji="📄")

    def _show_privacy(self):
        info_popup("隐私政策", legal.PRIVACY_POLICY, emoji="🔒")

    def _show_disclaimer(self):
        info_popup("免责声明", legal.DISCLAIMER, btn_text="我知道了", emoji="⚠️")


# ──────────────────────────
#  API密钥配置页 (从"我的"跳转)
# ──────────────────────────
class ApiConfigScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "api_config"
        root = BoxLayout(orientation="vertical", padding=[0, 10, 0, 0])
        # 返回标题栏
        hdr = BoxLayout(size_hint_y=None, height=46, padding=[12, 8])
        back = CuteButton(text="←", bg=C(PALETTE["sub"]), size_hint_x=0.2,
                          height=38, radius=14)
        back.bind(on_press=lambda x: setattr(self.manager, "current", "profile"))
        hdr.add_widget(back)
        hdr.add_widget(lab("🔑 API密钥管理", font_size=18, bold=True,
                           color=C(PALETTE["text"]), halign="left", valign="middle"))
        root.add_widget(hdr)

        sv = ScrollView()
        inner = BoxLayout(orientation="vertical", size_hint_y=None,
                          padding=[14, 10], spacing=8)
        inner.bind(minimum_height=inner.setter("height"))

        # 说明文字（自适应宽度）
        tip = lab("在以下免费平台注册后填入 key：\n"
                  "· apibyte.cn（工商基础）\n"
                  "· xxapi.cn（股东/变更）\n"
                  "· jisuapi.com（工商/股东/变更/高管，字段极全）\n"
                  "· juhe.cn（对外投资/经营异常/行政处罚/商标/专利等）\n"
                  "· openapi.tianyancha.com（分支，需申请）\n"
                  "· openapi.qcc.com（全维度，需企业认证）",
                  font_size=13, color=C(PALETTE["sub"]),
                  size_hint_y=None)
        tip.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + 8))
        inner.bind(width=lambda i, w: setattr(tip, "text_size", (w - 28, None)))
        inner.add_widget(tip)

        cfg = load_config()
        self.fields = {}
        for label, key in [("apibyte key", "apibyte_key"),
                           ("xxapi key", "xxapi_key"),
                           ("jisuapi key", "jisuapi_key"),
                           ("聚合数据 key (juhe)", "juhe_key"),
                           ("天眼查开放 key", "tianyancha_key"),
                           ("企查查 key", "qcc_key")]:
            lbl = lab(label, font_size=13, color=C(PALETTE["text"]),
                      size_hint_y=None, height=20)
            lbl.bind(width=lambda i, w: setattr(lbl, "text_size", (w, None)))
            inner.add_widget(lbl)
            ti = CuteInput(text=cfg.get(key, ""), multiline=False,
                           size_hint_y=None, height=42)
            self.fields[key] = ti
            inner.add_widget(ti)

        save = CuteButton(text="💾 保存设置", bg=C(PALETTE["primary"]),
                          size_hint_y=None, height=48, radius=14)
        save.bind(on_press=lambda x: self._save())
        inner.add_widget(save)

        sv.add_widget(inner)
        root.add_widget(sv)
        self.add_widget(root)

    def _save(self):
        for key, ti in self.fields.items():
            set_key(key, ti.text.strip())
        info_popup("保存成功", "✅ API密钥已保存。", emoji="✅")
        self.manager.current = "profile"


# ──────────────────────────
#  自定义数据源配置页 (从"我的"跳转)
# ──────────────────────────
class CustomConfigScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "custom_config"
        root = BoxLayout(orientation="vertical", padding=[0, 10, 0, 0])
        hdr = BoxLayout(size_hint_y=None, height=46, padding=[12, 8])
        back = CuteButton(text="←", bg=C(PALETTE["sub"]), size_hint_x=0.2,
                          height=38, radius=14)
        back.bind(on_press=lambda x: setattr(self.manager, "current", "profile"))
        hdr.add_widget(back)
        hdr.add_widget(lab("➕ 自定义数据源", font_size=18, bold=True,
                           color=C(PALETTE["text"]), halign="left", valign="middle"))
        root.add_widget(hdr)

        sv = ScrollView()
        inner = BoxLayout(orientation="vertical", size_hint_y=None,
                          padding=[14, 10], spacing=8)
        inner.bind(minimum_height=inner.setter("height"))

        tip = lab("接入你自己在官网申请的任意接口，用于工商基础查询。",
                  font_size=13, color=C(PALETTE["sub"]),
                  size_hint_y=None, height=26)
        tip.bind(width=lambda i, w: setattr(tip, "text_size", (w - 28, None)))
        inner.add_widget(tip)

        cfg = load_config()
        cfg_custom = (cfg.get("custom_apis") or [{}])[0]
        self.cust = {}
        for clabel, ckey in [("名称", "name"),
                             ("接口URL（用 {kw} 占位企业名）", "url"),
                             ("API Key", "key"),
                             ("请求头模板（如 Authorization: Bearer {key}）", "header"),
                             ("字段映射JSON（如 {\"name\":\"data.name\"}）", "mapping")]:
            lbl = lab(clabel, font_size=13, color=C(PALETTE["text"]),
                      size_hint_y=None, height=20)
            lbl.bind(width=lambda i, w: setattr(lbl, "text_size", (w, None)))
            inner.add_widget(lbl)
            ti = CuteInput(text=str(cfg_custom.get(ckey, "")), multiline=False,
                           size_hint_y=None, height=42)
            self.cust[ckey] = ti
            inner.add_widget(ti)

        csave = CuteButton(text="💾 保存自定义源", bg=C(PALETTE["mint"]),
                           size_hint_y=None, height=48, radius=14)
        csave.bind(on_press=lambda x: self._save_custom())
        inner.add_widget(csave)

        sv.add_widget(inner)
        root.add_widget(sv)
        self.add_widget(root)

    def _save_custom(self):
        c = {k: self.cust[k].text.strip() for k in self.cust}
        if c.get("url"):
            cfg = load_config()
            cfg["custom_apis"] = [c]
            save_config(cfg)
        info_popup("保存成功", "✅ 自定义数据源已保存。", emoji="✅")
        self.manager.current = "profile"


# ──────────────────────────
#  企业详情页
# ──────────────────────────
class DetailScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "detail"
        self.root_layout = BoxLayout(orientation="vertical", padding=[0, 10, 0, 0])
        top = BoxLayout(size_hint_y=None, height=46, padding=[12, 8])
        back = CuteButton(text="← 返回", bg=C(PALETTE["sub"]),
                          size_hint_x=0.35, height=40, radius=14)
        back.bind(on_press=lambda x: setattr(self.manager, "current", "search"))
        title = lab("🔎 企业详情", font_size=18, bold=True,
                   color=C(PALETTE["primary_d"]),
                   halign="center", valign="center")
        top.add_widget(back)
        top.add_widget(title)
        self.root_layout.add_widget(top)

        self.sv = ScrollView()
        self.body = BoxLayout(orientation="vertical", size_hint_y=None,
                              padding=[10, 4], spacing=10)
        self.body.bind(minimum_height=self.body.setter("height"))
        self.sv.add_widget(self.body)
        self.root_layout.add_widget(self.sv)
        self.add_widget(self.root_layout)

    def show(self, name):
        self.body.clear_widgets()
        self.body.add_widget(lab("🔄 加载中…", color=C(PALETTE["sub"]),
                                 size_hint_y=None, height=30))
        threading.Thread(target=self._load, args=(name,), daemon=True).start()

    def _load(self, name):
        try:
            d = get_company_detail(name)
            err = None
        except Exception as e:
            d, err = None, str(e)
        Clock.schedule_once(lambda dt: self._render(name, d, err))

    def _section(self, key, title, rows, source=""):
        emoji = EMOJI.get(key, "📌")
        card = CuteCard(padding=[14, 10], spacing=4, size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        hdr = f"{title}   · 源：{source}" if source else title
        hdr_lbl = lab(f"{emoji} {hdr}", font_size=15, bold=True,
                      color=C(PALETTE["primary_d"]),
                      size_hint_y=None, height=24)
        hdr_lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1]))
        card.bind(width=lambda i, w: setattr(hdr_lbl, "text_size", (w - 28, None)))
        card.add_widget(hdr_lbl)
        if not rows:
            no_lbl = lab("· 暂无数据（未配置对应数据源 / 爬虫未命中）",
                        font_size=13, color=C(PALETTE["sub"]),
                        size_hint_y=None)
            no_lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + 4))
            card.bind(width=lambda i, w: setattr(no_lbl, "text_size", (w - 28, None)))
            card.add_widget(no_lbl)
        for r in rows:
            r_lbl = lab("· " + str(r), font_size=14,
                        color=C(PALETTE["text"]),
                        size_hint_y=None)
            r_lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + 2))
            card.bind(width=lambda i, w: setattr(r_lbl, "text_size", (w - 28, None)))
            card.add_widget(r_lbl)
        self.body.add_widget(card)

    def _render(self, name, d, err):
        self.body.clear_widgets()
        if err:
            self.body.add_widget(lab(f"😢 加载失败：{err}",
                                     color=C(PALETTE["danger"]),
                                     size_hint_y=None, height=30))
            return
        src = d.get("sources") or []
        banner = "当前数据源：" + ("、".join(src) if src
                                   else "无（未配置 key，已兜底网页抓取）")
        bcard = CuteCard(bg=C(PALETTE["chip"]), border=C(PALETTE["primary"]),
                         padding=[12, 8], spacing=4, size_hint_y=None)
        bcard.bind(minimum_height=bcard.setter("height"))
        b_lbl = lab("📡 " + banner, font_size=14, bold=True,
                     color=C(PALETTE["primary_d"]),
                     size_hint_y=None)
        b_lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + 4))
        bcard.bind(width=lambda i, w: setattr(b_lbl, "text_size", (w - 24, None)))
        bcard.add_widget(b_lbl)
        self.body.add_widget(bcard)

        b = d.get("basic") or {}
        card = CuteCard(padding=[14, 10], spacing=4, size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        n_lbl = lab(b.get("name", name), font_size=18, bold=True,
                    color=C(PALETTE["text"]),
                    size_hint_y=None)
        n_lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + 4))
        card.bind(width=lambda i, w: setattr(n_lbl, "text_size", (w - 28, None)))
        card.add_widget(n_lbl)
        pairs = [
            ("法定代表人", b.get("legal_person")),
            ("注册资本", b.get("reg_capital")),
            ("成立日期", b.get("establish_time")),
            ("登记状态", b.get("reg_status")),
            ("统一信用代码", b.get("credit_code")),
            ("企业类型", b.get("org_type")),
            ("行业", b.get("category")),
            ("注册地址", b.get("reg_location")),
            ("经营范围", b.get("business_scope")),
            ("省份", b.get("province")),
            ("曾用名", b.get("history_name")),
            ("登记机关", b.get("reg_organ")),
            ("核准日期", b.get("approval_date")),
            ("电话", b.get("phone")),
            ("邮箱", b.get("email")),
            ("官网", b.get("website")),
            ("参保人数", b.get("insure_num")),
            ("是否上市", b.get("is_listed")),
        ]
        for k, v in pairs:
            if v:
                v_lbl = lab(f"{k}：{v}", font_size=14,
                            color=C(PALETTE["text"]),
                            size_hint_y=None)
                v_lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + 2))
                card.bind(width=lambda i, w: setattr(v_lbl, "text_size", (w - 28, None)))
                card.add_widget(v_lbl)
        self.body.add_widget(card)

        ms = d.get("module_sources", {})
        self._section("shareholders",
                      "股东信息",
                      [f"{s.get('name')}（出资比例 {s.get('ratio')}，金额 {s.get('amount')}）"
                       for s in d.get("shareholders", [])], ms.get("shareholders", ""))
        self._section("changes",
                      "变更记录",
                      [f"{c.get('item')} @ {c.get('time')}" for c in d.get("changes", [])],
                      ms.get("changes", ""))
        self._section("key_persons",
                      "主要人员",
                      [f"{p.get('name')}（{p.get('position')}）"
                       for p in d.get("key_persons", [])], ms.get("key_persons", ""))
        self._section("investments",
                      "对外投资",
                      [f"{i.get('name')}（持股 {i.get('ratio')}）"
                       for i in d.get("investments", [])], ms.get("investments", ""))
        self._section("branches",
                      "分支机构",
                      [br.get("name", "") for br in d.get("branches", [])],
                      ms.get("branches", ""))
        for key, title, _, _ in JUHE_DIMENSIONS:
            self._section(key, title, d.get("dims", {}).get(key, []), ms.get(key, ""))


# ──────────────────────────
#  底部导航栏 + App 入口
# ──────────────────────────
class QXApp(App):
    FONT = FONT
    tabs = [("🔍", "搜索", "search"),
            ("⭐", "关注", "follow"),
            ("📊", "对比", "compare"),
            ("👤", "我的", "profile")]
    current_tab = "search"

    def build(self):
        Window.clearcolor = C(PALETTE["bg"])
        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(SearchScreen())
        self.sm.add_widget(FollowScreen())
        self.sm.add_widget(CompareScreen())
        self.sm.add_widget(ProfileScreen())
        self.sm.add_widget(DetailScreen())
        self.sm.add_widget(ApiConfigScreen())
        self.sm.add_widget(CustomConfigScreen())

        # 根容器：ScreenManager + 底部导航栏
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.sm)

        # 底部导航栏
        nav_bar = BoxLayout(size_hint_y=None, height=56,
                            padding=[4, 4, 4, 4], spacing=2)
        # 绘制白色背景
        from kivy.graphics import Color, Rectangle
        with nav_bar.canvas.before:
            Color(*C(PALETTE["nav_bg"]))
            self._nav_rect = Rectangle(pos=nav_bar.pos, size=nav_bar.size)
        nav_bar.bind(pos=lambda i, p: setattr(self._nav_rect, "pos", p),
                     size=lambda i, s: setattr(self._nav_rect, "size", s))
        # 上边分割线
        with nav_bar.canvas.before:
            Color(*C(PALETTE["line"]))
            self._nav_line = Rectangle(pos=(nav_bar.pos[0], nav_bar.pos[1] + nav_bar.size[1] - 1),
                                        size=(nav_bar.size[0], 1))
        nav_bar.bind(pos=lambda i, p: setattr(self._nav_line, "pos", (p[0], p[1] + i.height - 1)),
                     size=lambda i, s: setattr(self._nav_line, "size", (s[0], 1)))

        self.nav_btns = []
        for emoji, text, screen_name in self.tabs:
            btn_box = BoxLayout(orientation="vertical", spacing=1,
                                size_hint_x=0.25)
            e_lbl = Label(text=emoji, font_size=22,
                         color=C(PALETTE["nav_on"]) if screen_name == "search"
                         else C(PALETTE["nav_off"]),
                         halign="center", valign="middle", size_hint_y=None, height=30)
            t_lbl = Label(text=text, font_size=12, font_name=FONT,
                         color=C(PALETTE["nav_on"]) if screen_name == "search"
                         else C(PALETTE["nav_off"]),
                         halign="center", valign="middle", size_hint_y=None, height=18)
            btn_box.add_widget(e_lbl)
            btn_box.add_widget(t_lbl)
            btn_box.bind(on_touch_down=lambda inst, touch, sn=screen_name: (
                self._switch_tab(sn) if inst.collide_point(*touch.pos) else None))
            self.nav_btns.append((emoji, text, screen_name, e_lbl, t_lbl))
            nav_bar.add_widget(btn_box)
        root.add_widget(nav_bar)

        # 监听 ScreenManager 切换，更新导航栏选中态
        self.sm.bind(current=self._on_screen_change)

        # 首次启动弹免责声明
        cfg = load_config()
        if not cfg.get("agreed_disclaimer"):
            Clock.schedule_once(lambda dt: info_popup(
                "数据来源与免责声明", legal.DISCLAIMER,
                btn_text="我已阅读并同意", emoji="📢",
                on_close=_mark_agreed), 0.4)
        return root

    def _switch_tab(self, screen_name):
        if screen_name in ("search", "follow", "compare", "profile"):
            self.sm.current = screen_name
            self.current_tab = screen_name

    def _on_screen_change(self, sm, screen_name):
        # 映射子页面到对应 tab
        tab_map = {
            "search": "search", "follow": "follow",
            "compare": "compare", "profile": "profile",
            "detail": "search", "api_config": "profile",
            "custom_config": "profile",
        }
        active_tab = tab_map.get(screen_name, "search")
        self.current_tab = active_tab
        for emoji, text, sn, e_lbl, t_lbl in self.nav_btns:
            if sn == active_tab:
                e_lbl.color = C(PALETTE["nav_on"])
                t_lbl.color = C(PALETTE["nav_on"])
            else:
                e_lbl.color = C(PALETTE["nav_off"])
                t_lbl.color = C(PALETTE["nav_off"])


if __name__ == "__main__":
    QXApp().run()
