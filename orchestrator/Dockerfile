# SpecPilot 沙箱镜像：极简、非特权、无预置网络工具。
# 由 orchestrator/sandbox.sh 使用；网络隔离、文件系统边界在 docker run 时强制
# （--network none / --read-only / 仅挂载项目目录），不在镜像内承诺。
FROM python:3.12-slim

# 非 root 默认用户；sandbox.sh 运行时还会显式映射宿主 UID/GID，
# 保证挂载目录内生成的文件归宿主用户所有
RUN useradd --create-home --shell /usr/sbin/nologin sandbox
USER sandbox
WORKDIR /work

CMD ["python3"]
