# bot-bullet

一款 macOS 菜单栏应用：自动截取你的屏幕，用温柔明日香的语气生成一条 B 站「醒目留言（SC）」风格的弹幕，显示在屏幕左下角。

## 1. 安装

安装包在 `release/bot-bullet.dmg`。
如果需要自己修改代码，请重新打包，参考第5节。

## 2. 使用

1. 点击菜单栏的红底「弹」图标；
2. 点「设置 DeepSeek API Key…」，填入你的 [DeepSeek API Key](https://platform.deepseek.com/) 并保存；
3. 保存后自动开始运行，屏幕左下角约每 15 秒弹出一条弹幕，60 秒后自动消失。

## 3. 常见问题

**想彻底卸载？**
把 Applications 里的 bot-bullet 移到废纸篓即可；配置文件与 API Key 保存在 `~/.config/bot-bullet/config.json`，可一并删除。

## 4. 从源码运行（开发者）

```bash
uv sync
uv run bot-bullet-tray      # 菜单栏应用
uv run bot-bullet           # 无界面的命令行模式（调试用）
```

## 5. 打包

```bash
./package/build_mac.sh
```

脚本会依次完成图标生成、PyInstaller 打包、设置菜单栏常驻，最终产出唯一的安装文件 `release/bot-bullet.dmg`。打包相关的一切脚本都在 `package/` 目录下。
