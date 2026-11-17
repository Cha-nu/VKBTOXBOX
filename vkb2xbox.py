# -*- coding: utf-8 -*-
"""vkb2xbox - VKB 조이스틱 입력을 가상 Xbox 360 컨트롤러로 변환.

사용법:
    python vkb2xbox.py setup     매핑 마법사 (스틱을 직접 눌러서 지정)
    python vkb2xbox.py run       변환 실행 (게임 켜기 전에 실행)
    python vkb2xbox.py monitor   스틱의 원시 입력 확인

옵션: --config <경로>  (기본: 이 파일 옆의 config.json)
"""
import json
import os
import sys
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
# 게임 창에 포커스가 있어도 스틱 입력을 계속 읽기 위해 필요
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
# dummy 비디오 드라이버는 창 메시지를 돌리지 않아서, 이게 없으면 장치를 꽂거나
# 뽑아도 알아채지 못한다 (별도 스레드에서 장치 변화를 감지)
os.environ["SDL_JOYSTICK_THREAD"] = "1"

import pygame  # noqa: E402

if getattr(sys, "frozen", False):
    # exe로 묶인 경우: 설정은 exe 옆에 저장하고, 기본 매핑은 exe 안에서 꺼낸다
    HERE = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE = getattr(sys, "_MEIPASS", HERE)
else:
    HERE = BUNDLE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "config.json")
# config.json이 아직 없을 때 GUI가 처음 불러오는 기본 매핑
BUILTIN_CONFIG = os.path.join(BUNDLE, "config.example.json")
DEVICE_MATCH = "VKB"
# 이름에 이 글자가 들어간 장치는 입력으로 쓰지 않는다 (가상 패드 자신을 다시 읽지 않도록)
VIRTUAL_HINTS = ("xbox", "x-box", "xinput")

BUTTON_OUTPUTS = ["A", "B", "X", "Y", "LB", "RB", "LS", "RS", "START", "BACK",
                  "DU", "DD", "DL", "DR"]
ANALOG_OUTPUTS = ["LX+", "LX-", "LY+", "LY-", "RX+", "RX-", "RY+", "RY-", "LT", "RT"]

HAT_OPPOSITE = {"U": "D", "D": "U", "L": "R", "R": "L"}


# ----------------------------------------------------------------- 공통

def init_pygame():
    pygame.display.init()
    pygame.joystick.init()


def is_virtual(name):
    """우리가 만든 가상 패드(및 다른 Xbox 패드)인지. 입력 장치로 쓰면 출력이 되먹임된다."""
    n = name.lower()
    return any(h in n for h in VIRTUAL_HINTS)


class Sticks:
    """연결된 모든 조이스틱(스틱·스로틀·페달 등)을 열어 두고 이름으로 찾아 준다.

    장치 키는 조이스틱 이름이며, 같은 이름이 여럿이면 ' #2', ' #3'이 붙는다.
    """

    def __init__(self, default_match=DEVICE_MATCH):
        self.default = default_match  # "device"가 없는 예전 매핑이 쓸 장치
        self.by_id = {}               # instance_id -> (키, Joystick)
        self._cache = {}
        self._scan()

    def _scan(self):
        changed = False
        for i in range(pygame.joystick.get_count()):
            try:
                j = pygame.joystick.Joystick(i)
                iid = j.get_instance_id()
                name = j.get_name().strip()
            except pygame.error:
                continue
            if iid in self.by_id or is_virtual(name):
                continue
            used = {k for k, _ in self.by_id.values()}
            key, n = name, 2
            while key in used:
                key, n = f"{name} #{n}", n + 1
            self.by_id[iid] = (key, j)
            changed = True
        if changed:
            self._cache.clear()
        return changed

    def pump(self):
        """이벤트를 처리한다. 장치가 꽂히거나 뽑혔으면 True."""
        added = removed = False
        for e in pygame.event.get():
            if e.type == pygame.JOYDEVICEADDED:
                added = True
            elif e.type == pygame.JOYDEVICEREMOVED:
                if self.by_id.pop(e.instance_id, None) is not None:
                    removed = True
                    self._cache.clear()
        if added:
            added = self._scan()
        return added or removed

    def names(self):
        return [k for k, _ in self.by_id.values()]

    def info(self):
        """[(키, 축 수, 버튼 수, 햇 수)]"""
        return [(k, j.get_numaxes(), j.get_numbuttons(), j.get_numhats())
                for k, j in self.by_id.values()]

    def find(self, spec):
        """spec과 이름이 같은 장치, 없으면 이름에 spec이 들어간 장치. 없으면 None."""
        if spec is None:
            spec = self.default
        if spec in self._cache:
            return self._cache[spec]
        low = spec.lower()
        hit = None
        for k, j in self.by_id.values():
            if k.lower() == low:
                hit = j
                break
        if hit is None:
            for k, j in self.by_id.values():
                if low in k.lower():
                    hit = j
                    break
        self._cache[spec] = hit
        return hit

    def snapshot(self):
        """{키: {"axes": [...], "buttons": {...}, "hats": [...]}}"""
        self.pump()
        out = {}
        for k, j in list(self.by_id.values()):
            try:
                out[k] = {
                    "axes": [j.get_axis(a) for a in range(j.get_numaxes())],
                    "buttons": {b for b in range(j.get_numbuttons()) if j.get_button(b)},
                    "hats": [j.get_hat(h) for h in range(j.get_numhats())],
                }
            except pygame.error:
                pass
        return out


def print_devices(sticks):
    for k, na, nb, nh in sticks.info():
        print(f"장치: {k}  (축 {na}, 버튼 {nb}, 햇 {nh})")


def wait_for_sticks(default_match=DEVICE_MATCH):
    sticks = Sticks(default_match)
    if not sticks.names():
        print("조이스틱을 찾는 중... (장치를 연결하세요, Ctrl+C로 취소)")
        while not sticks.names():
            time.sleep(0.5)
            sticks.pump()
    print_devices(sticks)
    return sticks


def detect_input(base, cur, kinds=("button", "axis")):
    """두 스냅샷을 비교해 새로 눌리거나 크게 움직인 입력 하나를 돌려준다. 없으면 None."""
    if "button" in kinds:
        for dev, c in cur.items():
            b = base.get(dev)
            if b is None:
                continue
            new = c["buttons"] - b["buttons"]
            if new:
                return {"type": "button", "index": min(new), "device": dev}
            for h, xy in enumerate(c["hats"]):
                d = hat_dir(xy)
                if d and xy != b["hats"][h]:
                    return {"type": "hat", "index": h, "dir": d, "device": dev}
    if "axis" in kinds:
        best, best_d = None, 0.6
        for dev, c in cur.items():
            b = base.get(dev)
            if b is None:
                continue
            for a, v in enumerate(c["axes"]):
                d = v - b["axes"][a]
                if abs(d) > best_d:
                    best_d = abs(d)
                    best = {"type": "axis", "index": a, "sign": 1 if d > 0 else -1,
                            "device": dev}
        return best
    return None


def hat_dir(xy):
    x, y = xy
    if x == 0 and y > 0:
        return "U"
    if x == 0 and y < 0:
        return "D"
    if y == 0 and x < 0:
        return "L"
    if y == 0 and x > 0:
        return "R"
    return None


def src_value(sticks, s):
    """입력 소스 하나의 값을 0.0~1.0으로 돌려준다. 장치가 없으면 0."""
    j = sticks.find(s.get("device"))
    if j is None:
        return 0.0
    t = s["type"]
    try:
        if t == "button":
            return 1.0 if j.get_button(s["index"]) else 0.0
        if t == "hat":
            x, y = j.get_hat(s["index"])
            d = s["dir"]
            hit = (d == "U" and y > 0) or (d == "D" and y < 0) or \
                  (d == "L" and x < 0) or (d == "R" and x > 0)
            return 1.0 if hit else 0.0
        if t == "axis":
            v = j.get_axis(s["index"]) * s["sign"]
            lo = s.get("min", 0.0)
            hi = s.get("max", 1.0)
            if v <= lo:
                return 0.0
            return min(1.0, (v - lo) / (hi - lo))
    except pygame.error:  # 방금 뽑혔거나, 그 장치에 없는 축/버튼 번호
        pass
    return 0.0


# 입력 하나로 Xbox 버튼 두 개를 동시에 누르는 조합 출력
COMBOS = {"LB+RB": ("LB", "RB"), "LT+RT": ("LT", "RT"), "LS+RS": ("LS", "RS")}


def out_value(sticks, binds, name):
    """Xbox 출력 하나의 값(0.0~1.0). 그 출력이 속한 조합 매핑도 함께 반영한다."""
    srcs = list(binds.get(name, []))
    for combo, members in COMBOS.items():
        if name in members:
            srcs += binds.get(combo, [])
    return max((src_value(sticks, s) for s in srcs), default=0.0)


_DESC_WORDS = {"ko": ("버튼", "햇", "축"), "en": ("Button", "Hat", "Axis")}


def describe(s, with_device=False, lang="ko"):
    w_btn, w_hat, w_axis = _DESC_WORDS.get(lang, _DESC_WORDS["ko"])
    if s["type"] == "button":
        t = f"{w_btn} {s['index'] + 1}"
    elif s["type"] == "hat":
        t = f"{w_hat} {s['index']} {s['dir']}"
    else:
        t = f"{w_axis} {s['index']} ({'+' if s['sign'] > 0 else '-'})"
    if with_device and s.get("device"):
        t += f" [{s['device']}]"
    return t


def prime_pad(pad):
    """새 가상 패드의 초기 상태를 중립으로 만든다.

    갓 만든 패드는 스틱이 약간 쏠린 값을 보고하고, 중립(전부 0) 보고는 드라이버가
    '변화 없음'으로 무시한다. 0이 아닌 값을 한 번 보낸 뒤 중립을 보내야 한다.
    """
    pad.left_joystick(x_value=256, y_value=256)
    pad.right_joystick(x_value=256, y_value=256)
    pad.update()
    pad.reset()
    pad.update()


# ----------------------------------------------------------------- 실행

def run(config_path, seconds=None):
    import vgamepad as vg

    if not os.path.exists(config_path):
        print("config.json이 없습니다. 먼저 setup을 실행하세요.")
        return 1
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    binds = cfg["bindings"]

    init_pygame()
    sticks = wait_for_sticks(cfg.get("device", DEVICE_MATCH))

    def report_missing():
        specs = {s.get("device") or sticks.default
                 for srcs in binds.values() for s in srcs}
        for spec in sorted(specs):
            if sticks.find(spec) is None:
                print(f"연결 안 됨: {spec}  (꽂으면 자동으로 인식합니다)")

    report_missing()

    B = vg.XUSB_BUTTON
    xbtn = {
        "A": B.XUSB_GAMEPAD_A, "B": B.XUSB_GAMEPAD_B,
        "X": B.XUSB_GAMEPAD_X, "Y": B.XUSB_GAMEPAD_Y,
        "LB": B.XUSB_GAMEPAD_LEFT_SHOULDER, "RB": B.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "LS": B.XUSB_GAMEPAD_LEFT_THUMB, "RS": B.XUSB_GAMEPAD_RIGHT_THUMB,
        "START": B.XUSB_GAMEPAD_START, "BACK": B.XUSB_GAMEPAD_BACK,
        "DU": B.XUSB_GAMEPAD_DPAD_UP, "DD": B.XUSB_GAMEPAD_DPAD_DOWN,
        "DL": B.XUSB_GAMEPAD_DPAD_LEFT, "DR": B.XUSB_GAMEPAD_DPAD_RIGHT,
    }

    pad = None
    for attempt in range(5):  # 가상 장치가 처음 꽂힐 때는 한두 번 실패할 수 있음
        try:
            pad = vg.VX360Gamepad()
            break
        except Exception as e:  # ViGEmBus 미설치 등
            err = e
            time.sleep(1.0)
    if pad is None:
        print(f"가상 Xbox 컨트롤러를 만들 수 없습니다: {err}")
        print("ViGEmBus 드라이버가 설치되어 있는지 확인하세요.")
        return 1
    prime_pad(pad)

    def out(name):
        return out_value(sticks, binds, name)

    print("가상 Xbox 360 컨트롤러 동작 중. 이 창을 켜 둔 채로 게임을 실행하세요.")
    print("종료: Ctrl+C 또는 창 닫기")
    last = None
    t_end = None if seconds is None else time.time() + seconds
    try:
        while t_end is None or time.time() < t_end:
            if sticks.pump():
                print("장치 목록이 바뀌었습니다.")
                print_devices(sticks)
                report_missing()
            pressed = tuple(n for n in BUTTON_OUTPUTS if out(n) > 0.0)
            lx = round(out("LX+") - out("LX-"), 3)
            ly = round(out("LY+") - out("LY-"), 3)
            rx = round(out("RX+") - out("RX-"), 3)
            ry = round(out("RY+") - out("RY-"), 3)
            lt = round(out("LT"), 3)
            rt = round(out("RT"), 3)
            state = (pressed, lx, ly, rx, ry, lt, rt)
            if state != last:
                pad.reset()
                for n in pressed:
                    pad.press_button(button=xbtn[n])
                pad.left_joystick_float(x_value_float=lx, y_value_float=ly)
                pad.right_joystick_float(x_value_float=rx, y_value_float=ry)
                pad.left_trigger_float(value_float=lt)
                pad.right_trigger_float(value_float=rt)
                pad.update()
                last = state
            time.sleep(0.004)
    except KeyboardInterrupt:
        pass
    pad.reset()
    pad.update()
    print("종료했습니다.")
    return 0


# ----------------------------------------------------------------- 모니터

def monitor():
    init_pygame()
    sticks = wait_for_sticks()
    print("스틱을 움직이거나 버튼을 눌러 보세요. 종료: Ctrl+C")
    last = {}
    try:
        while True:
            if sticks.pump():
                print_devices(sticks)
            for dev, s in sticks.snapshot().items():
                state = ([round(a, 2) for a in s["axes"]],
                         [b + 1 for b in sorted(s["buttons"])], s["hats"])
                if last.get(dev) != state:
                    print(f"[{dev}] 축 {state[0]}  버튼 {state[1]}  햇 {state[2]}")
                    last[dev] = state
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    return 0


# ----------------------------------------------------------------- 마법사

class Quit(Exception):
    pass


def kb_flush():
    import msvcrt
    while msvcrt.kbhit():
        msvcrt.getwch()


def kb_poll():
    """눌린 키가 있으면 소문자로, 없으면 None."""
    import msvcrt
    if msvcrt.kbhit():
        return msvcrt.getwch().lower()
    return None


def detect(sticks, text, kinds, wait_release=True):
    """프롬프트를 보여주고 입력 하나를 감지한다. S=건너뛰기(None), Q=중단."""
    print(f"\n▶ {text}")
    print("   (S = 건너뛰기, Q = 중단)")
    time.sleep(0.6)
    kb_flush()
    base = sticks.snapshot()
    found = None
    while found is None:
        k = kb_poll()
        if k == "s":
            print("   건너뜀")
            return None
        if k in ("q", "\x1b"):
            raise Quit()
        cur = sticks.snapshot()
        for dev, snap in cur.items():  # 도중에 꽂힌 장치
            base.setdefault(dev, snap)
        found = detect_input(base, cur, kinds)
        time.sleep(0.01)
    print(f"   → {describe(found, True)}")
    if wait_release:
        dev, idx = found["device"], found["index"]
        t0 = time.time()
        while time.time() - t0 < 5.0:
            cur = sticks.snapshot().get(dev)
            if cur is None:
                break
            if found["type"] == "button" and idx not in cur["buttons"]:
                break
            if found["type"] == "hat" and cur["hats"][idx] == (0, 0):
                break
            if found["type"] == "axis" and \
                    abs(cur["axes"][idx] - base[dev]["axes"][idx]) < 0.3:
                break
            time.sleep(0.01)
    return found


def setup(config_path):
    init_pygame()
    j = wait_for_sticks()
    binds = {}

    def add(name, src):
        binds.setdefault(name, []).append(src)

    def axis_half(src, sign_mul, lo, hi=1.0):
        return dict(src, sign=src["sign"] * sign_mul, min=lo, max=hi)

    print("\n=== 조이스틱 → Xbox 매핑 마법사 ===")
    print("연결된 모든 장치(스틱·스로틀·페달)를 함께 인식합니다.")
    print("안내에 따라 스틱을 움직이거나 버튼을 누르면 자동으로 인식합니다.")
    print("각 단계 전에는 스틱에서 손을 떼고 중립으로 두세요.")

    try:
        # --- 비행 축
        s = detect(j, "[롤] 스틱을 오른쪽으로 끝까지 기울이세요", {"axis"})
        if s:
            add("LX+", axis_half(s, 1, 0.02))
            add("LX-", axis_half(s, -1, 0.02))

        s = detect(j, "[피치] 스틱을 앞으로(모니터 쪽) 끝까지 미세요", {"axis"})
        if s:
            add("LY+", axis_half(s, 1, 0.02))
            add("LY-", axis_half(s, -1, 0.02))

        print("\n다음은 스로틀입니다. 먼저 스로틀 레버를 '최소(끝까지 내림)'로 두세요.")
        s = detect(j, "[스로틀] 레버를 최대(가속 방향)로 끝까지 올리세요", {"axis"},
                   wait_release=False)
        if s:
            # 가운데 = 중립, 위쪽 절반 = RT(가속), 아래쪽 절반 = LT(감속)
            add("RT", axis_half(s, 1, 0.15))
            add("LT", axis_half(s, -1, 0.15))
            print("   가운데는 중립, 위쪽 절반은 가속(RT), 아래쪽 절반은 감속(LT)입니다.")
            print("   레버를 가운데쯤으로 돌려 놓으세요.")
            time.sleep(1.5)

        s = detect(j, "[요] 스틱을 오른쪽으로 끝까지 비트세요 (트위스트)", {"axis"})
        if s:
            add("RB", axis_half(s, 1, 0.3))
            add("LB", axis_half(s, -1, 0.3))

        # --- 카메라 (오른쪽 스틱): 축 또는 햇/버튼
        for pos, neg, label, d_pos, d_neg in (
                ("RX+", "RX-", "카메라 오른쪽", "오른쪽", "왼쪽"),
                ("RY+", "RY-", "카메라 위쪽", "위쪽", "아래쪽")):
            s = detect(j, f"[{label}] 미니스틱이나 햇을 {d_pos}으로 미세요",
                       {"axis", "button"})
            if not s:
                continue
            if s["type"] == "axis":
                add(pos, axis_half(s, 1, 0.1))
                add(neg, axis_half(s, -1, 0.1))
            elif s["type"] == "hat":
                add(pos, s)
                add(neg, dict(s, dir=HAT_OPPOSITE[s["dir"]]))
            else:
                add(pos, s)
                s2 = detect(j, f"[카메라 {d_neg}] {d_neg} 방향 버튼을 누르세요", {"button"})
                if s2:
                    add(neg, s2)

        # --- 버튼
        buttons = [
            ("A", "A 버튼 (ACZero 기준: 기총 / 확인)"),
            ("B", "B 버튼 (미사일 / 취소)"),
            ("X", "X 버튼 (무장 전환)"),
            ("Y", "Y 버튼 (타겟 전환)"),
            ("LS", "왼쪽 스틱 클릭 L3"),
            ("RS", "오른쪽 스틱 클릭 R3 (카메라 모드)"),
            ("START", "Menu / Start (일시정지)"),
            ("BACK", "View / Back (레이더 맵 전환)"),
        ]
        for name, label in buttons:
            s = detect(j, f"[{label}] 로 쓸 버튼을 누르세요", {"button"})
            if s:
                add(name, s)

        s = detect(j, "[LB+RB 동시 (오토파일럿)] 로 쓸 버튼을 누르세요", {"button"})
        if s:
            add("LB", s)
            add("RB", s)

        # --- D패드
        s = detect(j, "[D패드 위] 로 쓸 햇을 위로 미세요 (또는 버튼)", {"button"})
        if s and s["type"] == "hat":
            for name, d in (("DU", "U"), ("DD", "D"), ("DL", "L"), ("DR", "R")):
                add(name, dict(s, dir=d))
            print("   햇의 네 방향을 D패드에 모두 연결했습니다.")
        else:
            if s:
                add("DU", s)
            for name, label in (("DD", "D패드 아래"), ("DL", "D패드 왼쪽"),
                                ("DR", "D패드 오른쪽")):
                s = detect(j, f"[{label}] 로 쓸 버튼을 누르세요", {"button"})
                if s:
                    add(name, s)
    except (Quit, KeyboardInterrupt):
        print("\n중단했습니다. 저장하지 않았습니다.")
        return 1

    cfg = {"device": DEVICE_MATCH, "bindings": binds}
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print("\n=== 저장 완료 ===")
    for name in ANALOG_OUTPUTS + BUTTON_OUTPUTS:
        if name in binds:
            print(f"  {name:6s} ← " + ", ".join(describe(s, True) for s in binds[name]))
    print(f"\n설정 파일: {config_path}")
    print("이제 run.bat을 실행한 뒤 게임을 켜면 됩니다.")
    return 0


# ----------------------------------------------------------------- 진입점

def main(argv):
    args = list(argv)
    config_path = DEFAULT_CONFIG
    seconds = None
    if "--config" in args:
        i = args.index("--config")
        config_path = args[i + 1]
        del args[i:i + 2]
    if "--seconds" in args:  # 테스트용: 지정한 시간 뒤 자동 종료
        i = args.index("--seconds")
        seconds = float(args[i + 1])
        del args[i:i + 2]
    cmd = args[0] if args else "run"
    if cmd == "setup":
        return setup(config_path)
    if cmd == "run":
        return run(config_path, seconds)
    if cmd == "monitor":
        return monitor()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
