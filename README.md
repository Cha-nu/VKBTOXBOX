# vkb2xbox

VKB 조이스틱(을 비롯한 HOTAS·스로틀·러더 페달) 입력을 **가상 Xbox 360 컨트롤러**로 바꿔 주는 Windows용 매핑 프로그램입니다.

게임패드만 지원하는 게임(에이스 컴뱃 시리즈 등)을 플라이트 스틱으로 하고 싶을 때 씁니다.
스틱의 축·버튼·햇을 Xbox 패드의 스틱·트리거·버튼에 자유롭게 연결하고, 게임은 평범한 Xbox 360 패드가 꽂힌 것으로 인식합니다.

## 기능

- 축 → 스틱 / 트리거 / 버튼, 버튼·햇 → 버튼 / 스틱 방향 등 자유로운 매핑
- **여러 장치 동시 사용**: 스틱 + 별도 스로틀 + 러더 페달처럼 연결된 조이스틱을 모두 인식하고, 매핑마다 어느 장치의 입력인지 기억합니다. 실행 중에 꽂거나 뽑아도 자동으로 따라갑니다
- 출력 하나에 입력 여러 개 연결 가능
- 입력 하나로 두 버튼 동시 누르기 (`LB+RB`, `LT+RT`, `L3+R3`)
- 축마다 데드존 설정
- GUI: 스틱을 움직여서 매핑 지정, 가상 패드의 실제 출력을 그림으로 실시간 확인
- CLI: 매핑 마법사(`setup`), 변환 실행(`run`), 원시 입력 확인(`monitor`)

## 바로 실행 (exe)

Python 없이 쓰려면 [Releases](https://github.com/Cha-nu/VKBTOXBOX/releases)에서 `vkb2xbox.exe`를 받아 실행하면 됩니다.

- 처음 실행하면 제가 쓰는 매핑(VKB Gladiator EVO R 기준)이 기본으로 들어 있습니다. 바꾼 내용은 exe 옆의 `config.json`에 저장됩니다.
- 가상 패드를 만들려면 **ViGEmBus 드라이버**가 필요합니다. 아래 [설치 방법](#vigembus-드라이버-설치)을 참고하세요.
- 직접 빌드하려면 `pip install pyinstaller` 후 `build.bat`을 실행합니다.

## ViGEmBus 드라이버 설치

가상 Xbox 360 컨트롤러를 만드는 드라이버입니다. 한 번만 설치하면 되고, 아래 중 편한 방법 하나를 쓰면 됩니다.

**방법 1 — 프로그램에서 설치**

`vkb2xbox.exe`에서 **가상 Xbox 패드 켜기**를 눌렀을 때 드라이버가 없으면 설치 프로그램을 실행할지 묻습니다. **예**를 누르고 설치를 끝낸 뒤 버튼을 다시 누르세요.

**방법 2 — winget 명령어**

PowerShell이나 명령 프롬프트에서 실행합니다.

```
winget install ViGEm.ViGEmBus
```

**방법 3 — 직접 내려받기**

[ViGEmBus 릴리스 페이지](https://github.com/nefarius/ViGEmBus/releases/latest)에서 `ViGEmBus_x.xx.x_x64_x86_arm64.exe`를 받아 실행합니다.

설치 중 관리자 권한을 묻는 창이 뜨면 허용하세요. 설치 후에도 가상 패드가 만들어지지 않으면 PC를 다시 시작해 보세요.

설치되었는지는 **설정 → 앱 → 설치된 앱**에서 "ViGEm Bus Driver"를 찾거나, 다음 명령으로 확인할 수 있습니다.

```
winget list ViGEm.ViGEmBus
```

## 설치 (소스로 실행)

1. [Python 3](https://www.python.org/downloads/) 설치 (설치할 때 "Add python.exe to PATH" 체크)
2. 패키지 설치

   ```
   pip install -r requirements.txt
   ```

   `vgamepad`를 설치하는 도중 **ViGEmBus 드라이버** 설치 창이 뜹니다. 가상 패드를 만드는 데 필요하니 끝까지 설치하세요.

| 필요한 것 | 용도 |
| --- | --- |
| pygame | 조이스틱 입력 읽기 |
| vgamepad | 가상 Xbox 360 컨트롤러 만들기 |
| ViGEmBus 드라이버 | vgamepad가 쓰는 가상 장치 드라이버 |

## 사용법

### GUI (권장)

`gui.bat`을 실행합니다.

1. 표에서 Xbox 출력 항목을 더블클릭하고, 스틱을 움직이거나 버튼을 누르면 그 입력이 지정됩니다. 축은 원하는 방향으로 끝까지 움직이세요.
2. **가상 Xbox 패드 켜기**를 누릅니다. 오른쪽 그림이 가상 패드의 실제 출력을 보여 줍니다.
3. 창을 켜 둔 채로 게임을 실행합니다.

매핑은 `config.json`에 자동 저장됩니다.

### 명령줄

```
python vkb2xbox.py setup     매핑 마법사
python vkb2xbox.py run       변환 실행 (게임 켜기 전에 실행)
python vkb2xbox.py monitor   스틱의 원시 입력 확인
```

`setup.bat`, `run.bat`으로도 실행할 수 있습니다. `--config <경로>`로 다른 설정 파일을 쓸 수 있습니다.

## 설정 파일

`config.example.json`은 제가 쓰는 매핑 예시입니다. `config.json`으로 복사해서 시작점으로 써도 되지만, 버튼 번호는 스틱 모델과 펌웨어 설정마다 다르므로 직접 다시 지정하는 편이 낫습니다.

```json
{
  "device": "VKB",
  "bindings": {
    "LX+": [{"type": "axis", "index": 0, "sign": 1, "min": 0.02, "max": 1.0, "device": "스틱 이름"}],
    "RT":  [{"type": "axis", "index": 2, "sign": 1, "min": 0.15, "max": 1.0, "device": "스로틀 이름"}],
    "A":   [{"type": "button", "index": 21}],
    "RX+": [{"type": "hat", "index": 0, "dir": "R"}]
  }
}
```

- 각 입력의 `device`: 그 입력이 속한 조이스틱 이름입니다. GUI나 `setup`으로 지정하면 자동으로 들어갑니다. 같은 이름의 장치가 둘이면 두 번째부터 ` #2`가 붙습니다.
- 맨 위의 `device`: 입력에 `device`가 없을 때(예전 버전으로 만든 매핑) 쓸 장치로, 이름에 이 글자가 들어간 조이스틱을 고릅니다.
- 축의 `min`은 데드존, `sign`은 방향입니다.
- 이름에 `Xbox`/`XInput`이 들어간 장치는 입력으로 쓰지 않습니다. 가상 패드 자신의 출력을 다시 읽지 않기 위해서입니다.

## 참고

- 게임은 보통 XInput 1번 컨트롤러만 읽습니다. 다른 패드가 꽂혀 있으면 가상 패드가 2번이 될 수 있으니 뽑아 두세요. GUI가 이 경우 경고를 표시합니다.
- 가상 패드를 켜는 순간 Windows가 장치 목록을 다시 훑느라 몇 초 멈출 수 있습니다.
- Windows 전용입니다.
