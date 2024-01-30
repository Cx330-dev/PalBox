#!/bin/sh

echo "CPU 核心数量: $(nproc)"
echo "内存大小: $(free -h | awk '/Mem/ {print $2}')"

UE_TRUE_SCRIPT_NAME=$(echo \"$0\" | xargs readlink -f)
UE_PROJECT_ROOT=$(dirname "$UE_TRUE_SCRIPT_NAME")

chmod +x "$UE_PROJECT_ROOT/Pal/Binaries/Linux/PalServer-Linux-Test"
"$UE_PROJECT_ROOT/Pal/Binaries/Linux/PalServer-Linux-Test" Pal "$@" -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS
