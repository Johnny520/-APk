# -*- coding: utf-8 -*-
"""企信查 · 可爱风 UI 主题与可复用组件。

集中管理粉系调色板、圆角卡片 / 按钮 / 输入框，以及通用弹窗，
让所有界面保持一致的可爱风格。
"""
import os

from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(BASE, "fonts", "NotoSansSC.ttf")
if not os.path.exists(FONT):
    FONT = None

# 可爱粉系调色板
PALETTE = {
    "bg":        "#FFF1F6",  # 整体背景：极浅粉
    "card":      "#FFFFFF",  # 卡片：纯白
    "primary":   "#FF8FB1",  # 主色：草莓粉
    "primary_d": "#F26D92",  # 主色深：用于标题
    "mint":      "#7FD8C0",  # 薄荷绿
    "lavender":  "#B9A3F2",  # 薰衣草紫
    "sky":       "#8EC9F2",  # 天空蓝
    "sun":       "#FFD479",  # 暖阳黄
    "text":      "#5A4A52",  # 主文字：暖灰
    "sub":       "#A2929B",  # 次要文字
    "danger":    "#FF7A85",  # 警示红
    "line":      "#F4DCE6",  # 描边/分割线
    "chip":      "#FFE3EE",  # 浅粉标签底
}


def C(hexstr):
    """hex 字符串 -> Kivy rgba 元组。"""
    return get_color_from_hex(hexstr)


def _darker(rgba, f=0.88):
    return [max(0.0, c * f) for c in rgba[:3]] + [rgba[3]]


class _Round:
    """为任意 Widget 叠加一个圆角矩形背景（及可选描边）。"""

    def _setup_round(self, bg, radius=20, border=None, border_w=1.5):
        self._r_bg = list(bg)
        self._r_radius = radius
        self._r_border = border
        self._r_border_w = border_w
        with self.canvas.before:
            self._r_color = Color(*bg)
            self._r_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[radius])
            if border is not None:
                self._r_lcolor = Color(*border)
                self._r_line = Line(
                    rounded_rectangle=(self.pos[0], self.pos[1],
                                       self.size[0], self.size[1], radius),
                    width=border_w)
        self.bind(pos=self._r_redraw, size=self._r_redraw)

    def _r_redraw(self, *a):
        self._r_rect.pos = self.pos
        self._r_rect.size = self.size
        if self._r_border is not None:
            self._r_line.rounded_rectangle = (
                self.pos[0], self.pos[1],
                self.size[0], self.size[1], self._r_radius)


class CuteButton(_Round, Button):
    """圆角可爱按钮，按下有轻微变深反馈。"""

    def __init__(self, bg=None, radius=22, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", (0, 0, 0, 0))
        kw.setdefault("font_name", FONT)
        kw.setdefault("color", C("#FFFFFF"))
        kw.setdefault("bold", True)
        super().__init__(**kw)
        base = bg or C(PALETTE["primary"])
        self._base_bg = base
        self._setup_round(base, radius)
        self.bind(on_press=lambda *a: setattr(self._r_color, "rgba", _darker(self._base_bg)))
        self.bind(on_release=lambda *a: setattr(self._r_color, "rgba", self._base_bg))

    def set_base(self, color):
        """运行时切换底色（如开关状态），并同步按下反馈基准色。"""
        self._base_bg = color
        self._r_color.rgba = color


class CuteCard(_Round, BoxLayout):
    """圆角卡片容器，默认白底浅粉描边。"""

    def __init__(self, bg=None, radius=20, border=None, border_w=1.5, **kw):
        kw.setdefault("orientation", "vertical")
        super().__init__(**kw)
        self._setup_round(
            bg or C(PALETTE["card"]), radius,
            border if border is not None else C(PALETTE["line"]), border_w)


class CuteInput(_Round, TextInput):
    """圆角输入框。"""

    def __init__(self, radius=16, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_color", (0, 0, 0, 0))
        kw.setdefault("font_name", FONT)
        kw.setdefault("foreground_color", C(PALETTE["text"]))
        kw.setdefault("hint_text_color", C(PALETTE["sub"]))
        kw.setdefault("cursor_color", C(PALETTE["primary_d"]))
        kw.setdefault("padding", [12, 9, 12, 9])
        super().__init__(**kw)
        self._setup_round(C("#FFFFFF"), radius,
                          border=C(PALETTE["line"]), border_w=1.5)


class CuteLabel(_Round, Label):
    """可选圆角底的小标签 / 徽标。"""

    def __init__(self, bg=None, radius=14, **kw):
        kw.setdefault("font_name", FONT)
        kw.setdefault("color", C(PALETTE["text"]))
        kw.setdefault("halign", "left")
        kw.setdefault("valign", "top")
        super().__init__(**kw)
        if bg is not None:
            self._setup_round(bg, radius)


def info_popup(title, text, btn_text="知道了", on_close=None, emoji="ℹ️"):
    """通用滚动信息弹窗（可爱风）。返回 popup 便于外部控制。"""
    lay = BoxLayout(orientation="vertical", spacing=10, padding=14)
    sv = ScrollView(size_hint=(1, 1))
    lbl = Label(text=text, font_name=FONT, font_size=14, color=C(PALETTE["text"]),
                halign="left", valign="top", size_hint_y=None)
    lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1]))
    sv.bind(width=lambda i, w: setattr(lbl, "text_size", (w - 20, None)))
    sv.add_widget(lbl)
    lay.add_widget(sv)
    btn = CuteButton(text=btn_text, bg=C(PALETTE["primary"]),
                     size_hint_y=None, height=48)
    lay.add_widget(btn)
    popup = Popup(title=f"{emoji}  {title}", content=lay, size_hint=(0.92, 0.86),
                  auto_dismiss=False, title_font=FONT,
                  title_color=C(PALETTE["text"]),
                  background_color=C("#FFF1F6"))
    popup.separator_color = C(PALETTE["line"])

    def _close(*a):
        popup.dismiss()
        if on_close:
            on_close()

    btn.bind(on_press=_close)
    popup.open()
    return popup


def confirm_popup(title, text, yes_text="确定", no_text="取消",
                  on_yes=None, emoji="❓"):
    """确认弹窗（两个按钮）。"""
    lay = BoxLayout(orientation="vertical", spacing=10, padding=14)
    body = Label(text=text, font_name=FONT, font_size=14, color=C(PALETTE["text"]),
                 halign="left", valign="top", size_hint_y=1,
                 text_size=(360, None))
    lay.add_widget(body)
    row = BoxLayout(size_hint_y=None, height=48, spacing=10)
    no = CuteButton(text=no_text, bg=C(PALETTE["sub"]))
    yes = CuteButton(text=yes_text, bg=C(PALETTE["danger"]))
    row.add_widget(no)
    row.add_widget(yes)
    lay.add_widget(row)
    popup = Popup(title=f"{emoji}  {title}", content=lay, size_hint=(0.9, 0.6),
                  auto_dismiss=False, title_font=FONT,
                  title_color=C(PALETTE["text"]),
                  background_color=C("#FFF1F6"))

    def _no(*a):
        popup.dismiss()

    def _yes(*a):
        popup.dismiss()
        if on_yes:
            on_yes()

    no.bind(on_press=_no)
    yes.bind(on_press=_yes)
    popup.open()
    return popup
