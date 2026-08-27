#!/usr/bin/env bash
# 一键打包：生成可安装的 bot-bullet.dmg（拖拽安装）
# 用法: ./build_mac.sh     （在任意目录执行均可）
#
# 唯一产物: release/bot-bullet-<版本>.dmg
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

APP_NAME="bot-bullet"
APP_PATH="release/$APP_NAME.app"
BUILD_DIR="package/build"

# 版本号以 pyproject.toml 为唯一来源，打包时写进 .app 并带到 dmg 文件名
VERSION="$(grep -m1 '^version' pyproject.toml | sed 's/.*= *"\(.*\)"/\1/')"
if [ -z "$VERSION" ]; then
  echo "错误: 无法从 pyproject.toml 读取版本号" >&2
  exit 1
fi
DMG_PATH="release/$APP_NAME-$VERSION.dmg"

rm -rf "$APP_PATH" "$DMG_PATH" "$BUILD_DIR" package/bot-bullet.spec

echo "==> 生成应用图标 icns"
# 图标生成用项目虚拟环境 (.venv) 的 python——系统 python 可能没装 PySide6
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python || command -v python3)"
fi
"${PYTHON_BIN}" - <<'PYEOF'
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

ICON_DIR = "package/assets/icon.iconset"

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

os.makedirs(ICON_DIR, exist_ok=True)
entries = [(16,"16x16"),(32,"32x32"),(64,"128x128"),(128,"256x256"),(512,"512x512"),
           (32,"16x16@2x"),(64,"32x32@2x"),(256,"128x128@2x"),(512,"256x256@2x")]
for s, name in entries:
    img = render(s)
    if name.endswith("@2x"):
        img = img.scaled(s // 2, s // 2)
    img.save(f"{ICON_DIR}/icon_{name}.png")
print("iconset 生成完成")
PYEOF
mkdir -p package/assets
iconutil -c icns package/assets/icon.iconset -o package/assets/bot-bullet.icns

echo "==> PyInstaller 打包 .app"
uv run pyinstaller \
  --noconfirm \
  --name "$APP_NAME" \
  --windowed \
  --osx-bundle-identifier com.dirtybottle.bot-bullet \
  --icon "$PROJECT_ROOT/package/assets/bot-bullet.icns" \
  --hidden-import bot_bullet.tools.overlay_server \
  --hidden-import bot_bullet.config \
  --hidden-import bot_bullet.prompt \
  --specpath package --workpath "$BUILD_DIR" --distpath release \
  "$PROJECT_ROOT/package/entry_mac.py"

echo "==> 设置菜单栏常驻 (LSUIElement，不占 Dock)"
plutil -replace LSUIElement -bool true "$APP_PATH/Contents/Info.plist"

echo "==> 写入版本号 v$VERSION"
plutil -replace CFBundleShortVersionString -string "$VERSION" "$APP_PATH/Contents/Info.plist"
plutil -replace CFBundleVersion           -string "$VERSION" "$APP_PATH/Contents/Info.plist"

echo "==> 制作 DMG 安装镜像"
DMG_STAGE="$BUILD_DIR/dmg"
mkdir -p "$DMG_STAGE"
cp -R "$APP_PATH" "$DMG_STAGE/"
ln -s /Applications "$DMG_STAGE/Applications"
hdiutil create -volname "$APP_NAME" \
  -srcfolder "$DMG_STAGE" \
  -ov -format UDZO \
  "$DMG_PATH"

# DMG 已包含完整应用，清理其余中间产物，release 只留 .dmg
rm -rf "$APP_PATH" "$DMG_STAGE" "$PROJECT_ROOT/release/$APP_NAME"

echo ""
echo "✅ 打包完成: $DMG_PATH"
