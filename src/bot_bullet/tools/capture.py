import base64

import mss


def capture(monitors: list[int] | None = None) -> list[str]:
    with mss.MSS() as sct:
        selected = monitors or list(range(1, len(sct.monitors)))
        invalid = [i for i in selected if i < 1 or i >= len(sct.monitors)]
        if invalid:
            raise ValueError(f"无效的显示器索引 {invalid}，可用范围是 1~{len(sct.monitors) - 1}")
        monitor_imgs = []
        for i, monitor in enumerate(sct.monitors[1:], 1):
            if i not in selected:
                continue
            img = sct.grab(monitor)
            monitor_imgs.append(
                f"data:image/png;base64,{base64.b64encode(mss.tools.to_png(img.rgb, img.size)).decode()}"
            )
    return monitor_imgs