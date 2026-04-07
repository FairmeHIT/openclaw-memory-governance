# Prototype

本目录承载个性化记忆治理原型的实现代码。

建议模块：

- `classifier/`
- `policy/`
- `retrieval_guard/`
- `audit/`
- `sandbox/`

原则：

- 优先外挂式集成 OpenClaw 基线
- 先完成基线对照实验，再逐步增强
- 先实现规则版，再考虑接入 OPA / OpenFGA / gVisor
