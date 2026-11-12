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

# (출력 이름, 표시 이름)
ROWS = [
    ("LX+", "왼쪽 스틱 →   (롤 오른쪽)"),
    ("LX-", "왼쪽 스틱 ←   (롤 왼쪽)"),
    ("LY+", "왼쪽 스틱 ↑   (스틱 앞으로)"),
    ("LY-", "왼쪽 스틱 ↓   (스틱 당김)"),
    ("RX+", "오른쪽 스틱 →   (카메라)"),
    ("RX-", "오른쪽 스틱 ←   (카메라)"),
    ("RY+", "오른쪽 스틱 ↑   (카메라)"),
    ("RY-", "오른쪽 스틱 ↓   (카메라)"),
    ("RT", "RT 트리거   (가속)"),
    ("LT", "LT 트리거   (감속)"),
    ("RB", "RB 범퍼   (요 오른쪽)"),
    ("LB", "LB 범퍼   (요 왼쪽)"),
    ("LB+RB", "LB + RB 동시   (오토파일럿)"),
    ("LT+RT", "LT + RT 동시   (포스트 스톨 기동)"),
    ("A", "A 버튼"),
    ("B", "B 버튼"),
    ("X", "X 버튼"),
    ("Y", "Y 버튼"),
    ("LS", "왼쪽 스틱 클릭 (L3)"),
    ("RS", "오른쪽 스틱 클릭 (R3)"),
    ("LS+RS", "L3 + R3 동시"),
    ("START", "Start / Menu"),
    ("BACK", "Back / View"),
    ("DU", "D패드 ↑"),
    ("DD", "D패드 ↓"),
    ("DL", "D패드 ←"),
    ("DR", "D패드 →"),
]
LABEL = dict(ROWS)

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
        c.create_text(20, 372, text="VKB 원시 입력", fill=self.TEXT, font=FONT_S, anchor="w")
        self.raw_bars = []
        for i in range(6):
            x0 = 20 + i * 90
            c.create_text(x0, 390, text=f"축 {i}", fill="#8a909a", font=FONT_S, anchor="w")
            c.create_rectangle(x0, 400, x0 + 80, 410, fill=self.OFF, outline="")
            c.create_line(x0 + 40, 398, x0 + 40, 412, fill="#70777f")
            self.raw_bars.append((x0, c.create_rectangle(x0 + 40, 400, x0 + 40, 410,
                                                         fill="#4fb3ff", outline="")))
        self.raw_text = c.create_text(20, 426, text="", fill="#8a909a", font=FONT_S,
                                      anchor="w")

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

    def show_raw(self, snap):
        c = self.c
        for i, (x0, item) in enumerate(self.raw_bars):
            v = snap["axes"][i] if snap and i < len(snap["axes"]) else 0.0
            mid = x0 + 40
            c.coords(item, min(mid, mid + 40 * v), 400, max(mid, mid + 40 * v), 410)
        if snap is None:
            c.itemconfig(self.raw_text, text="스틱 연결 안 됨")
        else:
            btns = " ".join(str(b + 1) for b in sorted(snap["buttons"])) or "-"
            hats = " ".join(core.hat_dir(h) or "·" for h in snap["hats"]) or "-"
            c.itemconfig(self.raw_text, text=f"버튼: {btns}     햇: {hats}")


# ----------------------------------------------------------------- 앱

class App:
    def __init__(self, root, config_path):
        self.root = root
        self.config_path = config_path
        self.binds = {}
        self.device = core.DEVICE_MATCH
        self.load()

        self.stick = None
        self.next_open = 0.0
        self.capture = None
        self.pad = None
        self.vg = None
        self.slot = None
        self.slots_before = set()
        self.pad_started = 0.0
        self.last_sent = None
        self.active_rows = set()
        self.frame = 0

        root.title("vkb2xbox - VKB → Xbox 360 매핑")
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
        self.tree.heading("out", text="Xbox 출력")
        self.tree.heading("src", text="VKB 입력")
        self.tree.column("out", width=250, anchor="w")
        self.tree.column("src", width=250, anchor="w")
        self.tree.tag_configure("on", background="#cfe8ff")
        for name, _ in ROWS:
            self.tree.insert("", "end", iid=name, values=(LABEL[name], ""))
        self.tree.grid(row=0, column=0, columnspan=4, sticky="nsew")
        self.tree.bind("<Double-1>", lambda e: self.start_capture(False))
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())
        self.tree.selection_set(ROWS[0][0])

        ttk.Button(left, text="입력 지정", command=lambda: self.start_capture(False)) \
            .grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(left, text="입력 추가", command=lambda: self.start_capture(True)) \
            .grid(row=1, column=1, sticky="ew", pady=(8, 0), padx=4)
        ttk.Button(left, text="지우기", command=self.clear_row) \
            .grid(row=1, column=2, sticky="ew", pady=(8, 0))
        ttk.Button(left, text="전체 초기화", command=self.clear_all) \
            .grid(row=1, column=3, sticky="ew", pady=(8, 0), padx=(4, 0))

        opts = ttk.Frame(left)
        opts.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.pair_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="반대 방향 자동 지정", variable=self.pair_var) \
            .grid(row=0, column=0, sticky="w")
        ttk.Label(opts, text="     선택 항목 데드존 %").grid(row=0, column=1)
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
        self.out_btn = ttk.Button(bar, text="가상 Xbox 패드 켜기", command=self.toggle_output)
        self.out_btn.grid(row=0, column=0, sticky="w")
        self.out_label = ttk.Label(bar, text="")
        self.out_label.grid(row=0, column=1, sticky="w", padx=10)
        self.dev_label = ttk.Label(right, text="", font=FONT_S, foreground="#555555")
        self.dev_label.grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Label(right, font=FONT_S, foreground="#555555", justify="left", text=(
            "· 표의 항목을 더블클릭(또는 '입력 지정')한 뒤 스틱을 움직이거나 버튼을 누르세요.\n"
            "· 축은 원하는 방향으로 끝까지 움직이면 됩니다. Esc = 취소.\n"
            "· 변경 내용은 config.json에 자동 저장됩니다."
        )).grid(row=4, column=0, sticky="w", pady=(6, 0))

        root.bind("<Escape>", lambda e: self.cancel_capture())
        root.protocol("WM_DELETE_WINDOW", self.close)

        core.init_pygame()
        self.refresh_tree()
        self.on_select()
        self.set_idle_status()
        self.tick()

    # ------------------------------------------------------------- 설정 파일

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    cfg = json.load(f)
                self.binds = cfg.get("bindings", {})
                self.device = cfg.get("device", core.DEVICE_MATCH)
            except (OSError, ValueError) as e:
                messagebox.showwarning("vkb2xbox", f"config.json을 읽지 못했습니다:\n{e}")

    def save(self):
        self.binds = {k: v for k, v in self.binds.items() if v}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"device": self.device, "bindings": self.binds}, f,
                      ensure_ascii=False, indent=2)

    # ------------------------------------------------------------- 표

    def src_text(self, s):
        t = core.describe(s)
        if s["type"] == "axis":
            t += f"  데드존 {round(s.get('min', 0) * 100)}%"
        return t

    def refresh_tree(self):
        for name, _ in ROWS:
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
        if messagebox.askyesno("vkb2xbox", "모든 매핑을 지울까요?"):
            self.binds = {}
            self.save()
            self.refresh_tree()
            self.on_select()

    # ------------------------------------------------------------- 입력 지정

    def set_status(self, text, color="#fff4c2"):
        self.status.config(text=text, bg=color)

    def set_idle_status(self):
        self.set_status("항목을 더블클릭해서 입력을 지정하세요.", "#e8eaee")

    def start_capture(self, add):
        name = self.selected()
        if not name:
            return
        if self.stick is None:
            self.set_status("스틱이 연결되어 있지 않습니다.", "#ffd0d0")
            return
        self.capture = {"name": name, "add": add, "t0": time.time(), "base": None}
        self.set_status(f"「{LABEL[name].split('   ')[0]}」 에 쓸 입력을 움직이거나 누르세요…"
                        f"   (Esc 취소)", "#fff4c2")

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
        found = None
        new = snap["buttons"] - base["buttons"]
        if new:
            found = {"type": "button", "index": min(new)}
        if found is None:
            for h, xy in enumerate(snap["hats"]):
                d = core.hat_dir(xy)
                if d and xy != base["hats"][h]:
                    found = {"type": "hat", "index": h, "dir": d}
                    break
        if found is None:
            best, best_d, sign = None, 0.6, 1
            for a, v in enumerate(snap["axes"]):
                d = v - base["axes"][a]
                if abs(d) > best_d:
                    best, best_d, sign = a, abs(d), (1 if d > 0 else -1)
            if best is not None:
                found = {"type": "axis", "index": best, "sign": sign}
        if found is None:
            return
        self.capture = None
        self.assign(cap["name"], found, cap["add"])
        self.set_status(f"「{LABEL[cap['name']].split('   ')[0]}」 ← {core.describe(found)}",
                        "#d6f5d6")

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
            messagebox.showerror("vkb2xbox", f"vgamepad를 불러올 수 없습니다:\n{e}")
            return
        self.vg = vg
        # 가상 패드가 꽂히면 Windows가 장치 목록을 다시 훑느라 몇 초간 창이 멈춘다
        self.out_label.config(text="가상 패드 연결 중… (몇 초 걸립니다)", foreground="#a06a00")
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
            messagebox.showerror("vkb2xbox", "가상 Xbox 컨트롤러를 만들 수 없습니다.\n"
                                 f"ViGEmBus 드라이버를 확인하세요.\n\n{err}")
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
        self.out_btn.config(text="가상 Xbox 패드 끄기")

    def stop_output(self):
        if self.pad is not None:
            try:
                self.pad.reset()
                self.pad.update()
            except Exception:
                pass
            self.pad = None
        self.slot = None
        self.out_btn.config(text="가상 Xbox 패드 켜기")

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
        j = self.stick
        vals = {}
        for name, _ in ROWS:
            vals[name] = core.out_value(j, self.binds, name)
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
        snap = None
        st, active = EMPTY_STATE, set()

        if self.stick is None and now >= self.next_open:
            self.next_open = now + 1.0
            self.stick = core.open_stick(self.device)
            if self.stick is not None:
                j = self.stick
                self.dev_label.config(text=f"입력 장치: {j.get_name()}  (축 {j.get_numaxes()}, "
                                           f"버튼 {j.get_numbuttons()}, 햇 {j.get_numhats()})")
            else:
                self.dev_label.config(text=f"입력 장치: '{self.device}' 스틱을 찾는 중…")

        if self.stick is not None:
            try:
                snap = core.snapshot(self.stick)
                if not self.stick.get_init():
                    raise pygame.error("removed")
                st, active = self.compute()
            except pygame.error:
                self.stick = None
                snap = None
                st, active = EMPTY_STATE, set()
                self.cancel_capture()

        if self.capture and snap is not None:
            self.poll_capture(snap)

        shown = st
        if self.pad is not None:
            try:
                self.send(st)
            except Exception as e:
                self.stop_output()
                self.set_status(f"가상 패드 출력 오류: {e}", "#ffd0d0")
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
            self.view.show_raw(snap)
            if self.pad is None:
                self.out_label.config(text="꺼짐 · 그림은 매핑 미리보기", foreground="#555555")
            elif self.slot is not None and self.slot > 0:
                # 게임은 보통 1번 컨트롤러만 읽는다
                self.out_label.config(
                    text=f"켜짐 · 주의: XInput {self.slot + 1}번 (다른 패드가 1번 차지)",
                    foreground="#c0392b")
            elif self.slot is not None:
                self.out_label.config(
                    text=f"켜짐 · 그림은 가상 패드의 실제 출력 (XInput {self.slot + 1}번)",
                    foreground="#1a7f1a")
            else:
                self.out_label.config(text="켜짐 · 가상 패드 확인 중…", foreground="#a06a00")
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
        print("stick:", app.stick.get_name() if app.stick else None)
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
