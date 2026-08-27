# 深度学习与计算机视觉 · AI-native 课程幻灯片

华中科技大学《深度学习与计算机视觉》课程（王兴刚）的 HTML 课件，由原 PPT 重新设计而来：浅色学术 keynote 风、自绘 SVG 示意图、重点提示框、结构化小结与经核实的参考文献。

## 使用

直接用浏览器打开 `index.html`（无需服务器、可离线）：

- `←` / `→` / 空格：翻页；`Home` / `End`：首末页
- `O` 或 `Esc`：总览模式（缩略图跳转）
- `F`：全屏；支持 URL `#/N` 定位与触摸滑动

## 内容

| 文件 | 讲次 | 页数 |
|---|---|---|
| `lecture1.html` | 第 1 讲 深度学习与计算机视觉简介 | 57 |
| `lecture2.html` | 第 2 讲 从 AlexNet 到 ChatGPT | 71 |
| `lecture3.html` | 第 3 讲 从浅层到深度的表征学习 | 78 |

## 目录结构

- `css/slides.css` / `js/slides.js` — 共享设计系统与导航运行时（1280×720 画布等比缩放）
- `demo.html` — 全部版式组件的用法示范
- `assets/lectureN/` — 各讲图片素材（自 PPT 抽取并去重）
- `extract.py` / `build.py` / `data/` — 早期 PPT→HTML 转换流水线（存档，现行课件为人工重新设计）
