# Agent 全局指引

## 项目概述
`binseek` 是一个基于 Python + C++ 的 TUI 二进制文件查看/搜索/编辑工具。
- **Python 侧**：UI 与业务编排（Textual）。
- **C++ 侧**：核心 IO、搜索、替换算法，编译为共享库。
- **构建**：顶层 `Makefile`，默认在 WSL 中执行，支持 `linux` / `windows` / `test` / `clean`。

## 开发约定
1. **不要直接修改二进制产物**（`binseek/libcore.so`、`binseek/libcore.dll`），应修改 `src/cpp/` 源码后重新 `make`。
2. **Python 与 C++ 边界**：C++ 仅暴露 C API；Python 通过 `binseek/core/_native.py` 的 `ctypes` 调用。
3. **UI 代码**放在 `binseek/ui/`，**编辑模型**放在 `binseek/model/`，**核心包装**放在 `binseek/core/`。
4. 新增功能时应同步补充 pytest 测试，关键 C++ 算法应在 `tests/cpp/` 加小型自测。
5. 保持跨平台：路径处理使用 `pathlib`；C++ 中使用 `#ifdef _WIN32` 区分 Windows 与 POSIX。
6. 不要引入不必要的依赖；C++ 侧尽量只使用标准库。
7. 功能阶段完成后提交git commit，并更新文档。

## 常用命令
```bash
# Linux 共享库
make linux

# Windows DLL（mingw-w64 交叉编译）
make windows

# 运行测试
make test

# 运行程序
python -m binseek [file]
```

## 代码风格
- Python：PEP 8，类型注解可选。
- C++：C++17，清晰的分文件头/源结构，C API 函数使用 `bs_` 前缀。

## 项目文档
- `issue.md` 记录已知问题和注意事项。
- `project.md` 项目规划。