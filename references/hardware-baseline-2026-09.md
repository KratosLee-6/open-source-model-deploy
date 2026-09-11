# 硬件价格基准快照 · 2026-09-11T14:24:13

> 自动生成：`python3 scripts/refresh_gpu_prices.py`
> 更新频率：每周一次（GitHub Actions）
> 数据源：参考价（NVIDIA/Apple 官网反爬严）+ 云租公开价

> ⚠️ **注意**：以下价格是 **参考价**，实际购买/租赁请以电商实时报价为准。误差 ±10-30%。

## NVIDIA GeForce（消费级）

| 型号 | 显存 | TDP | 价格 (USD) | 档位 |
|---|---|---|---|---|
| RTX 5060 Ti 16GB | 16 GB | 180 W | $429 | consumer |
| RTX 5070 12GB | 12 GB | 250 W | $549 | consumer |
| RTX 5070 Ti 16GB | 16 GB | 300 W | $749 | consumer |
| RTX 5080 16GB | 16 GB | 360 W | $999 | consumer |
| RTX 5090 32GB | 32 GB | 575 W | $1999 | consumer |

## NVIDIA 数据中心

| 型号 | 显存 | TDP | 价格 (USD) | 档位 |
|---|---|---|---|---|
| L4 24GB | 24 GB | 72 W | $2400 | datacenter |
| L40S 48GB | 48 GB | 350 W | $9800 | datacenter |
| A100 80GB | 80 GB | 400 W | $12000 | datacenter |
| H100 80GB PCIe | 80 GB | 350 W | $25000 | datacenter |
| H100 80GB SXM | 80 GB | 700 W | $30000 | datacenter |
| H200 141GB | 141 GB | 700 W | $35000 | datacenter |

## Apple Silicon（统一内存）

| 型号 | 统一内存 | 价格 (USD) | 档位 |
|---|---|---|---|
| Mac mini M4 Pro 24GB | 24 GB | $1399 | consumer |
| Mac mini M4 Max 36GB | 36 GB | $1999 | consumer |
| Mac Studio M4 Max 64GB | 64 GB | $3599 | consumer |
| Mac Studio M3 Ultra 192GB | 192 GB | $5999 | consumer |
| Mac Pro M2 Ultra 192GB | 192 GB | $12999 | workstation |

## 云租按需价格（USD/小时 + 包月估算）

| 实例规格 | 每小时 | 包月估算 (730h) | 厂商 |
|---|---|---|---|
| AWS p4d.24xlarge (8× A100 40GB) | $32.77 | $24,284 | AWS |
| AWS p5.48xlarge (8× H100 80GB) | $98.32 | $72,851 | AWS |
| AliyC GPU gn7 (8× A100 80GB) | $30.43 | $22,063 | Aliyun |
| AliyC GPU gn7e (8× A100 80GB) | $38.52 | $28,103 | Aliyun |
| AliyC GPU gn8 (8× H100 80GB) | $78.5 | $57,186 | Aliyun |
| AutoDL RTX 4090 单卡 | $1.2 | $864 | AutoDL |
| AutoDL A100 80GB 单卡 | $4.5 | $3,276 | AutoDL |
| AutoDL H100 80GB 单卡 | $10.0 | $7,200 | AutoDL |

## 推荐组合（按预算）

| 预算 | 推荐方案 | 月成本 | 适用模型 |
|---|---|---|---|
| **0 元** | 笔记本（无独显）| $0 | 1.5-3B Q4 量化 |
| **$500-800** | RTX 5060 Ti 16GB | $0 (一次性) | 8-14B Q4 |
| **$1000-1500** | RTX 5080 16GB | $0 (一次性) | 14-32B Q4 |
| **$2000-2500** | RTX 5090 32GB | $0 (一次性) | 70B Q4 / 32B FP16 |
| **$2400-3500** | 1× L4 24GB 服务器 | $0 (一次性) | 服务端 13B-30B |
| **$150-500/月** | AutoDL 单卡按需 | $150-500 | 14B-70B 按需 |
| **$3000-7000/月** | AutoDL/A100 包月 | $3000-7000 | 70B 满血生产 |
| **$7000-30000/月** | 阿里云 gn7/gn8 | $7000-30000 | 671B MoE 生产 |
| **$20000-70000/月** | AWS p4d/p5 | $24000-73000 | 1T MoE 顶级 |

---

**快照时间**: 2026-09-11T14:24:13
**下次更新**: 下周一北京时间 8:00