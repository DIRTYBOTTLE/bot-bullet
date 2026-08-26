import base64

import mss


def capture(mnts:list[int]):
    monitor_imgs = []
    with mss.MSS() as sct:
        for monitor in sct.monitors[1:]:
            img = sct.grab(monitor)
            monitor_imgs.append(f"data:image/png;base64,{base64.b64encode(mss.tools.to_png(img.rgb, img.size)).decode()}")
    return monitor_imgs