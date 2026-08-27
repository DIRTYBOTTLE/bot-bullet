# bot-bullet

一款 macOS 菜单栏应用：自动截取你的屏幕，用温柔明日香的语气生成一条 B 站「醒目留言（SC）」风格的弹幕，显示在屏幕左下角。

![效果展示](docs/效果展示.png)

## 1. 安装

安装包是 `release/bot-bullet.dmg`。双击打开后，把 **bot-bullet** 拖入 Applications 文件夹，然后从启动台或 Spotlight 启动 bot-bullet。

首次启动如果 macOS 提示无法验证开发者：在弹窗里点「打开」即可。
首次截屏时系统会请求「屏幕录制」权限，**必须允许**，否则截屏全黑、弹幕无内容。

需要自己改代码重新打包的话，参考第 5 节。

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
