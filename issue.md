# 已知问题 / 注意事项

## 构建环境
- 当前 Windows 宿主 Shell 的 PATH 中没有 `make` 和 `x86_64-w64-mingw32-g++`。
- 项目默认在 **WSL** 中构建，已验证 WSL 内包含：
  - `g++ (Ubuntu 13.3.0)`
  - `GNU Make 4.3`
  - `x86_64-w64-mingw32-g++ (GCC 13-win32)`
- 若要在 Windows 宿主侧直接调用，可执行 `wsl make ...` 或在 WSL 配置集成。

## Python 版本
- WSL 默认环境中 `python3.13` 命令可能不存在，通常使用 `python3`。
- Windows 宿主侧已安装 `Python 3.13.5`。
- `pyproject.toml` 指定 `requires-python = ">=3.13"`。

## 依赖
- Textual 需要通过 pip 安装（见 `requirements.txt`）。
- 开发依赖（pytest）见 `requirements-dev.txt`。
- C++ 核心不依赖第三方库，仅使用 C++17 标准库。

## 跨平台
- C++ 共享库在 Windows 上静态链接 `libgcc` / `libstdc++`，减少运行时依赖。
- Python 侧通过 `sys.platform` 判断加载 `.so` 或 `.dll`。

## 已解决
- Windows 下 pytest 退出时的段错误：由 `thread_local std::string` 析构引起，已改为固定长度 `thread_local char[]` 错误缓冲区。

## 待补充 / 限制
- 搜索当前基于原始文件内容；对已编辑（未保存）的插入/删除内容不会出现在搜索结果中。
- 搜索的 Regex 支持尚未实现（当前仅支持 bytes / hex string）。
- 大文件搜索时结果数有上限（默认 1000），Replace All 目前也受此上限影响。
- 十六进制视图目前是固定页大小（256 字节），未根据终端高度动态调整。
