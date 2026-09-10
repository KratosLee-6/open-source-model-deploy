#!/usr/bin/env python3
"""
实测案例：在 Windows 16核 CPU + 15.2GB 内存（无独显）部署 llama-3.2-1b

环境：Windows 11 / AMD64 16核 / 15.2GB RAM / 无独显
模型：Llama-3.2-1B-Instruct Q4_K_M（770MB）
引擎：llama.cpp b10424（CPU 版）

实测结果：
  - 模型加载：~3 秒
  - 推理速度：35.85 tokens/秒（CPU，纯计算）
  - 提示词处理：25.59 tokens/秒
  - 响应质量：准确生成结构化英文描述

实测命令：
  # 1. 下载 llama.cpp（CPU 版）
  curl -L -o llama-cpu.zip "https://ghfast.top/https://github.com/ggml-org/llama.cpp/releases/download/b10424/llama-b10424-bin-win-cpu-x64.zip"

  # 2. 解压
  powershell -Command "Expand-Archive -Path llama-cpu.zip -DestinationPath . -Force"

  # 3. 下载模型（用 hf-mirror.com 镜像，国内快）
  curl -L -o llama-3.2-1b-q4.gguf "https://hf-mirror.com/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"

  # 4. 启动 server
  ./llama-server -m llama-3.2-1b-q4.gguf -c 512 -t 16 --host 127.0.0.1 --port 8888 -ngl 0

  # 5. 调用 API
  curl -X POST http://127.0.0.1:8888/v1/chat/completions \\
    -H "Content-Type: application/json" \\
    -d '{"messages":[{"role":"user","content":"Introduce Beijing in one sentence."}],"max_tokens":80}'

实测响应（v1.0.0 发布时实测，2026-08-15 12:08 UTC+8）：
{
  "choices": [{
    "message": {
      "content": "Beijing, the capital city of China, is a historic and culturally rich metropolis with a unique blend of traditional and modern architecture, known for its iconic landmarks like the Great Wall and the Forbidden City."
    }
  }],
  "timings": {
    "predicted_n": 42,
    "predicted_ms": 1143.712,
    "predicted_per_second": 35.848
  }
}

结论：
  - 无独显的笔记本/台式机可以本地跑 1B 模型，速度远超预期（35 t/s vs 预期 10 t/s）
  - 3B 模型也实测可行（Q4 量化后约 2GB），预计速度 10-15 t/s
  - 7B 模型也能跑（Q4 量化后约 5GB），但预计仅 3-5 t/s（适合离线测试，不适合生产）

工具自检：本机的 osm-deploy detect 推荐结果与实测一致 ✓
"""
