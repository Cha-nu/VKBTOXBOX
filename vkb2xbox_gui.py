# -*- coding: utf-8 -*-
"""vkb2xbox GUI - 매핑 편집 + 가상 Xbox 360 패드 실시간 확인."""
import ctypes
import json
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox

import vkb2xbox as core
from vkb2xbox import pygame

FONT = ("Malgun Gothic", 10)
FONT_B = ("Malgun Gothic", 10, "bold")
FONT_S = ("Malgun Gothic", 9)

# ----------------------------------------------------------------- 언어

LANGS = [("ko", "한국어"), ("en", "English")]

# (출력 이름, 한국어 표시 이름, 영어 표시 이름)
ROWS = [
    ("LX+", "왼쪽 스틱 →   (롤 오른쪽)", "Left stick →   (roll right)"),
    ("LX-", "왼쪽 스틱 ←   (롤 왼쪽)", "Left stick ←   (roll left)"),
    ("LY+", "왼쪽 스틱 ↑   (스틱 앞으로)", "Left stick ↑   (stick forward)"),
    ("LY-", "왼쪽 스틱 ↓   (스틱 당김)", "Left stick ↓   (stick back)"),
    ("RX+", "오른쪽 스틱 →   (카메라)", "Right stick →   (camera)"),
    ("RX-", "오른쪽 스틱 ←   (카메라)", "Right stick ←   (camera)"),
    ("RY+", "오른쪽 스틱 ↑   (카메라)", "Right stick ↑   (camera)"),
    ("RY-", "오른쪽 스틱 ↓   (카메라)", "Right stick ↓   (camera)"),
    ("RT", "RT 트리거   (가속)", "RT trigger   (throttle up)"),
    ("LT", "LT 트리거   (감속)", "LT trigger   (throttle down)"),
    ("RB", "RB 범퍼   (요 오른쪽)", "RB bumper   (yaw right)"),
    ("LB", "LB 범퍼   (요 왼쪽)", "LB bumper   (yaw left)"),
    ("LB+RB", "LB + RB 동시   (오토파일럿)", "LB + RB together   (autopilot)"),
    ("LT+RT", "LT + RT 동시   (포스트 스톨 기동)", "LT + RT together   (post-stall maneuver)"),
    ("A", "A 버튼", "A button"),
    ("B", "B 버튼", "B button"),
    ("X", "X 버튼", "X button"),
    ("Y", "Y 버튼", "Y button"),
    ("LS", "왼쪽 스틱 클릭 (L3)", "Left stick click (L3)"),
    ("RS", "오른쪽 스틱 클릭 (R3)", "Right stick click (R3)"),
    ("LS+RS", "L3 + R3 동시", "L3 + R3 together"),
    ("START", "Start / Menu", "Start / Menu"),
    ("BACK", "Back / View", "Back / View"),
    ("DU", "D패드 ↑", "D-pad ↑"),
    ("DD", "D패드 ↓", "D-pad ↓"),
    ("DL", "D패드 ←", "D-pad ←"),
    ("DR", "D패드 →", "D-pad →"),
]
ROW_NAMES = [r[0] for r in ROWS]
_ROW_LABELS = {"ko": {r[0]: r[1] for r in ROWS}, "en": {r[0]: r[2] for r in ROWS}}

TEXT = {
    "ko": {
        "title": "vkb2xbox - 조이스틱 → Xbox 360 매핑",
        "col_out": "Xbox 출력",
        "col_src": "조이스틱 입력",
        "btn_assign": "입력 지정",
        "btn_add": "입력 추가",
        "btn_clear": "지우기",
        "btn_clear_all": "전체 초기화",
        "pair": "반대 방향 자동 지정",
        "deadzone": "     선택 항목 데드존 %",
        "pad_on": "가상 Xbox 패드 켜기",
        "pad_off": "가상 Xbox 패드 끄기",
        "language": "언어 / Language",
        "help": ("· 표의 항목을 더블클릭(또는 '입력 지정')한 뒤 스틱을 움직이거나 버튼을 누르세요.\n"
                 "· 축은 원하는 방향으로 끝까지 움직이면 됩니다. Esc = 취소.\n"
                 "· 스틱·스로틀·페달 등 연결된 모든 장치를 함께 인식합니다.\n"
                 "· 변경 내용은 config.json에 자동 저장됩니다."),
        "raw": "원시 입력",
        "raw_dev": "원시 입력 · {dev}",
        "raw_multi": "   (장치 {count}개 중 마지막으로 움직인 것)",
        "raw_none": "조이스틱 연결 안 됨",
        "raw_text": "버튼: {btns}     햇: {hats}",
        "axis_n": "축 {i}",
        "src_deadzone": "  데드존 {pct}%",
        "dev": "입력 장치: ",
        "dev_indent": "                 ",
        "dev_row": "{name}  (축 {na}, 버튼 {nb}, 햇 {nh})",
        "dev_searching": "입력 장치: 조이스틱을 찾는 중…",
        "config_fail": "config.json을 읽지 못했습니다:\n{e}",
        "confirm_clear_all": "모든 매핑을 지울까요?",
        "idle": "항목을 더블클릭해서 입력을 지정하세요.",
        "no_stick": "조이스틱이 연결되어 있지 않습니다.",
        "capture": "「{name}」 에 쓸 입력을 움직이거나 누르세요…   (Esc 취소)",
        "captured": "「{name}」 ← {src}",
        "vgamepad_fail": "vgamepad를 불러올 수 없습니다:\n{e}",
        "connecting": "가상 패드 연결 중… (몇 초 걸립니다)",
        "vigem_ask": ("가상 Xbox 컨트롤러를 만들 수 없습니다.\n"
                      "ViGEmBus 드라이버가 설치되어 있지 않은 것 같습니다.\n\n"
                      "지금 드라이버 설치 프로그램을 실행할까요?\n"
                      "(설치가 끝나면 '가상 Xbox 패드 켜기'를 다시 누르세요)\n\n{e}"),
        "vigem_fail": ("가상 Xbox 컨트롤러를 만들 수 없습니다.\n"
                       "ViGEmBus 드라이버를 확인하세요.\n\n{e}"),
        "out_error": "가상 패드 출력 오류: {e}",
        "out_off": "꺼짐 · 그림은 매핑 미리보기",
        "out_slot_warn": "켜짐 · 주의: XInput {n}번 (다른 패드가 1번 차지)",
        "out_ok": "켜짐 · 그림은 가상 패드의 실제 출력 (XInput {n}번)",
        "out_checking": "켜짐 · 가상 패드 확인 중…",
    },
    "en": {
        "title": "vkb2xbox - Joystick → Xbox 360 mapper",
        "col_out": "Xbox output",
        "col_src": "Joystick input",
        "btn_assign": "Assign",
        "btn_add": "Add input",
        "btn_clear": "Clear",
        "btn_clear_all": "Clear all",
        "pair": "Auto-assign opposite direction",
        "deadzone": "     Deadzone of selected %",
        "pad_on": "Turn on virtual Xbox pad",
        "pad_off": "Turn off virtual Xbox pad",
        "language": "Language / 언어",
        "help": ("· Double-click a row (or 'Assign'), then move a stick or press a button.\n"
                 "· For axes, move all the way in the direction you want. Esc = cancel.\n"
                 "· All connected devices (stick, throttle, pedals...) are read together.\n"
                 "· Changes are saved to config.json automatically."),
        "raw": "Raw input",
        "raw_dev": "Raw input · {dev}",
        "raw_multi": "   (last moved of {count} devices)",
        "raw_none": "No joystick connected",
        "raw_text": "Buttons: {btns}     Hats: {hats}",
        "axis_n": "Axis {i}",
        "src_deadzone": "  deadzone {pct}%",
        "dev": "Input devices: ",
        "dev_indent": "                          ",
        "dev_row": "{name}  ({na} axes, {nb} buttons, {nh} hats)",
        "dev_searching": "Input devices: searching for joysticks…",
        "config_fail": "Could not read config.json:\n{e}",
        "confirm_clear_all": "Clear all mappings?",
        "idle": "Double-click a row to assign an input.",
        "no_stick": "No joystick is connected.",
        "capture": "Move or press the input for “{name}”…   (Esc to cancel)",
        "captured": "“{name}” ← {src}",
        "vgamepad_fail": "Could not load vgamepad:\n{e}",
        "connecting": "Connecting virtual pad… (takes a few seconds)",
        "vigem_ask": ("Could not create a virtual Xbox controller.\n"
                      "The ViGEmBus driver does not seem to be installed.\n\n"
                      "Run the driver installer now?\n"
                      "(After installing, press 'Turn on virtual Xbox pad' again)\n\n{e}"),
        "vigem_fail": ("Could not create a virtual Xbox controller.\n"
                       "Please check the ViGEmBus driver.\n\n{e}"),
        "out_error": "Virtual pad output error: {e}",
        "out_off": "Off · preview of the mapping",
        "out_slot_warn": "On · warning: XInput #{n} (another pad has #1)",
        "out_ok": "On · showing the virtual pad's real output (XInput #{n})",
        "out_checking": "On · checking virtual pad…",
    },
}

LANG = "ko"


def detect_lang():
    """Windows UI 언어가 한국어면 ko, 아니면 en."""
    try:
        return "ko" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x12 \
            else "en"
    except Exception:
        return "ko"


def tr(key, **kw):
    s = TEXT[LANG][key]
    return s.format(**kw) if kw else s


def label(name):
    return _ROW_LABELS[LANG][name]


def short_label(name):
    return label(name).split("   ")[0]

PAIR = {"LX+": "LX-", "LY+": "LY-", "RX+": "RX-", "RY+": "RY-",
        "RT": "LT", "RB": "LB", "DU": "DD", "DL": "DR"}
PAIR.update({v: k for k, v in list(PAIR.items())})


def default_min(name):
    if name[:2] in ("LX", "LY"):
        return 0.02
    if name[:2] in ("RX", "RY"):
        return 0.10
    if name in ("LT", "RT"):
        return 0.15
    return 0.30


# ----------------------------------------------------------------- XInput 읽기

class _XGamepad(ctypes.Structure):
    _fields_ = [("wButtons", ctypes.c_ushort), ("bLeftTrigger", ctypes.c_ubyte),
                ("bRightTrigger", ctypes.c_ubyte), ("sThumbLX", ctypes.c_short),
                ("sThumbLY", ctypes.c_short), ("sThumbRX", ctypes.c_short),
                ("sThumbRY", ctypes.c_short)]


class _XState(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_ulong), ("Gamepad", _XGamepad)]


XBITS = {"DU": 0x0001, "DD": 0x0002, "DL": 0x0004, "DR": 0x0008, "START": 0x0010,
         "BACK": 0x0020, "LS": 0x0040, "RS": 0x0080, "LB": 0x0100, "RB": 0x0200,
         "A": 0x1000, "B": 0x2000, "X": 0x4000, "Y": 0x8000}

try:
    _xinput = ctypes.windll.xinput1_4
except OSError:
    _xinput = None


def xinput_read(slot):
    """XInput 슬롯 상태를 dict로. 연결 안 됨이면 None."""
    if _xinput is None:
        return None
    st = _XState()
    if _xinput.XInputGetState(slot, ctypes.byref(st)) != 0:
        return None
    g = st.Gamepad
    return {
        "buttons": {n for n, bit in XBITS.items() if g.wButtons & bit},
        "lx": max(-1.0, g.sThumbLX / 32767.0), "ly": max(-1.0, g.sThumbLY / 32767.0),
        "rx": max(-1.0, g.sThumbRX / 32767.0), "ry": max(-1.0, g.sThumbRY / 32767.0),
        "lt": g.bLeftTrigger / 255.0, "rt": g.bRightTrigger / 255.0,
    }


def xinput_connected():
    return {i for i in range(4) if xinput_read(i) is not None}


EMPTY_STATE = {"buttons": set(), "lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0,
               "lt": 0.0, "rt": 0.0}


# ----------------------------------------------------------------- 패드 그림

class PadView:
    BG = "#1b1d22"
    BODY = "#2b2f36"
    EDGE = "#4a505a"
    OFF = "#3a3f47"
    ON = "#f2f2f2"
    TEXT = "#c9ced6"
    FACE = {"A": "#6bbf3b", "B": "#d9412e", "X": "#2f7fd9", "Y": "#e6b422"}

    def __init__(self, parent):
        c = self.c = tk.Canvas(parent, width=560, height=440, bg=self.BG,
                               highlightthickness=0)
        self.items = {}
        # 트리거 / 범퍼
        for name, x0 in (("LT", 95), ("RT", 385)):
            c.create_rectangle(x0, 10, x0 + 80, 28, fill=self.OFF, outline=self.EDGE)
            self.items[name] = c.create_rectangle(x0, 10, x0, 28, fill="#ff9d2e", outline="")
            c.create_text(x0 + 40, 19, text=name, fill=self.TEXT, font=FONT_S)
        for name, x0 in (("LB", 90), ("RB", 380)):
            self.items[name] = c.create_rectangle(x0, 36, x0 + 90, 56, fill=self.OFF,
                                                  outline=self.EDGE)
            c.create_text(x0 + 45, 46, text=name, fill=self.TEXT, font=FONT_S)
        # 본체
        c.create_polygon(
            [120, 70, 440, 70, 500, 110, 540, 300, 500, 350, 440, 330, 390, 270,
             170, 270, 120, 330, 60, 350, 20, 300, 60, 110],
            smooth=True, fill=self.BODY, outline=self.EDGE, width=2)
        # 스틱
        self.sticks = {}
        for name, cx, cy in (("L", 150, 140), ("R", 345, 225)):
            ring = c.create_oval(cx - 36, cy - 36, cx + 36, cy + 36, fill="#202329",
                                 outline=self.EDGE, width=2)
            dot = c.create_oval(cx - 22, cy - 22, cx + 22, cy + 22, fill="#565c67",
                                outline="#70777f", width=2)
            self.sticks[name] = (cx, cy, ring, dot)
        # ABXY
        for name, cx, cy in (("Y", 410, 105), ("A", 410, 175), ("X", 375, 140),
                             ("B", 445, 140)):
            self.items[name] = c.create_oval(cx - 15, cy - 15, cx + 15, cy + 15,
                                             fill=self.OFF, outline=self.FACE[name], width=2)
            c.create_text(cx, cy, text=name, fill="#ffffff", font=FONT_B)
        # Back / Guide / Start
        self.items["BACK"] = c.create_oval(226, 131, 254, 149, fill=self.OFF,
                                           outline=self.EDGE)
        self.items["START"] = c.create_oval(306, 131, 334, 149, fill=self.OFF,
                                            outline=self.EDGE)
        c.create_text(240, 160, text="Back", fill=self.TEXT, font=FONT_S)
        c.create_text(320, 160, text="Start", fill=self.TEXT, font=FONT_S)
        c.create_oval(264, 112, 296, 144, fill="#3d424b", outline=self.EDGE, width=2)
        # D패드
        c.create_rectangle(204, 214, 226, 236, fill=self.OFF, outline="")
        for name, box in (("DU", (204, 190, 226, 214)), ("DD", (204, 236, 226, 260)),
                          ("DL", (180, 214, 204, 236)), ("DR", (226, 214, 250, 236))):
            self.items[name] = c.create_rectangle(*box, fill=self.OFF, outline=self.EDGE)
        # 원시 입력 표시
        self.raw_title = c.create_text(20, 372, text=tr("raw"), fill=self.TEXT,
                                       font=FONT_S, anchor="w")
        self.raw_bars = []
        self.axis_labels = []
        for i in range(8):
            x0 = 20 + i * 67
            self.axis_labels.append(c.create_text(x0, 390, text=tr("axis_n", i=i),
                                                  fill="#8a909a", font=FONT_S, anchor="w"))
            c.create_rectangle(x0, 400, x0 + 58, 410, fill=self.OFF, outline="")
            c.create_line(x0 + 29, 398, x0 + 29, 412, fill="#70777f")
            self.raw_bars.append((x0, c.create_rectangle(x0 + 29, 400, x0 + 29, 410,
                                                         fill="#4fb3ff", outline="")))
        self.raw_text = c.create_text(20, 426, text="", fill="#8a909a", font=FONT_S,
                                      anchor="w")

    def retranslate(self):
        for i, item in enumerate(self.axis_labels):
            self.c.itemconfig(item, text=tr("axis_n", i=i))

    def show(self, st):
        c = self.c
        on = st["buttons"]
        for name in ("LB", "RB", "BACK", "START", "DU", "DD", "DL", "DR"):
            c.itemconfig(self.items[name], fill=self.ON if name in on else self.OFF)
        for name in "ABXY":
            c.itemconfig(self.items[name], fill=self.FACE[name] if name in on else self.OFF)
        for name, x0 in (("LT", 95), ("RT", 385)):
            c.coords(self.items[name], x0, 10, x0 + 80 * st[name.lower()], 28)
        for key, bx, by, click in (("L", "lx", "ly", "LS"), ("R", "rx", "ry", "RS")):
            cx, cy, ring, dot = self.sticks[key]
            x = cx + st[bx] * 20
            y = cy - st[by] * 20
            c.coords(dot, x - 22, y - 22, x + 22, y + 22)
            c.itemconfig(dot, fill=self.ON if click in on else "#565c67")
            moved = abs(st[bx]) > 0.01 or abs(st[by]) > 0.01
            c.itemconfig(ring, outline="#4fb3ff" if moved else self.EDGE)

    def show_raw(self, dev, snap, count):
        """dev 장치의 원시 입력을 보여 준다. count = 연결된 장치 수."""
        c = self.c
        for i, (x0, item) in enumerate(self.raw_bars):
            v = snap["axes"][i] if snap and i < len(snap["axes"]) else 0.0
            mid = x0 + 29
            c.coords(item, min(mid, mid + 29 * v), 400, max(mid, mid + 29 * v), 410)
        if snap is None:
            c.itemconfig(self.raw_title, text=tr("raw"))
            c.itemconfig(self.raw_text, text=tr("raw_none"))
        else:
            title = tr("raw_dev", dev=dev)
            if count > 1:
                title += tr("raw_multi", count=count)
            c.itemconfig(self.raw_title, text=title)
            btns = " ".join(str(b + 1) for b in sorted(snap["buttons"])) or "-"
            hats = " ".join(core.hat_dir(h) or "·" for h in snap["hats"]) or "-"
            c.itemconfig(self.raw_text, text=tr("raw_text", btns=btns, hats=hats))


# ----------------------------------------------------------------- 앱

class App:
    def __init__(self, root, config_path):
        self.root = root
        self.config_path = config_path
        self.binds = {}
        self.device = core.DEVICE_MATCH
        self.load()

        self.sticks = None
        self.raw_dev = None
        self.raw_prev = {}
        self.capture = None
        self.pad = None
        self.vg = None
        self.slot = None
        self.slots_before = set()
        self.pad_started = 0.0
        self.last_sent = None
        self.active_rows = set()
        self.frame = 0

        root.configure(bg="#f3f4f6")
        root.resizable(False, False)
        style = ttk.Style()
        style.configure("Treeview", font=FONT, rowheight=24)
        style.configure("Treeview.Heading", font=FONT_B)
        style.configure("TButton", font=FONT)
        style.configure("TCheckbutton", font=FONT)
        style.configure("TLabel", font=FONT)

        left = ttk.Frame(root, padding=10)
        left.grid(row=0, column=0, sticky="ns")
        right = ttk.Frame(root, padding=(0, 10, 10, 10))
        right.grid(row=0, column=1, sticky="n")

        # --- 왼쪽: 매핑 표
        self.tree = ttk.Treeview(left, columns=("out", "src"), show="headings",
                                 height=len(ROWS), selectmode="browse")
        self.tree.column("out", width=260, anchor="w")
        self.tree.column("src", width=360, anchor="w")
        self.tree.tag_configure("on", background="#cfe8ff")
        for name in ROW_NAMES:
            self.tree.insert("", "end", iid=name, values=("", ""))
        self.tree.grid(row=0, column=0, columnspan=4, sticky="nsew")
        self.tree.bind("<Double-1>", lambda e: self.start_capture(False))
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())
        self.tree.selection_set(ROW_NAMES[0])

        self.btn_assign = ttk.Button(left, command=lambda: self.start_capture(False))
        self.btn_assign.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.btn_add = ttk.Button(left, command=lambda: self.start_capture(True))
        self.btn_add.grid(row=1, column=1, sticky="ew", pady=(8, 0), padx=4)
        self.btn_clear = ttk.Button(left, command=self.clear_row)
        self.btn_clear.grid(row=1, column=2, sticky="ew", pady=(8, 0))
        self.btn_clear_all = ttk.Button(left, command=self.clear_all)
        self.btn_clear_all.grid(row=1, column=3, sticky="ew", pady=(8, 0), padx=(4, 0))

        opts = ttk.Frame(left)
        opts.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.pair_var = tk.BooleanVar(value=True)
        self.pair_chk = ttk.Checkbutton(opts, variable=self.pair_var)
        self.pair_chk.grid(row=0, column=0, sticky="w")
        self.dz_label = ttk.Label(opts)
        self.dz_label.grid(row=0, column=1)
        self.dz_var = tk.StringVar(value="")
        self.dz_spin = ttk.Spinbox(opts, from_=0, to=90, increment=1, width=5,
                                   textvariable=self.dz_var, command=self.apply_deadzone)
        self.dz_spin.grid(row=0, column=2, padx=4)
        self.dz_spin.bind("<Return>", lambda e: self.apply_deadzone())
        self.dz_spin.bind("<FocusOut>", lambda e: self.apply_deadzone())

        # --- 오른쪽: 상태 + 패드 그림
        self.status = tk.Label(right, text="", font=("Malgun Gothic", 11, "bold"),
                               bg="#fff4c2", fg="#333333", anchor="w", padx=10, pady=8,
                               width=52, justify="left")
        self.status.grid(row=0, column=0, sticky="ew")
        self.view = PadView(right)
        self.view.c.grid(row=1, column=0, pady=8)

        bar = ttk.Frame(right)
        bar.grid(row=2, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)
        self.out_btn = ttk.Button(bar, command=self.toggle_output)
        self.out_btn.grid(row=0, column=0, sticky="w")
        self.out_label = ttk.Label(bar, text="")
        self.out_label.grid(row=0, column=1, sticky="w", padx=10)
        self.dev_label = ttk.Label(right, text="", font=FONT_S, foreground="#555555",
                                   wraplength=560, justify="left")
        self.dev_label.grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.help_label = ttk.Label(right, font=FONT_S, foreground="#555555",
                                    justify="left", wraplength=560)
        self.help_label.grid(row=4, column=0, sticky="w", pady=(6, 0))

        lang_row = ttk.Frame(right)
        lang_row.grid(row=5, column=0, sticky="e", pady=(8, 0))
        self.lang_label = ttk.Label(lang_row, font=FONT_S, foreground="#555555")
        self.lang_label.grid(row=0, column=0, padx=(0, 6))
        self.lang_var = tk.StringVar(value=dict(LANGS)[LANG])
        lang_box = ttk.Combobox(lang_row, textvariable=self.lang_var, state="readonly",
                                width=9, font=FONT, values=[n for _, n in LANGS])
        lang_box.grid(row=0, column=1)
        lang_box.bind("<<ComboboxSelected>>", lambda e: self.change_lang())

        root.bind("<Escape>", lambda e: self.cancel_capture())
        root.protocol("WM_DELETE_WINDOW", self.close)

        core.init_pygame()
        self.sticks = core.Sticks(self.device)
        self.retranslate()
        self.on_select()
        self.tick()

    # ------------------------------------------------------------- 언어

    def retranslate(self):
        """현재 언어로 모든 고정 문구를 다시 쓴다."""
        self.root.title(tr("title"))
        self.tree.heading("out", text=tr("col_out"))
        self.tree.heading("src", text=tr("col_src"))
        for name in ROW_NAMES:
            self.tree.set(name, "out", label(name))
        self.btn_assign.config(text=tr("btn_assign"))
        self.btn_add.config(text=tr("btn_add"))
        self.btn_clear.config(text=tr("btn_clear"))
        self.btn_clear_all.config(text=tr("btn_clear_all"))
        self.pair_chk.config(text=tr("pair"))
        self.dz_label.config(text=tr("deadzone"))
        self.out_btn.config(text=tr("pad_off" if self.pad is not None else "pad_on"))
        self.help_label.config(text=tr("help"))
        self.lang_label.config(text=tr("language"))
        self.view.retranslate()
        self.update_dev_label()
        self.refresh_tree()
        if self.capture:
            self.show_capture_prompt(self.capture["name"])
        else:
            self.set_idle_status()

    def change_lang(self):
        global LANG
        code = {n: c for c, n in LANGS}.get(self.lang_var.get(), LANG)
        if code == LANG:
            return
        LANG = code
        self.save()
        self.retranslate()

    # ------------------------------------------------------------- 설정 파일

    def load(self):
        global LANG
        LANG = detect_lang()
        # 설정 파일이 아직 없으면 내장된 기본 매핑으로 시작한다
        path = self.config_path
        if not os.path.exists(path):
            path = core.BUILTIN_CONFIG
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    cfg = json.load(f)
                self.binds = cfg.get("bindings", {})
                self.device = cfg.get("device", core.DEVICE_MATCH)
                if cfg.get("language") in TEXT:
                    LANG = cfg["language"]
            except (OSError, ValueError) as e:
                messagebox.showwarning("vkb2xbox", tr("config_fail", e=e))

    def save(self):
        self.binds = {k: v for k, v in self.binds.items() if v}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"device": self.device, "language": LANG, "bindings": self.binds},
                      f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------- 표

    def src_text(self, s):
        t = core.describe(s, lang=LANG)
        if s["type"] == "axis":
            t += tr("src_deadzone", pct=round(s.get("min", 0) * 100))
        if s.get("device"):
            t += f"  [{s['device']}]"
        return t

    def update_dev_label(self):
        info = self.sticks.info()
        if info:
            text = tr("dev") + ("\n" + tr("dev_indent")).join(
                tr("dev_row", name=k, na=na, nb=nb, nh=nh) for k, na, nb, nh in info)
        else:
            text = tr("dev_searching")
        self.dev_label.config(text=text)

    def refresh_tree(self):
        for name in ROW_NAMES:
            text = ",  ".join(self.src_text(s) for s in self.binds.get(name, []))
            self.tree.set(name, "src", text)

    def selected(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def on_select(self):
        name = self.selected()
        axes = [s for s in self.binds.get(name, []) if s["type"] == "axis"] if name else []
        if axes:
            self.dz_spin.state(["!disabled"])
            self.dz_var.set(str(round(axes[0].get("min", 0) * 100)))
        else:
            self.dz_var.set("")
            self.dz_spin.state(["disabled"])

    def apply_deadzone(self):
        name = self.selected()
        try:
            dz = max(0, min(90, int(float(self.dz_var.get())))) / 100.0
        except ValueError:
            return
        if not name:
            return
        targets = [name]
        if self.pair_var.get() and name in PAIR:
            targets.append(PAIR[name])
        changed = False
        for n in targets:
            for s in self.binds.get(n, []):
                if s["type"] == "axis" and s.get("min") != dz:
                    s["min"] = dz
                    changed = True
        if changed:
            self.save()
            self.refresh_tree()

    def clear_row(self):
        name = self.selected()
        if name and self.binds.pop(name, None) is not None:
            self.save()
            self.refresh_tree()
            self.on_select()

    def clear_all(self):
        if messagebox.askyesno("vkb2xbox", tr("confirm_clear_all")):
            self.binds = {}
            self.save()
            self.refresh_tree()
            self.on_select()

    # ------------------------------------------------------------- 입력 지정

    def set_status(self, text, color="#fff4c2"):
        self.status.config(text=text, bg=color)

    def set_idle_status(self):
        self.set_status(tr("idle"), "#e8eaee")

    def show_capture_prompt(self, name):
        self.set_status(tr("capture", name=short_label(name)), "#fff4c2")

    def start_capture(self, add):
        name = self.selected()
        if not name:
            return
        if not self.sticks.names():
            self.set_status(tr("no_stick"), "#ffd0d0")
            return
        self.capture = {"name": name, "add": add, "t0": time.time(), "base": None}
        self.show_capture_prompt(name)

    def cancel_capture(self):
        if self.capture:
            self.capture = None
            self.set_idle_status()

    def poll_capture(self, snap):
        cap = self.capture
        if time.time() - cap["t0"] < 0.3:
            return
        if cap["base"] is None:
            cap["base"] = snap
            return
        base = cap["base"]
        for dev, s in snap.items():  # 도중에 꽂힌 장치
            base.setdefault(dev, s)
        found = core.detect_input(base, snap)
        if found is None:
            return
        self.capture = None
        self.assign(cap["name"], found, cap["add"])
        self.set_status(tr("captured", name=short_label(cap["name"]),
                           src=core.describe(found, True, LANG)), "#d6f5d6")

    def assign(self, name, src, add):
        def put(n, s):
            if s["type"] == "axis":
                s = dict(s, min=default_min(n), max=1.0)
            if add:
                self.binds.setdefault(n, []).append(s)
            else:
                self.binds[n] = [s]

        put(name, src)
        if self.pair_var.get() and name in PAIR:
            if src["type"] == "axis":
                put(PAIR[name], dict(src, sign=-src["sign"]))
            elif src["type"] == "hat":
                put(PAIR[name], dict(src, dir=core.HAT_OPPOSITE[src["dir"]]))
        self.save()
        self.refresh_tree()
        self.on_select()

    # ------------------------------------------------------------- 가상 패드

    def toggle_output(self):
        if self.pad is not None:
            self.stop_output()
            return
        try:
            import vgamepad as vg
        except Exception as e:
            messagebox.showerror("vkb2xbox", tr("vgamepad_fail", e=e))
            return
        self.vg = vg
        # 가상 패드가 꽂히면 Windows가 장치 목록을 다시 훑느라 몇 초간 창이 멈춘다
        self.out_label.config(text=tr("connecting"), foreground="#a06a00")
        self.root.update_idletasks()
        self.slots_before = xinput_connected()
        err = None
        for _ in range(4):
            try:
                self.pad = vg.VX360Gamepad()
                break
            except Exception as e:
                err = e
                time.sleep(0.7)
        if self.pad is None:
            msi = os.path.join(os.path.dirname(vg.__file__), "win", "vigem", "install",
                               "x64", "ViGEmBusSetup_x64.msi")
            if os.path.exists(msi):
                # 드라이버 설치 프로그램이 함께 들어 있으면 바로 실행할 수 있게 한다
                if messagebox.askyesno("vkb2xbox", tr("vigem_ask", e=err)):
                    os.startfile(msi)
            else:
                messagebox.showerror("vkb2xbox", tr("vigem_fail", e=err))
            return
        core.prime_pad(self.pad)
        B = vg.XUSB_BUTTON
        self.xbtn = {
            "A": B.XUSB_GAMEPAD_A, "B": B.XUSB_GAMEPAD_B,
            "X": B.XUSB_GAMEPAD_X, "Y": B.XUSB_GAMEPAD_Y,
            "LB": B.XUSB_GAMEPAD_LEFT_SHOULDER, "RB": B.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "LS": B.XUSB_GAMEPAD_LEFT_THUMB, "RS": B.XUSB_GAMEPAD_RIGHT_THUMB,
            "START": B.XUSB_GAMEPAD_START, "BACK": B.XUSB_GAMEPAD_BACK,
            "DU": B.XUSB_GAMEPAD_DPAD_UP, "DD": B.XUSB_GAMEPAD_DPAD_DOWN,
            "DL": B.XUSB_GAMEPAD_DPAD_LEFT, "DR": B.XUSB_GAMEPAD_DPAD_RIGHT,
        }
        self.slot = None
        self.pad_started = time.time()
        self.last_sent = None
        self.out_btn.config(text=tr("pad_off"))

    def stop_output(self):
        if self.pad is not None:
            try:
                self.pad.reset()
                self.pad.update()
            except Exception:
                pass
            self.pad = None
        self.slot = None
        self.out_btn.config(text=tr("pad_on"))

    def send(self, st):
        key = (tuple(sorted(st["buttons"])), st["lx"], st["ly"], st["rx"], st["ry"],
               st["lt"], st["rt"])
        if key == self.last_sent:
            return
        pad = self.pad
        pad.reset()
        for n in st["buttons"]:
            pad.press_button(button=self.xbtn[n])
        pad.left_joystick_float(x_value_float=st["lx"], y_value_float=st["ly"])
        pad.right_joystick_float(x_value_float=st["rx"], y_value_float=st["ry"])
        pad.left_trigger_float(value_float=st["lt"])
        pad.right_trigger_float(value_float=st["rt"])
        pad.update()
        self.last_sent = key

    # ------------------------------------------------------------- 주기 처리

    def compute(self):
        """현재 스틱 입력에 매핑을 적용한 Xbox 상태와 활성 행 목록."""
        vals = {}
        for name in ROW_NAMES:
            vals[name] = core.out_value(self.sticks, self.binds, name)
        st = {
            "buttons": {n for n in core.BUTTON_OUTPUTS if vals[n] > 0.0},
            "lx": round(vals["LX+"] - vals["LX-"], 3),
            "ly": round(vals["LY+"] - vals["LY-"], 3),
            "rx": round(vals["RX+"] - vals["RX-"], 3),
            "ry": round(vals["RY+"] - vals["RY-"], 3),
            "lt": round(vals["LT"], 3), "rt": round(vals["RT"], 3),
        }
        return st, {n for n, v in vals.items() if v > 0.0}

    def tick(self):
        self.frame += 1
        now = time.time()
        snaps = {}
        st, active = EMPTY_STATE, set()

        try:
            if self.sticks.pump():
                self.update_dev_label()
            snaps = self.sticks.snapshot()
            st, active = self.compute()
        except pygame.error:
            snaps = {}
            st, active = EMPTY_STATE, set()

        if self.capture:
            if snaps:
                self.poll_capture(snaps)
            else:
                self.cancel_capture()

        # 원시 입력 표시는 마지막으로 움직인 장치를 따라간다
        for dev, s in snaps.items():
            p = self.raw_prev.get(dev)
            if p is None or s["buttons"] != p["buttons"] or s["hats"] != p["hats"] or \
                    any(abs(a - b) > 0.05 for a, b in zip(s["axes"], p["axes"])):
                if p is not None:
                    self.raw_dev = dev
                self.raw_prev[dev] = s
        if self.raw_dev not in snaps:
            self.raw_dev = next(iter(snaps), None)

        shown = st
        if self.pad is not None:
            try:
                self.send(st)
            except Exception as e:
                self.stop_output()
                self.set_status(tr("out_error", e=e), "#ffd0d0")
            else:
                if self.slot is None and self.frame % 15 == 0:
                    new = xinput_connected() - self.slots_before
                    if new:
                        self.slot = min(new)
                if self.slot is not None:
                    real = xinput_read(self.slot)
                    if real is not None:
                        shown = real

        if self.frame % 2 == 0:
            self.view.show(shown)
            self.view.show_raw(self.raw_dev, snaps.get(self.raw_dev), len(snaps))
            if self.pad is None:
                self.out_label.config(text=tr("out_off"), foreground="#555555")
            elif self.slot is not None and self.slot > 0:
                # 게임은 보통 1번 컨트롤러만 읽는다
                self.out_label.config(text=tr("out_slot_warn", n=self.slot + 1),
                                      foreground="#c0392b")
            elif self.slot is not None:
                self.out_label.config(text=tr("out_ok", n=self.slot + 1),
                                      foreground="#1a7f1a")
            else:
                self.out_label.config(text=tr("out_checking"), foreground="#a06a00")
            if active != self.active_rows:
                for n in active ^ self.active_rows:
                    self.tree.item(n, tags=("on",) if n in active else ())
                self.active_rows = active

        self.root.after(8, self.tick)

    def close(self):
        self.stop_output()
        self.root.destroy()


def selftest(app, path):
    """개발용: 가상 패드를 켜고 잠시 뒤 창을 캡처한 다음 종료."""
    def shot():
        app.root.update()
        try:
            from PIL import ImageGrab
            x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
            w, h = app.root.winfo_width(), app.root.winfo_height()
            ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(path)
        except Exception as e:
            print("screenshot failed:", e)
        print("sticks:", app.sticks.names())
        print("pad:", app.pad is not None, "slot:", app.slot, "frames:", app.frame,
              "before:", app.slots_before, "now:", xinput_connected())
        app.close()

    app.root.attributes("-topmost", True)
    app.root.after(1200, app.toggle_output)
    app.root.after(9000, shot)


def main():
    config_path = core.DEFAULT_CONFIG
    if "--config" in sys.argv:
        config_path = sys.argv[sys.argv.index("--config") + 1]
    root = tk.Tk()
    app = App(root, config_path)
    if os.environ.get("VKB2XBOX_SELFTEST"):
        selftest(app, os.environ["VKB2XBOX_SELFTEST"])
    root.mainloop()


if __name__ == "__main__":
    main()
