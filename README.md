# vkb2xbox

VKB 조이스틱 입력을 **가상 Xbox 360 컨트롤러**로 바꿔 주는 Windows용 매핑 프로그램입니다.

게임패드만 지원하는 게임(에이스 컴뱃 시리즈 등)을 플라이트 스틱으로 하고 싶을 때 씁니다.
스틱의 축·버튼·햇을 Xbox 패드의 스틱·트리거·버튼에 자유롭게 연결하고, 게임은 평범한 Xbox 360 패드가 꽂힌 것으로 인식합니다.

## 기능

- 축 → 스틱 / 트리거 / 버튼, 버튼·햇 → 버튼 / 스틱 방향 등 자유로운 매핑
- 출력 하나에 입력 여러 개 연결 가능
- 입력 하나로 두 버튼 동시 누르기 (`LB+RB`, `LT+RT`, `L3+R3`)
- 축마다 데드존 설정
- GUI: 스틱을 움직여서 매핑 지정, 가상 패드의 실제 출력을 그림으로 실시간 확인
- CLI: 매핑 마법사(`setup`), 변환 실행(`run`), 원시 입력 확인(`monitor`)

## 설치

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
    "LX+": [{"type": "axis", "index": 0, "sign": 1, "min": 0.02, "max": 1.0}],
    "A":   [{"type": "button", "index": 21}],
    "RX+": [{"type": "hat", "index": 0, "dir": "R"}]
  }
}
```

- `device`: 장치 이름에 이 글자가 들어간 조이스틱을 사용합니다. 다른 회사 스틱이면 이 값을 바꾸세요 (GUI와 `run`에 적용. `setup`·`monitor`는 `vkb2xbox.py`의 `DEVICE_MATCH`를 씁니다).
- 축의 `min`은 데드존, `sign`은 방향입니다.

## 참고

- 게임은 보통 XInput 1번 컨트롤러만 읽습니다. 다른 패드가 꽂혀 있으면 가상 패드가 2번이 될 수 있으니 뽑아 두세요. GUI가 이 경우 경고를 표시합니다.
- 가상 패드를 켜는 순간 Windows가 장치 목록을 다시 훑느라 몇 초 멈출 수 있습니다.
- Windows 전용입니다.
