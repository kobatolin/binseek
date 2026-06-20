# binseek 项目规划

## 项目目标
构建一个纯 TUI 二进制文件查看/搜索/编辑工具 `binseek`：
- 无 GUI，跨平台 x86-64 Windows / Linux
- 菜单栏 + 快捷键
- 快速打开大文件
- Python 负责 UI 与业务编排，C++ 负责核心算法与 IO
- 使用 Makefile 构建，Windows DLL 在 WSL 中用 mingw-w64 交叉编译

## 技术选型
| 层级 | 选型 | 说明 |
|---|---|---|
| TUI | Python 3.13 + Textual | 原生菜单、对话框、快捷键，跨平台体验好 |
| 核心算法/IO | C++17 + ctypes C API | 独立共享库，避免 C++ ABI 问题 |
| 构建 | 顶层 Makefile | `make linux` / `make windows` / `make test` / `make clean` |
| 打包 | pyproject.toml + requirements.txt | 标准 Python 项目 |

## 目录结构
```
binseek/
├── binseek/              # Python 包
│   ├── app.py            # Textual App
│   ├── __main__.py       # python -m binseek
│   ├── core/_native.py   # ctypes 加载
│   ├── model/buffer.py   # 编辑模型
│   └── ui/               # 各 UI 组件
├── src/cpp/              # C++ 核心
├── tests/                # pytest + C++ 自测
├── Makefile
├── pyproject.toml
├── requirements.txt
└── .gitignore
```

## 核心功能
- 只读 mmap 打开文件（Windows `CreateFileMapping`，Linux `mmap`）
- Boyer-Moore-Horspool 字节搜索
- 修改区间模型：覆盖/插入/删除，自动合并，保存时顺序写出
- 菜单/快捷键：Open/Save/Save As/Find/Replace/Goto/Quit

## 开发工作流
1. 创建并激活虚拟环境：
   ```bash
   python3.13 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```
2. 修改 C++ 代码后重新构建：
   ```bash
   wsl make linux
   wsl make windows
   ```
3. 每次提交前运行测试：
   ```bash
   wsl make test-cpp
   python -m pytest tests -q
   ```
4. 按里程碑做小而清晰的 git commit，消息格式如 `feat:`、`fix:`、`docs:`、`refactor:`。

## 里程碑
1. M0：仓库初始化 + Makefile + .gitignore
2. M1：C++ mmap + C API + ctypes 加载
3. M2：搜索/替换/保存算法
4. M3：Textual UI 骨架（菜单、hex 视图、状态栏）
5. M4：查找/替换/跳转对话框
6. M5：测试 + README + git commit
