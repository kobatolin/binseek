# Agent 指引

## 项目是什么
- `binseek`：Python 3.8+ + Textual 的 TUI 二进制查看/搜索/编辑器。
- C++17 核心（mmap、搜索、编辑）编译为共享库，Python 通过 `binseek/core/_native.py` 用 `ctypes` 调用。
- 目录边界：
  - `binseek/ui/`：Textual 组件（对话框、HexView、状态栏等）。
  - `binseek/model/`：业务模型，主要是 `Buffer`。
  - `binseek/core/`：C API 封装，唯一加载 `libcore.so` / `libcore.dll` 的地方。
  - `src/cpp/`：C++ 源码唯一来源。
  - `tests/`：pytest + `tests/cpp/` 小型 C++ 自测。

## 必须知道的构建事实
- 不要直接改 `binseek/libcore.so` 或 `binseek/libcore.dll`，应改 `src/cpp/` 后重新 `make`。
- 默认在 WSL 中构建；Windows DLL 用 mingw-w64 交叉编译。
  ```bash
  make linux      # -> binseek/libcore.so
  make windows    # -> binseek/libcore.dll
  make test-cpp   # 编译并运行 C++ 自测
  ```
- Windows 宿主侧若没 make/mingw，使用 `wsl make linux` / `wsl make windows`。

## Python 3.8 关键陷阱
- `from __future__ import annotations` 只延迟**函数/变量注解**，**不延迟基类泛型参数**。
- 因此 `ModalScreen[str | None]`、`Container[int | None]` 这类写法在 3.8 运行时会直接报 `TypeError`。
- 对会被运行时求值的类型表达式，统一用 `Optional[...]` / `Union[...]` / `List[...]` 等 `typing` 形式。

## 运行与验证
- 运行前必须已构建对应平台的共享库：
  ```bash
  python -m binseek [file]
  ```
- 提交前必须跑：
  ```bash
  make test-cpp
  python -m pytest tests -q
  ```
  或一次性 `make test`。
- WSL 开发建议使用独立环境 `.venv-linux`，避免覆盖 Windows 的 `.venv`：
  ```bash
  python3 -m venv .venv-linux
  source .venv-linux/bin/activate
  pip install -r requirements-dev.txt
  ```

## 打包分发
- wheel 同时包含 `libcore.dll` 与 `libcore.so`：
  ```bash
  make linux
  make windows
  pip install build
  python -m build --wheel --outdir dist
  ```
- `dist/` 已在 `.gitignore` 中，**不要提交 wheel**。

## 提交约定
- Commit 前缀：`feat:`、`fix:`、`docs:`、`refactor:`、`style:`、`test:`。
- 一个功能点尽量一次 commit；完成后同步更新 README / issue.md / project.md。

## 其他 repo 资源
- `.agents/skills/binseek-test/SKILL.md`：自动化测试工作流说明。
- `issue.md`：已知限制与注意事项。
- `project.md`：项目规划与里程碑。
