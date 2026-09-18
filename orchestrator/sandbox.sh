#!/usr/bin/env bash
# SpecPilot 容器沙箱执行器：把"执行安全守则"从提示词纪律变为容器强制。
#
# 用法:  orchestrator/sandbox.sh <项目目录> <命令...>
# 示例:  orchestrator/sandbox.sh examples/todo-cli python3 -m unittest discover -s tests
#
# 强制的边界（对应 SKILL.md"执行安全"五条）:
#   --network none                  网络默认关（外联在物理上不可达，不是"不允许"）
#   -v 项目目录:/work 且仅此挂载    路径收敛：容器内只见项目，项目外不可见
#   --read-only + tmpfs /tmp        根文件系统只读，可写面仅项目目录与 /tmp
#   --cap-drop ALL + no-new-privileges  破坏性命令防火墙：无特权可提
#   -u 宿主UID:GID                  生成的文件归宿主用户，不留 root 残留
#
# 依赖: Docker。需要第三方依赖的项目，先构建含依赖的定制镜像：
#   docker build -t my-sandbox --build-arg ... <你的Dockerfile>   （依赖安装发生在构建期并留痕，运行期无网）
set -euo pipefail

PROJECT_DIR="${1:?用法: sandbox.sh <项目目录> <命令...>}"
shift
IMAGE="${SPECPILOT_SANDBOX_IMAGE:-specpilot-sandbox:latest}"

command -v docker >/dev/null 2>&1 || { echo "错误：需要 Docker" >&2; exit 1; }
[ -d "$PROJECT_DIR" ] || { echo "错误：项目目录不存在：$PROJECT_DIR" >&2; exit 1; }
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"   # 绝对路径

# 镜像不存在则按同目录 Dockerfile 构建（构建期即留痕：镜像内容固定可审计）
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker build -t "$IMAGE" "$(dirname "$0")"

exec docker run --rm \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,size=128m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --memory 2g \
  --cpus 2 \
  --pids-limit 256 \
  -u "$(id -u):$(id -g)" \
  -v "$PROJECT_DIR:/work" \
  -w /work \
  "$IMAGE" \
  "$@"
