# -*- coding: utf-8 -*-
"""企信查 - 类天眼查风格企业信息查询 App (Kivy)。可爱风 UI。"""
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
                info_popup, confirm_popup)

# ---- 可点击圆角卡片（搜索结果项） ----
class TapCard(ButtonBehavior, CuteCard):
    def __init__(self, **kw):
        super().__init__(**kw)


# ---- 可爱风小工具 ----
def lab(text, **kw):
    kw.setdefault("font_name", FONT)
    kw.setdefault("color", C(PALETTE["text"]))
    kw.setdefault("halign", "left")
    kw.setdefault("valign", "top")
    return Label(text=text, **kw)


# 各模块 Emoji（可爱点缀）
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


def _mark_agreed():
    set_key("agreed_disclaimer", True)


class SearchScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "search"
        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        # 顶部标题
        hdr = BoxLayout(size_hint_y=None, height=58)
        hdr.add_widget(lab("🐾 企信查", font_size=28, bold=True,
                           color=C(PALETTE["primary_d"])))
        hdr.add_widget(lab("企业信息查询", font_size=13,
                           color=C(PALETTE["sub"]),
                           halign="right", valign="bottom"))
        root.add_widget(hdr)

        # 搜索条
        bar = CuteCard(padding=8, spacing=8, size_hint_y=None, height=58)
        hb = BoxLayout(orientation="horizontal", spacing=8)
        self.inp = CuteInput(hint_text="输入企业名称，如：腾讯",
                             size_hint_x=0.72, multiline=False)
        self.inp.bind(on_text_validate=lambda x: self.do_search())
        sbtn = CuteButton(text="🔍 搜索", size_hint_x=0.28,
                          bg=C(PALETTE["primary"]))
        sbtn.bind(on_press=lambda x: self.do_search())
        hb.add_widget(self.inp)
        hb.add_widget(sbtn)
        bar.add_widget(hb)
        root.add_widget(bar)

        self.status = lab("", font_size=13, color=C(PALETTE["sub"]),
                          size_hint_y=None, height=20)
        root.add_widget(self.status)

        self.sv = ScrollView()
        self.results = BoxLayout(orientation="vertical", size_hint_y=None,
                                 spacing=10, padding=2)
        self.results.bind(minimum_height=self.results.setter("height"))
        self.sv.add_widget(self.results)
        root.add_widget(self.sv)

        # 底部导航
        nav = CuteCard(padding=6, spacing=10, size_hint_y=None, height=58)
        nb = BoxLayout(spacing=10)
        setbtn = CuteButton(text="⚙️ 设置", bg=C(PALETTE["lavender"]))
        setbtn.bind(on_press=lambda x: setattr(self.manager, "current", "settings"))
        nb.add_widget(setbtn)
        nav.add_widget(nb)
        root.add_widget(nav)

        self.add_widget(root)

    def clear_results(self):
        self.results.clear_widgets()

    def do_search(self):
        kw = self.inp.text.strip()
        if not kw:
            return
        self.status.text = "🔄 查询中…"
        self.clear_results()
        threading.Thread(target=self._search, args=(kw,), daemon=True).start()

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
            self.status.text = ("未找到结果。可先在「设置」配置免费 API key，"
                                "或确认企业名称准确。")
            return
        self.status.text = f"🎉 共 {len(items)} 条结果"
        for it in items:
            self.results.add_widget(self._result_card(
                it.get("name", ""), it.get("credit_code", "")))

    def _result_card(self, name, code):
        card = TapCard(padding=14, spacing=4, size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(lab(f"🏢 {name}", font_size=17, bold=True,
                            color=C(PALETTE["text"]),
                            size_hint_y=None, height=26))
        if code:
            card.add_widget(lab(f"统一信用代码：{code}", font_size=13,
                                color=C(PALETTE["sub"]),
                                size_hint_y=None, height=20))
        card.bind(on_press=lambda x: self.goto_detail(name))
        return card

    def goto_detail(self, name):
        self.manager.get_screen("detail").show(name)
        self.manager.current = "detail"


class DetailScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "detail"
        self.root_layout = BoxLayout(orientation="vertical", padding=12, spacing=10)
        top = BoxLayout(size_hint_y=None, height=52, spacing=10)
        back = CuteButton(text="← 返回", bg=C(PALETTE["sub"]),
                          size_hint_x=0.4, height=44)
        back.bind(on_press=lambda x: setattr(self.manager, "current", "search"))
        title = lab("🔎 企业详情", font_size=20, bold=True,
                   color=C(PALETTE["primary_d"]),
                   halign="center", valign="center")
        top.add_widget(back)
        top.add_widget(title)
        self.root_layout.add_widget(top)

        self.sv = ScrollView()
        self.body = BoxLayout(orientation="vertical", size_hint_y=None,
                              padding=4, spacing=12)
        self.body.bind(minimum_height=self.body.setter("height"))
        self.sv.add_widget(self.body)
        self.root_layout.add_widget(self.sv)
        self.add_widget(self.root_layout)

    def show(self, name):
        self.manager.current = "detail"
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
        card = CuteCard(padding=14, spacing=6, size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        hdr = f"{title}   · 源：{source}" if source else title
        card.add_widget(lab(f"{emoji} {hdr}", font_size=16, bold=True,
                            color=C(PALETTE["primary_d"]),
                            size_hint_y=None, height=26,
                            text_size=(self.width - 40, None)))
        if not rows:
            card.add_widget(lab("· 暂无数据（未配置对应数据源 / 爬虫未命中）",
                                font_size=13, color=C(PALETTE["sub"]),
                                size_hint_y=None, height=22,
                                text_size=(self.width - 40, None)))
        for r in rows:
            card.add_widget(lab("· " + str(r), font_size=14,
                                color=C(PALETTE["text"]),
                                size_hint_y=None, height=22,
                                text_size=(self.width - 40, None)))
        self.body.add_widget(card)

    def _render(self, name, d, err):
        self.body.clear_widgets()
        if err:
            self.body.add_widget(lab(f"😢 加载失败：{err}",
                                     color=C(PALETTE["danger"])))
            return
        src = d.get("sources") or []
        banner = "当前数据源：" + ("、".join(src) if src
                                   else "无（未配置 key，已兜底网页抓取）")
        bcard = CuteCard(bg=C(PALETTE["chip"]), border=C(PALETTE["primary"]),
                         padding=12, spacing=4, size_hint_y=None)
        bcard.bind(minimum_height=bcard.setter("height"))
        bcard.add_widget(lab("📡 " + banner, font_size=14, bold=True,
                             color=C(PALETTE["primary_d"]),
                             size_hint_y=None, height=24,
                             text_size=(self.width - 40, None)))
        self.body.add_widget(bcard)

        b = d.get("basic") or {}
        card = CuteCard(padding=14, spacing=4, size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(lab(b.get("name", name), font_size=19, bold=True,
                            color=C(PALETTE["text"]),
                            size_hint_y=None, height=28))
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
                card.add_widget(lab(f"{k}：{v}", font_size=14,
                                    color=C(PALETTE["text"]),
                                    size_hint_y=None, height=22,
                                    text_size=(self.width - 40, None)))
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


class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "settings"
        root = BoxLayout(orientation="vertical")
        sv = ScrollView()
        inner = BoxLayout(orientation="vertical", size_hint_y=None, padding=12,
                          spacing=12)
        inner.bind(minimum_height=inner.setter("height"))
        W = inner.add_widget

        # ---- API 密钥 ----
        api_card = CuteCard(padding=14, spacing=8, size_hint_y=None)
        api_card.bind(minimum_height=api_card.setter("height"))
        api_card.add_widget(lab("🔑 API 密钥设置", font_size=18, bold=True,
                                color=C(PALETTE["primary_d"]),
                                size_hint_y=None, height=26))
        api_card.add_widget(lab(
            "在以下免费平台注册后填入 key：\n"
            "· apibyte.cn（工商基础）\n"
            "· xxapi.cn（股东/变更）\n"
            "· jisuapi.com（工商/股东/变更/高管，字段极全）\n"
            "· juhe.cn（对外投资/经营异常/行政处罚/商标/专利等全维度）\n"
            "· openapi.tianyancha.com（分支，需申请）\n"
            "· openapi.qcc.com（全维度，需企业认证）",
            font_size=13, color=C(PALETTE["sub"]),
            size_hint_y=None, height=130,
            text_size=(self.width - 60, None)))
        cfg = load_config()
        self.fields = {}
        for label, key in [("apibyte key", "apibyte_key"),
                           ("xxapi key", "xxapi_key"),
                           ("jisuapi key", "jisuapi_key"),
                           ("聚合数据 key(juhe)", "juhe_key"),
                           ("天眼查开放 key", "tianyancha_key"),
                           ("企查查 key", "qcc_key")]:
            api_card.add_widget(lab(label, font_size=13,
                                    size_hint_y=None, height=20))
            ti = CuteInput(text=cfg.get(key, ""), multiline=False,
                           size_hint_y=None, height=42)
            self.fields[key] = ti
            api_card.add_widget(ti)
        W(api_card)

        # ---- 自定义 API ----
        cust_card = CuteCard(padding=14, spacing=8, size_hint_y=None)
        cust_card.bind(minimum_height=cust_card.setter("height"))
        cust_card.add_widget(lab("➕ 自定义数据源（可选）", font_size=16, bold=True,
                                 color=C(PALETTE["primary_d"]),
                                 size_hint_y=None, height=24))
        cust_card.add_widget(lab(
            "接入你自己在官网申请的任意接口，用于工商基础查询。",
            font_size=13, color=C(PALETTE["sub"]),
            size_hint_y=None, height=38,
            text_size=(self.width - 60, None)))
        cfg_custom = (cfg.get("custom_apis") or [{}])[0]
        self.cust = {}
        for clabel, ckey in [("名称", "name"),
                             ("接口URL（用 {kw} 占位企业名）", "url"),
                             ("API Key", "key"),
                             ("请求头模板（如 Authorization: Bearer {key}，留空则作 ?key= 参数）", "header"),
                             ("字段映射JSON（可选，如 {\"name\":\"data.name\"}）", "mapping")]:
            cust_card.add_widget(lab(clabel, font_size=13,
                                     size_hint_y=None, height=20))
            ti = CuteInput(text=str(cfg_custom.get(ckey, "")), multiline=False,
                           size_hint_y=None, height=42)
            self.cust[ckey] = ti
            cust_card.add_widget(ti)
        csave = CuteButton(text="💾 保存自定义源", bg=C(PALETTE["mint"]),
                           size_hint_y=None, height=46)
        csave.bind(on_press=lambda x: self._save_custom())
        cust_card.add_widget(csave)
        W(cust_card)

        # ---- 缓存与高级 ----
        adv_card = CuteCard(padding=14, spacing=8, size_hint_y=None)
        adv_card.bind(minimum_height=adv_card.setter("height"))
        adv_card.add_widget(lab("🛠 缓存与高级", font_size=16, bold=True,
                                color=C(PALETTE["primary_d"]),
                                size_hint_y=None, height=24))
        clr = CuteButton(text="🧹 清空本地缓存", bg=C(PALETTE["danger"]),
                         size_hint_y=None, height=44)
        clr.bind(on_press=lambda x: self._clear_cache())
        adv_card.add_widget(clr)
        # 爬虫开关
        self.scrape_on = bool(cfg.get("enable_scrape", True))
        self.scrape_btn = CuteButton(
            text=self._scrape_label(),
            bg=C(PALETTE["mint"]) if self.scrape_on else C(PALETTE["sub"]),
            size_hint_y=None, height=44)
        self.scrape_btn.bind(on_press=lambda x: self._toggle_scrape())
        adv_card.add_widget(self.scrape_btn)
        self.adv = {}
        for alabel, akey in [("请求超时(秒)", "timeout"),
                             ("缓存有效期(天)", "cache_days")]:
            adv_card.add_widget(lab(alabel, font_size=13,
                                    size_hint_y=None, height=20))
            ti = CuteInput(text=str(cfg.get(akey, "")), multiline=False,
                           input_type="number", size_hint_y=None, height=42)
            self.adv[akey] = ti
            adv_card.add_widget(ti)
        W(adv_card)

        # ---- 协议与关于 ----
        about_card = CuteCard(padding=14, spacing=8, size_hint_y=None)
        about_card.bind(minimum_height=about_card.setter("height"))
        about_card.add_widget(lab("📜 协议与关于", font_size=16, bold=True,
                                  color=C(PALETTE["primary_d"]),
                                  size_hint_y=None, height=24))
        about_btn = CuteButton(text="💡 关于企信查", bg=C(PALETTE["mint"]),
                               size_hint_y=None, height=42)
        about_btn.bind(on_press=lambda x: info_popup(
            "关于企信查",
            f"企信查 v1.1.0\n包名：com.qxx.johnny\n目标：Android 12–16\n\n"
            f"类「天眼查」风格企业信息检索学习作品，可爱风 UI。\n\n"
            f"开发者：{legal.AUTHOR}\n微信：{legal.WECHAT}\n"
            f"邮箱：{legal.EMAIL}\n版权所有 © {legal.COPYRIGHT_YEAR}",
            emoji="💡"))
        about_card.add_widget(about_btn)
        agree_btn = CuteButton(text="📄 用户协议", bg=C(PALETTE["mint"]),
                               size_hint_y=None, height=42)
        agree_btn.bind(on_press=lambda x: info_popup("用户协议", legal.USER_AGREEMENT, emoji="📄"))
        about_card.add_widget(agree_btn)
        priv_btn = CuteButton(text="🔒 隐私政策", bg=C(PALETTE["mint"]),
                              size_hint_y=None, height=42)
        priv_btn.bind(on_press=lambda x: info_popup("隐私政策", legal.PRIVACY_POLICY, emoji="🔒"))
        about_card.add_widget(priv_btn)
        disc_btn = CuteButton(text="⚠️ 免责声明（数据来源）", bg=C(PALETTE["mint"]),
                               size_hint_y=None, height=42)
        disc_btn.bind(on_press=lambda x: info_popup("免责声明", legal.DISCLAIMER,
                                                     btn_text="我知道了", emoji="⚠️"))
        about_card.add_widget(disc_btn)
        about_card.add_widget(lab(
            f"开发者：{legal.AUTHOR}\n微信：{legal.WECHAT}\n"
            f"邮箱：{legal.EMAIL}\n版权所有 © {legal.COPYRIGHT_YEAR} 企信查",
            font_size=13, color=C(PALETTE["sub"]),
            size_hint_y=None, height=80,
            text_size=(self.width - 60, None)))
        W(about_card)

        # ---- 保存 / 返回 ----
        act_card = CuteCard(padding=10, spacing=10, size_hint_y=None)
        act_card.bind(minimum_height=act_card.setter("height"))
        save = CuteButton(text="💖 保存设置", bg=C(PALETTE["primary"]),
                          size_hint_y=None, height=50)
        save.bind(on_press=lambda x: self._save())
        act_card.add_widget(save)
        back = CuteButton(text="← 返回搜索", bg=C(PALETTE["sub"]),
                          size_hint_y=None, height=46)
        back.bind(on_press=lambda x: setattr(self.manager, "current", "search"))
        act_card.add_widget(back)
        W(act_card)

        sv.add_widget(inner)
        root.add_widget(sv)
        self.add_widget(root)

    def _scrape_label(self):
        return "🕷 免费网页抓取兜底：开启" if self.scrape_on else "🕷 免费网页抓取兜底：关闭"

    def _toggle_scrape(self):
        self.scrape_on = not self.scrape_on
        set_key("enable_scrape", self.scrape_on)
        self.scrape_btn.text = self._scrape_label()
        self.scrape_btn.set_base(C(PALETTE["mint"]) if self.scrape_on
                                 else C(PALETTE["sub"]))

    def _save(self):
        for key, ti in self.fields.items():
            set_key(key, ti.text.strip())
        for key, ti in self.adv.items():
            v = ti.text.strip()
            if v.isdigit():
                set_key(key, int(v))
        set_key("enable_scrape", self.scrape_on)
        info_popup("保存成功", "✅ 设置已保存。", emoji="💖")
        self.manager.current = "search"

    def _save_custom(self):
        c = {k: self.cust[k].text.strip() for k in self.cust}
        if c.get("url"):
            cfg = load_config()
            cfg["custom_apis"] = [c]
            save_config(cfg)
        info_popup("保存成功", "✅ 自定义数据源已保存。", emoji="💾")
        self.manager.current = "search"

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


class QXApp(App):
    FONT = FONT

    def build(self):
        Window.clearcolor = C(PALETTE["bg"])
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(SearchScreen())
        sm.add_widget(DetailScreen())
        sm.add_widget(SettingsScreen())
        # 首次启动弹免责声明
        cfg = load_config()
        if not cfg.get("agreed_disclaimer"):
            Clock.schedule_once(lambda dt: info_popup(
                "数据来源与免责声明", legal.DISCLAIMER,
                btn_text="我已阅读并同意", emoji="📢",
                on_close=_mark_agreed), 0.4)
        return sm


if __name__ == "__main__":
    QXApp().run()
