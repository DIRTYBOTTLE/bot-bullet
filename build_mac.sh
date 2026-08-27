#!/usr/bin/env bash
# 构建 macOS .app（菜单栏弹幕应用）
# 用法: ./build_mac.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 清理旧的构建产物"
rm -rf build dist

echo "==> 生成应用图标 (icon.png -> bot-bullet.icns)"
PYTHON_BIN="$(command -v python || command -v python3)"
"${PYTHON_BIN}" - <<'EOF'
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

def render(size):
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 0))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#ff5c5c"))
    p.drawRoundedRect(int(size*0.08), int(size*0.08), int(size*0.84), int(size*0.84),
                      int(size*0.22), int(size*0.22))
    p.setBrush(QColor("#ffffff"))
    d = size * 0.28
    p.drawEllipse(int((size-d)/2), int((size-d)/2), int(d), int(d))
    p.end()
    return img

import os
os.makedirs("assets/icon.iconset", exist_ok=True)
for s in [16, 32, 64, 128, 256, 512]:
    render(s).save(f"assets/icon.iconset/icon_{s}x{s}.png")
render(32).save("assets/icon.iconset/icon_16x16@2x.png")
render(64).save("assets/icon.iconset/icon_32x32@2x.png")
render(256).save("assets/icon.iconset/icon_128x128@2x.png")
render(512).save("assets/icon.iconset/icon_256x256@2x.png")
print("iconset 生成完成")
EOF
iconutil -c icns assets/icon.iconset -o assets/bot-bullet.icns

echo "==> PyInstaller 打包"
uv run pyinstaller \
  --noconfirm --clean \
  --name bot-bullet \
  --windowed \
  --osx-bundle-identifier com.dirtybottle.bot-bullet \
  --icon assets/bot-bullet.icns \
  --hidden-import bot_bullet.tools.overlay_server \
  --hidden-import bot_bullet.config \
  --hidden-import bot_bullet.prompt \
  entry_mac.py

echo "==> 设置菜单栏常驻 (LSUIElement，不占 Dock)"
plutil -replace LSUIElement -bool true dist/bot-bullet.app/Contents/Info.plist

echo ""
echo "✅ 构建完成: dist/bot-bullet.app"
echo "   首次打开（未签名）: 右键 dist/bot-bullet.app -> 打开"
echo "   调试运行: ./dist/bot-bullet.app/Contents/MacOS/bot-bullet"
