# 如何重新生成 json2chart.difypkg

`.difypkg` 是 Dify 插件的标准打包格式，由 **Dify CLI**（dify-plugin）根据当前仓库代码与 `manifest.yaml` 生成。

## 方式一：GitHub Actions 手动打包（推荐，尤其适合 Windows）

项目已提供**只生成、不发布**的 workflow（仅打包为 .difypkg 并供下载，不会提交到 dify-plugins 或发布市场），无需在本机安装 CLI：

1. 打开仓库 **Actions** 页：`https://github.com/<你的用户名>/json2chart/actions`
2. 左侧选择 **「Package Plugin (Manual, No Publish)」**
3. 点击 **「Run workflow」**，选择分支后运行
4. 运行结束后，在该次 Run 的 **Artifacts** 中下载 `difypkg`，解压得到 `json2chart-<version>.difypkg`
5. 若需要根目录名为 `json2chart.difypkg`，可将该文件重命名

这样在 Windows 上也可随时重新生成安装包，无需安装 Dify CLI。

## 方式二：本机使用 Dify CLI

### 安装 CLI

- **macOS**（推荐）：
  ```bash
  brew tap langgenius/dify
  brew install dify
  ```
- **Linux**：从 [dify-plugin-daemon Releases](https://github.com/langgenius/dify-plugin-daemon/releases) 下载对应架构的二进制（如 `dify-plugin-linux-amd64`），加执行权限并放入 `PATH`。
- **Windows**：官方未提供 Windows 版 CLI，可在 **WSL** 中按 Linux 方式安装并在项目目录下执行打包命令。

### 打包命令

在**项目根目录**（包含 `manifest.yaml` 的目录）执行：

```bash
# 输出文件名将根据 manifest.yaml 的 name 和 version 生成，例如 json2chart-1.2.0.difypkg
dify-plugin plugin package . -o json2chart-1.2.0.difypkg
```

或使用默认输出名（通常为 `plugin.difypkg`，以 CLI 为准）：

```bash
dify-plugin plugin package .
```

生成后的 `.difypkg` 可用于：

- 在 Dify 控制台「插件」中本地安装
- 提交到 Dify 插件市场

## 打包时会包含/排除什么

- 包含：`manifest.yaml`、`provider/`、`tools/`、`main.py`、`requirements.txt`、图标等插件运行所需文件
- 排除：由 `.difyignore` 和 `.gitignore` 等规则决定的文件（如 `.git/`、`__pycache__/`、`.env`、`build/` 等）

## 发布到市场时的自动打包

若通过 **Release 发布**，已有的 **Plugin Publish Workflow** 会在发布时自动打包并提交流程（如创建 PR 到 dify-plugins 等）。若仅需本地或自己使用安装包，用上面的**方式一**或**方式二**即可。
