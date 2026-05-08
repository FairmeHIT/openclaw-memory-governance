# 技术分享 PPT：HTML 详细版

更新日期：2026-04-29  
配套正文：[tech-sharing-report.md](./tech-sharing-report.md)  
建议时长：25-30 分钟  
建议用法：在 Markdown 预览或支持 HTML 的编辑器中打开，每个 `<section class="slide">` 都是 16:9 页面，可单页截图或复制到 PPTX。

<style>
:root {
  --bg: #f4f6f8;
  --paper: #fbfbf8;
  --ink: #1c2430;
  --muted: #637083;
  --line: #d8dee8;
  --blue: #2f63d7;
  --teal: #0f8b8d;
  --green: #2f9e5b;
  --amber: #d19122;
  --red: #c94848;
  --violet: #7158c8;
  --soft-blue: #e9f0ff;
  --soft-teal: #e6f5f3;
  --soft-green: #e8f5ed;
  --soft-amber: #fff3dc;
  --soft-red: #fdeaea;
  --soft-violet: #f0edff;
}

.deck {
  display: grid;
  gap: 32px;
  padding: 32px;
  background: var(--bg);
  overflow-x: auto;
}

.slide {
  position: relative;
  width: 1600px;
  height: 900px;
  box-sizing: border-box;
  padding: 62px 72px 58px;
  overflow: hidden;
  background: var(--paper);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 8px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
  box-shadow: 0 18px 50px rgba(28, 36, 48, 0.10);
}

.slide::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 8px;
  background: linear-gradient(90deg, var(--blue), var(--teal), var(--amber), var(--red));
}

.slide::after {
  content: attr(data-page);
  position: absolute;
  right: 56px;
  bottom: 32px;
  color: #8b96a6;
  font-size: 22px;
  font-weight: 700;
}

.eyebrow {
  margin: 0 0 14px;
  color: var(--blue);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0;
}

h1, h2, h3, p {
  margin: 0;
  letter-spacing: 0;
}

h1 {
  max-width: 1100px;
  font-size: 66px;
  line-height: 1.12;
  font-weight: 850;
}

h2 {
  font-size: 50px;
  line-height: 1.14;
  font-weight: 850;
}

h3 {
  font-size: 30px;
  line-height: 1.22;
  font-weight: 820;
}

.subtitle {
  margin-top: 22px;
  max-width: 1080px;
  color: var(--muted);
  font-size: 30px;
  line-height: 1.46;
}

.kicker {
  margin-top: 22px;
  color: var(--muted);
  font-size: 25px;
  line-height: 1.42;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.wide-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 34px;
}

.panel {
  border: 2px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
  padding: 26px;
}

.panel.blue { background: var(--soft-blue); border-color: #c9d8ff; }
.panel.teal { background: var(--soft-teal); border-color: #c8e9e4; }
.panel.green { background: var(--soft-green); border-color: #ccebd8; }
.panel.amber { background: var(--soft-amber); border-color: #f2d7a2; }
.panel.red { background: var(--soft-red); border-color: #f1caca; }
.panel.violet { background: var(--soft-violet); border-color: #dcd4ff; }

.small-title {
  color: var(--muted);
  font-size: 21px;
  font-weight: 850;
  text-transform: uppercase;
}

.big-number {
  margin-top: 10px;
  font-size: 58px;
  line-height: 1;
  font-weight: 900;
}

.metric-label {
  margin-top: 10px;
  color: var(--muted);
  font-size: 23px;
  line-height: 1.28;
}

.list {
  display: grid;
  gap: 16px;
  margin-top: 20px;
}

.item {
  display: grid;
  grid-template-columns: 26px 1fr;
  gap: 14px;
  align-items: start;
  color: #2c3646;
  font-size: 25px;
  line-height: 1.34;
}

.dot {
  width: 14px;
  height: 14px;
  margin-top: 10px;
  border-radius: 50%;
  background: var(--blue);
}

.dot.teal { background: var(--teal); }
.dot.green { background: var(--green); }
.dot.amber { background: var(--amber); }
.dot.red { background: var(--red); }
.dot.violet { background: var(--violet); }

.flow {
  display: flex;
  align-items: stretch;
  gap: 14px;
}

.flow-step {
  flex: 1;
  min-height: 120px;
  border: 2px solid var(--line);
  border-radius: 8px;
  background: #fff;
  padding: 22px;
}

.flow-step.blue { background: var(--soft-blue); border-color: #c9d8ff; }
.flow-step.teal { background: var(--soft-teal); border-color: #c8e9e4; }
.flow-step.green { background: var(--soft-green); border-color: #ccebd8; }
.flow-step.amber { background: var(--soft-amber); border-color: #f2d7a2; }
.flow-step.red { background: var(--soft-red); border-color: #f1caca; }
.flow-step.violet { background: var(--soft-violet); border-color: #dcd4ff; }

.flow-step strong {
  display: block;
  font-size: 27px;
  line-height: 1.2;
}

.flow-step span {
  display: block;
  margin-top: 10px;
  color: var(--muted);
  font-size: 21px;
  line-height: 1.32;
}

.arrow {
  display: grid;
  place-items: center;
  color: var(--muted);
  font-size: 34px;
  font-weight: 800;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 23px;
  line-height: 1.25;
}

.table th {
  color: var(--muted);
  font-size: 20px;
  text-align: left;
  border-bottom: 2px solid var(--line);
  padding: 12px 12px;
}

.table td {
  border-bottom: 1px solid var(--line);
  padding: 14px 12px;
  vertical-align: middle;
  overflow-wrap: anywhere;
}

.table strong {
  font-weight: 850;
}

code {
  padding: 2px 6px;
  border-radius: 6px;
  background: #eef2f7;
  color: #2c3646;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.9em;
}

.tag {
  display: inline-block;
  padding: 5px 11px;
  border-radius: 8px;
  background: #eef2f7;
  color: #445164;
  font-size: 20px;
  font-weight: 800;
}

.tag.blue { background: var(--soft-blue); color: var(--blue); }
.tag.teal { background: var(--soft-teal); color: var(--teal); }
.tag.green { background: var(--soft-green); color: var(--green); }
.tag.amber { background: var(--soft-amber); color: #9a6400; }
.tag.red { background: var(--soft-red); color: var(--red); }
.tag.violet { background: var(--soft-violet); color: var(--violet); }

.bar-chart {
  display: grid;
  gap: 17px;
}

.bar-row {
  display: grid;
  grid-template-columns: 238px 1fr 92px;
  gap: 16px;
  align-items: center;
}

.bar-row.compact {
  grid-template-columns: 178px 1fr 76px;
}

.bar-label {
  font-size: 22px;
  font-weight: 780;
  color: #2c3646;
}

.bar-track {
  height: 28px;
  border-radius: 8px;
  background: #e7ebf1;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  width: var(--v);
  border-radius: 8px;
  background: var(--blue);
}

.bar-fill.teal { background: var(--teal); }
.bar-fill.green { background: var(--green); }
.bar-fill.amber { background: var(--amber); }
.bar-fill.red { background: var(--red); }
.bar-fill.violet { background: var(--violet); }

.bar-value {
  font-size: 22px;
  font-weight: 850;
  text-align: right;
}

.columns {
  display: grid;
  grid-template-columns: repeat(var(--cols), 1fr);
  gap: 22px;
  align-items: end;
  height: 260px;
  padding: 20px 16px 0;
  border-left: 2px solid var(--line);
  border-bottom: 2px solid var(--line);
}

.column-wrap {
  display: grid;
  grid-template-rows: 1fr auto auto;
  height: 100%;
  align-items: end;
  gap: 10px;
}

.column {
  width: 100%;
  height: var(--h);
  min-height: 4px;
  border-radius: 8px 8px 0 0;
  background: var(--blue);
}

.column.teal { background: var(--teal); }
.column.green { background: var(--green); }
.column.amber { background: var(--amber); }
.column.red { background: var(--red); }
.column.violet { background: var(--violet); }

.column-number {
  color: var(--ink);
  font-size: 23px;
  font-weight: 880;
  text-align: center;
}

.column-label {
  min-height: 40px;
  color: var(--muted);
  font-size: 18px;
  font-weight: 760;
  text-align: center;
  line-height: 1.15;
}

.timeline {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.timeline-step {
  min-height: 170px;
  padding: 18px;
  border: 2px solid var(--line);
  border-radius: 8px;
  background: #fff;
}

.timeline-step b {
  display: block;
  color: var(--blue);
  font-size: 28px;
}

.timeline-step span {
  display: block;
  margin-top: 12px;
  font-size: 20px;
  line-height: 1.28;
}

.matrix {
  display: grid;
  border: 2px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}

.matrix.cols-4 { grid-template-columns: 1.1fr repeat(3, 1fr); }
.matrix.cols-5 { grid-template-columns: 1.1fr repeat(4, 1fr); }
.matrix.cols-6 { grid-template-columns: 1.2fr repeat(5, 1fr); }

.cell {
  min-height: 70px;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  background: #fff;
  font-size: 22px;
  line-height: 1.2;
}

.cell.header {
  background: #eef2f7;
  color: var(--muted);
  font-size: 20px;
  font-weight: 850;
}

.cell.good { background: var(--soft-green); color: #1d6d3b; font-weight: 850; }
.cell.warn { background: var(--soft-amber); color: #8f5e00; font-weight: 850; }
.cell.bad { background: var(--soft-red); color: #a73535; font-weight: 850; }
.cell.info { background: var(--soft-blue); color: var(--blue); font-weight: 850; }

.quote {
  padding: 24px 28px;
  border-left: 8px solid var(--blue);
  background: #fff;
  color: #263141;
  font-size: 30px;
  line-height: 1.42;
  font-weight: 760;
}

.diagram-box {
  border: 2px solid var(--line);
  border-radius: 8px;
  background: #fff;
  padding: 24px;
}

.phone {
  width: 260px;
  height: 500px;
  border: 8px solid #242d3a;
  border-radius: 42px;
  background: linear-gradient(180deg, #ffffff, #edf3f7);
  box-shadow: 0 12px 28px rgba(28, 36, 48, 0.14);
  padding: 44px 24px 28px;
}

.phone-line {
  height: 22px;
  margin-bottom: 16px;
  border-radius: 8px;
  background: #d9e3ee;
}

.phone-line.short { width: 62%; }
.phone-line.mid { width: 82%; }
.phone-chip {
  display: inline-block;
  margin: 8px 8px 0 0;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--soft-blue);
  color: var(--blue);
  font-size: 17px;
  font-weight: 850;
}

.stack {
  display: grid;
  gap: 18px;
}

.split-title {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: start;
  gap: 20px;
}

.footer-note {
  position: absolute;
  left: 72px;
  bottom: 32px;
  max-width: 1050px;
  color: #7a8798;
  font-size: 19px;
}

.speaker-notes {
  width: 1600px;
  box-sizing: border-box;
  padding: 18px 28px;
  border: 1px solid #d8dee8;
  border-radius: 8px;
  background: #ffffff;
  color: #2c3646;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
  font-size: 18px;
  line-height: 1.55;
}

@media print {
  @page { size: 16in 9in; margin: 0; }
  .deck { padding: 0; gap: 0; background: #fff; }
  .slide { border: 0; border-radius: 0; box-shadow: none; page-break-after: always; }
  .speaker-notes { display: none; }
}
</style>

<div class="deck">

<section class="slide" id="slide-01" data-page="01 / 19">
  <div class="wide-grid" style="align-items:center; height:100%;">
    <div>
      <p class="eyebrow">OpenClaw 个性化记忆治理原型验证</p>
      <h1>手机智能体长期记忆治理</h1>
      <p class="subtitle">从可检索上下文到可治理数据资产：让记忆能分类、能授权、能降级使用、能受控流动、能被审计证明。</p>
      <div class="quote" style="margin-top:46px;">今天分享的不是“怎么让智能体记得更多”，而是当智能体已经能长期记住用户之后，怎样让这些记忆可控、可用、可证明。</div>
    </div>
    <div class="diagram-box" style="display:grid; grid-template-columns:300px 1fr; gap:30px; align-items:center;">
      <div class="phone">
        <div class="phone-line short"></div>
        <div class="phone-line mid"></div>
        <div class="phone-line"></div>
        <span class="phone-chip">偏好</span>
        <span class="phone-chip">日程</span>
        <span class="phone-chip">工作上下文</span>
        <span class="phone-chip">跨端连续</span>
      </div>
      <div class="stack">
        <div class="flow-step"><strong>保存</strong><span>本地工作区文件与 session 记录</span></div>
        <div class="flow-step"><strong>对象化</strong><span>切成可治理 memory object</span></div>
        <div class="flow-step"><strong>召回与使用</strong><span>索引、检索、策略前置、输出形态控制</span></div>
        <div class="flow-step"><strong>同步与共享</strong><span>摘要、策略、tombstone、审计事件受控流动</span></div>
      </div>
    </div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
开场先把主题从“记忆能力”拉到“记忆治理”。强调 OpenClaw 的价值在于把记忆外显为工程对象，因此有机会做分类、授权、审计和同步控制。
</details>

<section class="slide" id="slide-02" data-page="02 / 19">
  <p class="eyebrow">问题引入</p>
  <h2>长期记忆正在从能力问题变成治理问题</h2>
  <p class="subtitle">当记忆从一次 prompt 的上下文，变成可保存、可索引、可召回、可同步的数据，它就需要数据治理，而不只是上下文工程。</p>
  <div class="flow" style="margin-top:46px;">
    <div class="flow-step blue"><strong>即时对话能力</strong><span>一次任务内使用上下文，生命周期短，边界相对清晰。</span></div>
    <div class="arrow">→</div>
    <div class="flow-step teal"><strong>长期个性化能力</strong><span>用户偏好、任务习惯、历史决策反复影响未来任务。</span></div>
    <div class="arrow">→</div>
    <div class="flow-step amber"><strong>持久化记忆资产</strong><span>落到文件、索引、向量和检索链路中，能被多次复用。</span></div>
    <div class="arrow">→</div>
    <div class="flow-step red"><strong>跨域流动风险</strong><span>跨设备、跨应用、第三方工具和多 agent 协作会放大边界问题。</span></div>
  </div>
  <div class="grid-3" style="margin-top:48px;">
    <div class="panel blue"><div class="small-title">记忆形态</div><div class="big-number">文件 + 索引</div><div class="metric-label">从不可见模型状态变成可观察工程对象</div></div>
    <div class="panel amber"><div class="small-title">治理挑战</div><div class="big-number">反复召回</div><div class="metric-label">一次误召回会在未来任务中持续复现</div></div>
    <div class="panel red"><div class="small-title">核心问题</div><div class="big-number">该不该用</div><div class="metric-label">不能只问相关性，还要问场景、用途和权限</div></div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这一页把“为什么现在讨论”说清楚。记忆不是临时文本，而是长期数据资产；治理问题来自持久化、检索和流动。
</details>

<section class="slide" id="slide-03" data-page="03 / 19">
  <p class="eyebrow">OpenClaw 视角</p>
  <h2>OpenClaw 让记忆可工程化，也让风险可放大</h2>
  <div class="grid-2" style="margin-top:40px;">
    <div class="panel green" style="min-height:520px;">
      <h3>机会：记忆外显为工程对象</h3>
      <div class="list">
        <div class="item"><span class="dot green"></span><span>明文工作区文件与 session 记录，便于观察和复现实验。</span></div>
        <div class="item"><span class="dot green"></span><span>chunk、SQLite、FTS、向量或混合检索链路，便于插入治理控制点。</span></div>
        <div class="item"><span class="dot green"></span><span>多 agent、多 workspace、本地优先，为个性化和跨域协作提供基础。</span></div>
        <div class="item"><span class="dot green"></span><span>沙箱、技能和审计日志可以连接到记忆使用过程。</span></div>
      </div>
    </div>
    <div class="panel red" style="min-height:520px;">
      <h3>风险：工程化不等于天然安全</h3>
      <div class="list">
        <div class="item"><span class="dot red"></span><span>文件不是硬隔离边界，普通内容和高敏片段容易混在一起。</span></div>
        <div class="item"><span class="dot red"></span><span>检索天然偏相关性，不天然理解域隔离、用途约束和生命周期。</span></div>
        <div class="item"><span class="dot red"></span><span>多 agent 与第三方工具会带来 role confusion、memory bleed 和外传风险。</span></div>
        <div class="item"><span class="dot red"></span><span>默认同步 raw memory 会把单机风险放大成多端风险。</span></div>
      </div>
    </div>
  </div>
  <div class="quote" style="margin-top:38px;">本项目选择 OpenClaw 做验证，是因为它把长期记忆外显化了；可观察是治理起点，但不是安全边界本身。</div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这一页不要把 OpenClaw 说成问题来源，而是说它提供了可治理的工程表面。机会与风险同时来自“记忆外显化”。
</details>

<section class="slide" id="slide-04" data-page="04 / 19">
  <p class="eyebrow">核心矛盾</p>
  <h2>更懂用户 vs 更少暴露用户</h2>
  <div class="grid-2" style="margin-top:46px;">
    <div class="panel blue" style="min-height:450px;">
      <h3>更懂用户</h3>
      <div class="list">
        <div class="item"><span class="dot blue"></span><span>偏好、习惯、日程、工作上下文能长期保持。</span></div>
        <div class="item"><span class="dot blue"></span><span>智能体能跨任务延续状态，减少重复解释成本。</span></div>
        <div class="item"><span class="dot blue"></span><span>跨设备保留个性化体验，手机、桌面和工具链协同。</span></div>
        <div class="item"><span class="dot blue"></span><span>第三方应用可以在授权范围内复用部分记忆价值。</span></div>
      </div>
    </div>
    <div class="panel red" style="min-height:450px;">
      <h3>更少暴露用户</h3>
      <div class="list">
        <div class="item"><span class="dot red"></span><span>域隔离：个人域、工作域、第三方域不能随意串扰。</span></div>
        <div class="item"><span class="dot red"></span><span>用途限制：同一条记忆在不同场景下输出形态不同。</span></div>
        <div class="item"><span class="dot red"></span><span>原文最小化：高敏内容参与计算，但不默认暴露原文。</span></div>
        <div class="item"><span class="dot red"></span><span>可撤销、可过期、可审计：记忆必须有生命周期。</span></div>
      </div>
    </div>
  </div>
  <div class="matrix cols-4" style="margin-top:42px;">
    <div class="cell header">路线</div><div class="cell header">智能体验</div><div class="cell header">隐私风险</div><div class="cell header">结论</div>
    <div class="cell">只追求记忆能力</div><div class="cell good">高</div><div class="cell bad">高</div><div class="cell warn">聪明但失控</div>
    <div class="cell">只做简单拦截</div><div class="cell bad">低</div><div class="cell good">低</div><div class="cell warn">安全但不个性化</div>
    <div class="cell">记忆治理路线</div><div class="cell good">尽量保留</div><div class="cell good">可控可证</div><div class="cell info">每次使用都带边界</div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
核心冲突不是“要不要记忆”，而是“怎样让记忆参与任务时仍然带边界”。这页为后面四个创新点铺路。
</details>

<section class="slide" id="slide-05" data-page="05 / 19">
  <p class="eyebrow">总体方案</p>
  <h2>从上下文文件到可治理数据资产</h2>
  <p class="subtitle">四个创新点按问题递进：先把记忆变成治理对象，再控制召回、控制输出形态，最后控制跨端流动；审计贯穿全链路。</p>
  <div class="flow" style="margin-top:44px;">
    <div class="flow-step blue"><strong>1. 记忆资产化</strong><span>content + representation + policy + lifecycle + audit identity</span></div>
    <div class="arrow">→</div>
    <div class="flow-step teal"><strong>2. 记忆防火墙</strong><span>相关性之外，增加域、用途、等级和生命周期判断</span></div>
    <div class="arrow">→</div>
    <div class="flow-step amber"><strong>3. 可用不可见</strong><span>摘要、脱敏、派生结果、沙箱，而不是原文裸露</span></div>
    <div class="arrow">→</div>
    <div class="flow-step green"><strong>4. 受控流动</strong><span>summary、policy、tombstone、DP update 受控同步</span></div>
  </div>
  <div class="matrix cols-5" style="margin-top:48px;">
    <div class="cell header">层次</div><div class="cell header">输入</div><div class="cell header">控制点</div><div class="cell header">输出</div><div class="cell header">证明方式</div>
    <div class="cell">资产化</div><div class="cell">session 文件</div><div class="cell">分类与元数据</div><div class="cell">memory object</div><div class="cell">覆盖率、完整率、分布</div>
    <div class="cell">防火墙</div><div class="cell">query + candidates</div><div class="cell">policy decision</div><div class="cell">allow / deny / downgrade</div><div class="cell">越权率、暴露率</div>
    <div class="cell">可用不可见</div><div class="cell">高敏记忆</div><div class="cell">output shape</div><div class="cell">derived result / sandbox</div><div class="cell">任务成功、最小必要</div>
    <div class="cell">受控流动</div><div class="cell">跨端记忆</div><div class="cell">sync policy</div><div class="cell">summary + tombstone</div><div class="cell">重识别、撤销、stale recall</div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这页是全场地图。不要把实验作为主线，要把实验放到每个创新点之后作为证据。
</details>

<section class="slide" id="slide-06" data-page="06 / 19">
  <p class="eyebrow">创新点一：记忆资产化</p>
  <h2>不是给文件打标签，而是让每条记忆带治理属性</h2>
  <div class="wide-grid" style="margin-top:42px;">
    <div>
      <div class="quote">memory = content + representation + policy + lifecycle + audit identity</div>
      <div class="grid-2" style="margin-top:28px;">
        <div class="panel blue">
          <h3>内容表示</h3>
          <div class="list">
            <div class="item"><span class="dot blue"></span><span>raw_text</span></div>
            <div class="item"><span class="dot blue"></span><span>retrieval_text</span></div>
            <div class="item"><span class="dot blue"></span><span>summary / embedding / index entry</span></div>
          </div>
        </div>
        <div class="panel teal">
          <h3>治理属性</h3>
          <div class="list">
            <div class="item"><span class="dot teal"></span><span>privacy_level、domain、purpose_allow</span></div>
            <div class="item"><span class="dot teal"></span><span>lifecycle、sync_policy、index_policy</span></div>
            <div class="item"><span class="dot teal"></span><span>audit_id、policy_version、source</span></div>
          </div>
        </div>
      </div>
    </div>
    <div class="diagram-box">
      <h3>治理粒度从文件级下降到可召回对象级</h3>
      <div class="stack" style="margin-top:24px;">
        <div class="panel red" style="padding:20px;"><span class="tag red">文件级</span><p class="kicker">一份 session 文件里混着普通偏好、路径线索、工作上下文和高敏内容；文件被打成高敏后，普通内容也一起被误杀。</p></div>
        <div class="panel green" style="padding:20px;"><span class="tag green">chunk 对象级</span><p class="kicker">每个可召回片段独立携带等级、域、用途和生命周期；普通内容可以继续可用，高敏内容可以降级或隔离。</p></div>
      </div>
      <div class="flow" style="margin-top:30px;">
        <div class="flow-step"><strong>原文</strong><span>混合文件</span></div>
        <div class="arrow">→</div>
        <div class="flow-step"><strong>切块</strong><span>召回粒度</span></div>
        <div class="arrow">→</div>
        <div class="flow-step"><strong>对象</strong><span>可治理身份</span></div>
      </div>
    </div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
强调 chunk 是实现手段，核心是治理对象。没有对象化，就无法谈细粒度授权、降级输出、受控同步和审计证明。
</details>

<section class="slide" id="slide-07" data-page="07 / 19">
  <p class="eyebrow">创新点一证据</p>
  <h2>整文件治理过粗，chunk 对象化释放可用内容</h2>
  <div class="grid-3" style="margin-top:38px;">
    <div class="panel red"><div class="small-title">文件级高敏率</div><div class="big-number">100%</div><div class="metric-label">13 个真实文件全部被高敏标签覆盖</div></div>
    <div class="panel amber"><div class="small-title">chunk 级高敏率</div><div class="big-number">15.86%</div><div class="metric-label">145 个 chunk 中仅 23 个是 L2</div></div>
    <div class="panel green"><div class="small-title">元数据完整率</div><div class="big-number">100%</div><div class="metric-label">每个对象都有治理字段</div></div>
  </div>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>隐私等级分布</h3>
      <div class="columns" style="--cols:3; margin-top:28px;">
        <div class="column-wrap"><div class="column green" style="--h:100%;"></div><div class="column-number">64</div><div class="column-label">L0<br>低风险</div></div>
        <div class="column-wrap"><div class="column amber" style="--h:90.6%;"></div><div class="column-number">58</div><div class="column-label">L1<br>中低风险</div></div>
        <div class="column-wrap"><div class="column red" style="--h:35.9%;"></div><div class="column-number">23</div><div class="column-label">L2<br>高敏</div></div>
      </div>
    </div>
    <div class="panel">
      <h3>文件级标签带来的误杀</h3>
      <div class="bar-chart" style="margin-top:34px;">
        <div class="bar-row"><span class="bar-label">文件级高敏覆盖</span><div class="bar-track"><div class="bar-fill red" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
        <div class="bar-row"><span class="bar-label">chunk 真实高敏</span><div class="bar-track"><div class="bar-fill amber" style="--v:15.86%;"></div></div><span class="bar-value">0.1586</span></div>
        <div class="bar-row"><span class="bar-label">低风险过度保护</span><div class="bar-track"><div class="bar-fill red" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
        <div class="bar-row"><span class="bar-label">标识符降噪</span><div class="bar-track"><div class="bar-fill green" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
      </div>
      <p class="kicker" style="margin-top:28px;">结论：治理对象太粗会直接导致误杀和不可用；资产化的收益是把普通可用内容和高敏受控内容分离开。</p>
    </div>
  </div>
  <p class="footer-note">数据来源：objectization_eval_v1；real files = 13，real chunks = 145。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这里用 100% vs 15.86% 打出冲击力。文件级治理不是更安全，而是把大量普通内容一起冻结，导致智能体可用性下降。
</details>

<section class="slide" id="slide-08" data-page="08 / 19">
  <p class="eyebrow">创新点二：记忆防火墙</p>
  <h2>相关不等于可用：控制点必须前置到检索返回之前</h2>
  <div class="flow" style="margin-top:42px;">
    <div class="flow-step blue"><strong>query</strong><span>主体、场景域、用途、调用方</span></div>
    <div class="arrow">→</div>
    <div class="flow-step teal"><strong>candidate retrieval</strong><span>相关性召回，但不直接进入上下文</span></div>
    <div class="arrow">→</div>
    <div class="flow-step amber"><strong>policy decision</strong><span>domain、purpose、privacy、lifecycle</span></div>
    <div class="arrow">→</div>
    <div class="flow-step green"><strong>returned result</strong><span>allow / deny / downgrade / sandbox</span></div>
  </div>
  <div class="grid-2" style="margin-top:46px;">
    <div class="panel">
      <h3>一次记忆返回必须同时满足</h3>
      <div class="matrix cols-4" style="margin-top:22px;">
        <div class="cell header">检查项</div><div class="cell header">问题</div><div class="cell header">失败动作</div><div class="cell header">证据</div>
        <div class="cell">相关性</div><div class="cell">是否回答当前问题</div><div class="cell warn">降权</div><div class="cell">retrieval hit</div>
        <div class="cell">场景域</div><div class="cell">personal / work / third-party 是否匹配</div><div class="cell bad">deny</div><div class="cell">policy decision</div>
        <div class="cell">用途</div><div class="cell">当前 purpose 是否被允许</div><div class="cell bad">deny</div><div class="cell">purpose_allow</div>
        <div class="cell">隐私等级</div><div class="cell">原文是否可返回</div><div class="cell warn">downgrade</div><div class="cell">output_shape</div>
        <div class="cell">生命周期</div><div class="cell">是否撤销、过期、tombstone</div><div class="cell bad">deny</div><div class="cell">lifecycle log</div>
      </div>
    </div>
    <div class="panel teal">
      <h3>边界变化</h3>
      <div class="list">
        <div class="item"><span class="dot teal"></span><span>传统检索：先把最相关候选交给模型，再提示模型不要泄露。</span></div>
        <div class="item"><span class="dot amber"></span><span>召回后过滤：最终返回减少越权，但 raw candidate 已经越过边界。</span></div>
        <div class="item"><span class="dot green"></span><span>检索前治理：敏感原文在进入模型上下文前就被拒绝、降级或送入沙箱。</span></div>
      </div>
      <div class="quote" style="margin-top:30px;">记忆防火墙不是多加一个过滤器，而是改变安全边界：高敏原文不应该先跨过边界，再靠后处理补救。</div>
    </div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
核心表达是“相关不等于可用”。把 policy decision 放在返回前，是从检索质量问题升级到使用控制问题。
</details>

<section class="slide" id="slide-09" data-page="09 / 19">
  <p class="eyebrow">创新点二证据</p>
  <h2>检索前控制和召回后过滤不是等价方案</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>raw boundary 暴露率</h3>
      <p class="kicker">候选内容是否已经跨过治理边界。</p>
      <div class="bar-chart" style="margin-top:28px;">
        <div class="bar-row"><span class="bar-label">baseline_raw</span><div class="bar-track"><div class="bar-fill red" style="--v:87.5%;"></div></div><span class="bar-value">0.875</span></div>
        <div class="bar-row"><span class="bar-label">post_filter</span><div class="bar-track"><div class="bar-fill red" style="--v:87.5%;"></div></div><span class="bar-value">0.875</span></div>
        <div class="bar-row"><span class="bar-label">pre_guard</span><div class="bar-track"><div class="bar-fill green" style="--v:12.5%;"></div></div><span class="bar-value">0.125</span></div>
      </div>
      <h3 style="margin-top:40px;">高敏原文暴露率</h3>
      <div class="bar-chart" style="margin-top:24px;">
        <div class="bar-row"><span class="bar-label">baseline_raw</span><div class="bar-track"><div class="bar-fill red" style="--v:50%;"></div></div><span class="bar-value">0.50</span></div>
        <div class="bar-row"><span class="bar-label">post_filter</span><div class="bar-track"><div class="bar-fill red" style="--v:50%;"></div></div><span class="bar-value">0.50</span></div>
        <div class="bar-row"><span class="bar-label">pre_guard</span><div class="bar-track"><div class="bar-fill green" style="--v:0%;"></div></div><span class="bar-value">0.00</span></div>
      </div>
    </div>
    <div class="panel">
      <h3>任务成功与越权返回</h3>
      <div class="matrix cols-5" style="margin-top:24px;">
        <div class="cell header">模式</div><div class="cell header">任务成功</div><div class="cell header">raw boundary</div><div class="cell header">返回越权</div><div class="cell header">高敏原文</div>
        <div class="cell"><span class="tag red">baseline_raw</span></div><div class="cell good">1.000</div><div class="cell bad">0.875</div><div class="cell bad">0.750</div><div class="cell bad">0.500</div>
        <div class="cell"><span class="tag amber">post_filter</span></div><div class="cell warn">0.875</div><div class="cell bad">0.875</div><div class="cell warn">0.125</div><div class="cell bad">0.500</div>
        <div class="cell"><span class="tag green">pre_guard</span></div><div class="cell warn">0.875</div><div class="cell good">0.125</div><div class="cell warn">0.125</div><div class="cell good">0.000</div>
      </div>
      <div class="quote" style="margin-top:30px;">Post-filter 看起来最终少返回了一些越权内容，但 raw candidate 已经跨过边界；Pre-guard 的价值是让高敏内容在进入模型上下文前就被挡住或降级。</div>
      <p class="kicker" style="margin-top:24px;">开销也很小：pre_guard policy eval p50 = 0.007 ms。</p>
    </div>
  </div>
  <p class="footer-note">数据来源：pre_guard_vs_post_filter_v1。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
重点讲 raw boundary。即使 post_filter 最终少返回越权结果，也不能改变“高敏原文已经被召回进边界内”的事实。
</details>

<section class="slide" id="slide-10" data-page="10 / 19">
  <p class="eyebrow">攻击压力测试</p>
  <h2>策略前置、意图门控、allowlist 三层收益</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>攻击成功率</h3>
      <div class="bar-chart" style="margin-top:28px;">
        <div class="bar-row"><span class="bar-label">baseline_raw</span><div class="bar-track"><div class="bar-fill red" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
        <div class="bar-row"><span class="bar-label">pre_guard</span><div class="bar-track"><div class="bar-fill amber" style="--v:37.5%;"></div></div><span class="bar-value">0.375</span></div>
        <div class="bar-row"><span class="bar-label">+ intent</span><div class="bar-track"><div class="bar-fill green" style="--v:0%;"></div></div><span class="bar-value">0.00</span></div>
        <div class="bar-row"><span class="bar-label">+ allowlist</span><div class="bar-track"><div class="bar-fill green" style="--v:0%;"></div></div><span class="bar-value">0.00</span></div>
      </div>
      <h3 style="margin-top:42px;">良性成功率</h3>
      <div class="bar-chart" style="margin-top:24px;">
        <div class="bar-row"><span class="bar-label">baseline_raw</span><div class="bar-track"><div class="bar-fill red" style="--v:0%;"></div></div><span class="bar-value">0.00</span></div>
        <div class="bar-row"><span class="bar-label">pre_guard</span><div class="bar-track"><div class="bar-fill amber" style="--v:50%;"></div></div><span class="bar-value">0.50</span></div>
        <div class="bar-row"><span class="bar-label">+ intent</span><div class="bar-track"><div class="bar-fill amber" style="--v:50%;"></div></div><span class="bar-value">0.50</span></div>
        <div class="bar-row"><span class="bar-label">+ allowlist</span><div class="bar-track"><div class="bar-fill green" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
      </div>
    </div>
    <div class="panel">
      <h3>三层防护拆解</h3>
      <div class="flow" style="margin-top:24px;">
        <div class="flow-step teal"><strong>pre_guard</strong><span>先压住高敏原文暴露：0.70 → 0.00</span></div>
        <div class="arrow">→</div>
        <div class="flow-step amber"><strong>intent gate</strong><span>识别导出、越权、角色混淆等攻击意图</span></div>
        <div class="arrow">→</div>
        <div class="flow-step green"><strong>allowlist</strong><span>保留被授权共享偏好，恢复良性查询保真</span></div>
      </div>
      <div class="matrix cols-4" style="margin-top:34px;">
        <div class="cell header">模式</div><div class="cell header">攻击成功</div><div class="cell header">高敏原文暴露</div><div class="cell header">良性成功</div>
        <div class="cell">baseline_raw</div><div class="cell bad">1.000</div><div class="cell bad">0.700</div><div class="cell bad">0.000</div>
        <div class="cell">pre_guard</div><div class="cell warn">0.375</div><div class="cell good">0.000</div><div class="cell warn">0.500</div>
        <div class="cell">pre_guard_intent</div><div class="cell good">0.000</div><div class="cell good">0.000</div><div class="cell warn">0.500</div>
        <div class="cell">pre_guard_intent_allowlist</div><div class="cell good">0.000</div><div class="cell good">0.000</div><div class="cell good">1.000</div>
      </div>
    </div>
  </div>
  <p class="footer-note">数据来源：attack_eval_v1；10 条查询，其中 8 条恶意、2 条良性。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这页不要宣称“完美防御”。要说实验拆出了三层收益：策略前置控制原文暴露，意图门控控制跨域攻击，allowlist 恢复授权共享的可用性。
</details>

<section class="slide" id="slide-11" data-page="11 / 19">
  <p class="eyebrow">创新点三：可用不可见</p>
  <h2>高敏记忆不是“给或不给”的二选一</h2>
  <div class="wide-grid" style="margin-top:42px;">
    <div>
      <div class="quote">高敏记忆可以参与任务，但不必以原文形式被看见。</div>
      <div class="flow" style="margin-top:34px;">
        <div class="flow-step red"><strong>raw</strong><span>原文直接返回，效用高但风险高</span></div>
        <div class="arrow">→</div>
        <div class="flow-step amber"><strong>summary</strong><span>摘要不天然安全，需要策略约束</span></div>
        <div class="arrow">→</div>
        <div class="flow-step teal"><strong>redacted</strong><span>字段脱敏，保留部分任务价值</span></div>
      </div>
      <div class="flow" style="margin-top:18px;">
        <div class="flow-step green"><strong>derived_result</strong><span>只输出结论，不输出原文</span></div>
        <div class="arrow">→</div>
        <div class="flow-step violet"><strong>sandbox_job</strong><span>高敏计算留在受控环境内</span></div>
        <div class="arrow">→</div>
        <div class="flow-step"><strong>deny</strong><span>核心敏感或不合规场景直接拒绝</span></div>
      </div>
    </div>
    <div class="panel">
      <h3>按隐私等级控制输出形态</h3>
      <div class="matrix cols-6" style="margin-top:26px;">
        <div class="cell header">等级</div><div class="cell header">raw</div><div class="cell header">summary</div><div class="cell header">redacted</div><div class="cell header">derived</div><div class="cell header">sandbox</div>
        <div class="cell">L0 低风险</div><div class="cell good">允许</div><div class="cell good">允许</div><div class="cell good">允许</div><div class="cell good">允许</div><div class="cell info">可选</div>
        <div class="cell">L1 中低风险</div><div class="cell warn">受限</div><div class="cell good">优先</div><div class="cell good">允许</div><div class="cell good">允许</div><div class="cell info">可选</div>
        <div class="cell">L2 高敏</div><div class="cell bad">默认禁止</div><div class="cell warn">需脱敏</div><div class="cell good">允许</div><div class="cell good">优先</div><div class="cell good">优先</div>
        <div class="cell">L3 核心敏感</div><div class="cell bad">禁止</div><div class="cell bad">禁止</div><div class="cell warn">强约束</div><div class="cell warn">强约束</div><div class="cell good">强隔离</div>
      </div>
      <p class="kicker" style="margin-top:24px;">输出策略不是模型临场决定，而是由记忆对象的等级、用途、场景域和生命周期共同决定。</p>
    </div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这一页讲隐私保护从“访问控制”推进到“使用形态控制”。高敏数据不流动，但可以在受控环境中产生最小必要结果。
</details>

<section class="slide" id="slide-12" data-page="12 / 19">
  <p class="eyebrow">创新点三证据</p>
  <h2>控制输出形态，比简单拒绝更有价值</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>任务成功率与原文暴露率</h3>
      <div class="matrix cols-5" style="margin-top:24px;">
        <div class="cell header">模式</div><div class="cell header">任务成功</div><div class="cell header">效用分</div><div class="cell header">原文暴露</div><div class="cell header">最小必要</div>
        <div class="cell">raw</div><div class="cell good">1.000</div><div class="cell good">1.000</div><div class="cell bad">1.000</div><div class="cell bad">0.000</div>
        <div class="cell">deny</div><div class="cell bad">0.000</div><div class="cell bad">0.000</div><div class="cell good">0.000</div><div class="cell good">1.000</div>
        <div class="cell">redacted</div><div class="cell good">1.000</div><div class="cell warn">0.833</div><div class="cell good">0.000</div><div class="cell good">1.000</div>
        <div class="cell">summary</div><div class="cell good">1.000</div><div class="cell good">1.000</div><div class="cell good">0.000</div><div class="cell warn">0.500</div>
        <div class="cell">derived_result</div><div class="cell good">1.000</div><div class="cell warn">0.833</div><div class="cell good">0.000</div><div class="cell good">1.000</div>
        <div class="cell">sandbox_job</div><div class="cell good">1.000</div><div class="cell warn">0.833</div><div class="cell good">0.000</div><div class="cell good">1.000</div>
      </div>
    </div>
    <div class="panel">
      <h3>关键对照</h3>
      <div class="bar-chart" style="margin-top:28px;">
        <div class="bar-row"><span class="bar-label">raw 原文暴露</span><div class="bar-track"><div class="bar-fill red" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
        <div class="bar-row"><span class="bar-label">deny 任务成功</span><div class="bar-track"><div class="bar-fill red" style="--v:0%;"></div></div><span class="bar-value">0.00</span></div>
        <div class="bar-row"><span class="bar-label">derived 成功</span><div class="bar-track"><div class="bar-fill green" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
        <div class="bar-row"><span class="bar-label">derived 暴露</span><div class="bar-track"><div class="bar-fill green" style="--v:0%;"></div></div><span class="bar-value">0.00</span></div>
        <div class="bar-row"><span class="bar-label">sandbox 成功</span><div class="bar-track"><div class="bar-fill green" style="--v:100%;"></div></div><span class="bar-value">1.00</span></div>
        <div class="bar-row"><span class="bar-label">summary 敏感泄露</span><div class="bar-track"><div class="bar-fill amber" style="--v:50%;"></div></div><span class="bar-value">0.50</span></div>
      </div>
      <div class="quote" style="margin-top:32px;">Raw 是可用但不可接受，deny 是安全但不可用。Derived result 和 sandbox job 代表中间路线：不暴露原文，也不放弃任务。</div>
    </div>
  </div>
  <p class="footer-note">数据来源：output_shape_eval_v1；sandbox_job latency p50 = 2.524 ms。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
特别提醒 summary 不天然安全。它没有原文暴露，但如果保留敏感实体或类别，仍会有敏感泄露，必须纳入输出策略。
</details>

<section class="slide" id="slide-13" data-page="13 / 19">
  <p class="eyebrow">创新点四：受控流动</p>
  <h2>连续体验不等于 raw memory everywhere</h2>
  <div class="wide-grid" style="margin-top:40px;">
    <div>
      <div class="flow">
        <div class="flow-step red"><strong>raw_sync</strong><span>复制原文，体验直接，风险也直接扩散</span></div>
        <div class="arrow">→</div>
        <div class="flow-step amber"><strong>summary_sync</strong><span>降低原文风险，但撤销语义不足</span></div>
        <div class="arrow">→</div>
        <div class="flow-step green"><strong>policy_sync</strong><span>同步摘要、策略、tombstone，支持撤销传播</span></div>
        <div class="arrow">→</div>
        <div class="flow-step teal"><strong>dp_sync</strong><span>同步扰动统计或偏好信号，牺牲部分效用</span></div>
      </div>
      <div class="matrix cols-5" style="margin-top:36px;">
        <div class="cell header">模式</div><div class="cell header">初始任务成功</div><div class="cell header">重识别风险</div><div class="cell header">原始高敏条目</div><div class="cell header">撤销后 stale recall</div>
        <div class="cell">local_only</div><div class="cell bad">0.000</div><div class="cell good">0.000</div><div class="cell good">0</div><div class="cell good">0</div>
        <div class="cell">raw_sync</div><div class="cell good">1.000</div><div class="cell bad">0.950</div><div class="cell bad">1</div><div class="cell bad">1</div>
        <div class="cell">summary_sync</div><div class="cell good">1.000</div><div class="cell good">0.000</div><div class="cell good">0</div><div class="cell bad">1</div>
        <div class="cell">policy_sync</div><div class="cell good">1.000</div><div class="cell good">0.000</div><div class="cell good">0</div><div class="cell good">0</div>
        <div class="cell">dp_sync</div><div class="cell warn">0.667</div><div class="cell good">0.000</div><div class="cell good">0</div><div class="cell good">0</div>
      </div>
    </div>
    <div class="panel green">
      <h3>受控流动同步什么</h3>
      <div class="list">
        <div class="item"><span class="dot green"></span><span>summary：最小必要摘要，而不是完整原文。</span></div>
        <div class="item"><span class="dot green"></span><span>preference signal：偏好标签或派生状态。</span></div>
        <div class="item"><span class="dot green"></span><span>policy metadata：隐私等级、场景域、用途边界。</span></div>
        <div class="item"><span class="dot green"></span><span>tombstone：删除与撤销必须跨端传播。</span></div>
        <div class="item"><span class="dot green"></span><span>DP update：在需要统计同步时引入隐私预算。</span></div>
      </div>
      <div class="quote" style="margin-top:28px;">Summary sync 能降低原文风险，但如果不带策略元数据和 tombstone，撤销后仍会 stale recall。</div>
    </div>
  </div>
  <p class="footer-note">数据来源：local_dual_device_sync_v1；policy_sync payload = 1273 bytes，dp_sync epsilon = 2.0。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这一页的关键不是“同步摘要就够了”，而是“同步受控表示”。summary 解决原文风险，但 policy + tombstone 才能解决撤销和生命周期。
</details>

<section class="slide" id="slide-14" data-page="14 / 19">
  <p class="eyebrow">审计可证与当前边界</p>
  <h2>不是只说保护了隐私，而是能证明每次记忆使用符合策略</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>端到端故事 trace</h3>
      <div class="timeline" style="margin-top:24px;">
        <div class="timeline-step"><b>1</b><span>高敏私人日程产生</span></div>
        <div class="timeline-step"><b>2</b><span>分类为 personal high sensitivity memory</span></div>
        <div class="timeline-step"><b>3</b><span>工作域请求会议安排</span></div>
        <div class="timeline-step"><b>4</b><span>通过 sandbox/derived 输出可用时间窗</span></div>
        <div class="timeline-step"><b>5</b><span>第三方请求完整细节被拒绝</span></div>
        <div class="timeline-step"><b>6</b><span>撤销后跨端不再召回</span></div>
      </div>
      <div class="grid-3" style="margin-top:30px;">
        <div class="panel green" style="padding:18px;"><div class="small-title">policy pass</div><div class="big-number" style="font-size:44px;">1.0</div></div>
        <div class="panel green" style="padding:18px;"><div class="small-title">raw exposure</div><div class="big-number" style="font-size:44px;">0</div></div>
        <div class="panel green" style="padding:18px;"><div class="small-title">audit complete</div><div class="big-number" style="font-size:44px;">1.0</div></div>
      </div>
    </div>
    <div class="panel amber">
      <h3>当前边界要主动说明</h3>
      <div class="list">
        <div class="item"><span class="dot amber"></span><span>样本规模仍偏小：真实文件 13 个、真实 chunk 145 个、攻击查询 10 条。</span></div>
        <div class="item"><span class="dot amber"></span><span>沙箱是规则级原型，不是真实 TEE 或生产级隔离 runtime。</span></div>
        <div class="item"><span class="dot amber"></span><span>DP 同步是语义验证，不是完整隐私预算系统。</span></div>
        <div class="item"><span class="dot amber"></span><span>OpenClaw memory search hook 还需要更深接线。</span></div>
        <div class="item"><span class="dot amber"></span><span>真实双设备、真实第三方接入、人工效用评分仍需补齐。</span></div>
      </div>
      <p class="kicker" style="margin-top:26px;">稳妥表述：这是一套面向长期记忆治理的可验证原型，证明关键机制方向有效，但还不是生产级完整系统。</p>
    </div>
  </div>
  <p class="footer-note">数据来源：story_trace_v1。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这页要主动处理可信度问题。先展示审计闭环，再说明边界，可以避免听众把原型结果误解为生产承诺。
</details>

<section class="slide" id="slide-15" data-page="15 / 19">
  <p class="eyebrow">总结与下一步</p>
  <h2>长期记忆的下一步，是从能力走向治理</h2>
  <div class="grid-2" style="margin-top:42px;">
    <div class="panel blue">
      <h3>一句话收束</h3>
      <div class="quote" style="margin-top:24px;">先把记忆对象化，再把使用控制前置到检索链路中，随后通过降级输出和受控分析解决高敏记忆可用性问题，最后用受控同步支持跨设备连续体验。</div>
      <p class="kicker" style="margin-top:28px;">目标不是让智能体什么都记住，而是让每条记忆都知道自己是谁、能在哪里用、能以什么形态用、能流向哪里、什么时候必须失效，并且这一切都能被证明。</p>
    </div>
    <div class="panel">
      <h3>下一步工程与实验</h3>
      <div class="list">
        <div class="item"><span class="dot blue"></span><span>扩大 gold set 和攻击集，覆盖更多真实记忆、跨域查询和 prompt injection 场景。</span></div>
        <div class="item"><span class="dot teal"></span><span>接真实 OpenClaw memory search hook，减少 wrapper 和模拟层。</span></div>
        <div class="item"><span class="dot violet"></span><span>补真实 sandbox runtime，对比规则级、容器级和 TEE 级边界。</span></div>
        <div class="item"><span class="dot green"></span><span>做真实双设备或 Docker 双环境同步，验证撤销传播和隔离边界。</span></div>
        <div class="item"><span class="dot amber"></span><span>加入人工效用评分，评估降级输出和派生结果的真实可用性。</span></div>
      </div>
    </div>
  </div>
  <div class="flow" style="margin-top:42px;">
    <div class="flow-step blue"><strong>资产化</strong><span>每条记忆有治理身份</span></div>
    <div class="arrow">→</div>
    <div class="flow-step teal"><strong>防火墙</strong><span>召回前就做策略判断</span></div>
    <div class="arrow">→</div>
    <div class="flow-step amber"><strong>可用不可见</strong><span>控制输出形态</span></div>
    <div class="arrow">→</div>
    <div class="flow-step green"><strong>受控流动</strong><span>同步策略和生命周期</span></div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
结尾不要再展开实验细节，回到路线图。最终记忆治理能力应当像数据资产治理一样，有身份、边界、生命周期和证据。
</details>

<section class="slide" id="slide-a" data-page="A / 19">
  <p class="eyebrow">备份页 A：完整数据覆盖</p>
  <h2>当前实验覆盖与证据链</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>数据覆盖</h3>
      <div class="grid-3" style="margin-top:26px;">
        <div class="panel blue" style="padding:18px;"><div class="small-title">real files</div><div class="big-number" style="font-size:48px;">13</div></div>
        <div class="panel teal" style="padding:18px;"><div class="small-title">real chunks</div><div class="big-number" style="font-size:48px;">145</div></div>
        <div class="panel amber" style="padding:18px;"><div class="small-title">chunk queries</div><div class="big-number" style="font-size:48px;">8</div></div>
        <div class="panel red" style="padding:18px;"><div class="small-title">attack queries</div><div class="big-number" style="font-size:48px;">10</div></div>
        <div class="panel violet" style="padding:18px;"><div class="small-title">sandbox queries</div><div class="big-number" style="font-size:48px;">6</div></div>
        <div class="panel green" style="padding:18px;"><div class="small-title">sync queries</div><div class="big-number" style="font-size:48px;">3</div></div>
      </div>
    </div>
    <div class="panel">
      <h3>创新点证据表</h3>
      <table class="table" style="margin-top:22px;">
        <tr><th>创新点</th><th>Before</th><th>After</th><th>关键指标</th></tr>
        <tr><td>记忆资产化</td><td>file high = 1.0</td><td>chunk high = 0.1586</td><td>overprotected = 1.0</td></tr>
        <tr><td>记忆防火墙</td><td>post raw boundary = 0.875</td><td>pre raw boundary = 0.125</td><td>sensitive raw = 0.0</td></tr>
        <tr><td>可用不可见</td><td>raw exposure = 1.0</td><td>derived/sandbox = 0.0</td><td>utility = 0.8333</td></tr>
        <tr><td>受控流动</td><td>summary stale = 1</td><td>policy stale = 0</td><td>policy gain = 1.0</td></tr>
      </table>
    </div>
  </div>
  <p class="footer-note">数据来源：report_pack_v1/summary.md。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
如果被问“实验覆盖多少”，用这页说明当前覆盖面和每个创新点对应的证据，不要把它当主线页讲太久。
</details>

<section class="slide" id="slide-b" data-page="B / 19">
  <p class="eyebrow">备份页 B：chunk 隐私等级分布</p>
  <h2>真实记忆切块后，高敏内容只占一部分</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>145 个 chunk 的等级分布</h3>
      <div class="columns" style="--cols:3; height:360px; margin-top:34px;">
        <div class="column-wrap"><div class="column green" style="--h:100%;"></div><div class="column-number">64</div><div class="column-label">L0<br>44.14%</div></div>
        <div class="column-wrap"><div class="column amber" style="--h:90.6%;"></div><div class="column-number">58</div><div class="column-label">L1<br>40.00%</div></div>
        <div class="column-wrap"><div class="column red" style="--h:35.9%;"></div><div class="column-number">23</div><div class="column-label">L2<br>15.86%</div></div>
      </div>
    </div>
    <div class="panel">
      <h3>为什么这对治理重要</h3>
      <div class="list">
        <div class="item"><span class="dot green"></span><span>L0/L1 占 84.14%，如果因为文件级高敏标签被整体拦截，会损失大量普通上下文。</span></div>
        <div class="item"><span class="dot red"></span><span>L2 虽然只占 15.86%，但必须带更严格的 output shape、同步和审计策略。</span></div>
        <div class="item"><span class="dot blue"></span><span>chunk 不是为了切得更碎，而是为了让“可召回单位”和“治理单位”对齐。</span></div>
      </div>
      <div class="bar-chart" style="margin-top:36px;">
        <div class="bar-row"><span class="bar-label">低/中低风险可用内容</span><div class="bar-track"><div class="bar-fill green" style="--v:84.14%;"></div></div><span class="bar-value">84.14%</span></div>
        <div class="bar-row"><span class="bar-label">高敏受控内容</span><div class="bar-track"><div class="bar-fill red" style="--v:15.86%;"></div></div><span class="bar-value">15.86%</span></div>
      </div>
    </div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这页用于回答“为什么不直接按文件做治理”。核心是可用性：绝大多数 chunk 不是高敏，但文件级策略会把它们一起误杀。
</details>

<section class="slide" id="slide-c" data-page="C / 19">
  <p class="eyebrow">备份页 C：工程开销</p>
  <h2>治理控制点的原型开销处于可接受范围</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>检索与策略开销</h3>
      <div class="bar-chart" style="margin-top:28px;">
        <div class="bar-row"><span class="bar-label">baseline retrieval p50</span><div class="bar-track"><div class="bar-fill blue" style="--v:85%;"></div></div><span class="bar-value">2.224 ms</span></div>
        <div class="bar-row"><span class="bar-label">guarded retrieval p50</span><div class="bar-track"><div class="bar-fill teal" style="--v:92%;"></div></div><span class="bar-value">2.409 ms</span></div>
        <div class="bar-row"><span class="bar-label">policy eval p50</span><div class="bar-track"><div class="bar-fill green" style="--v:1%;"></div></div><span class="bar-value">0.011 ms</span></div>
        <div class="bar-row"><span class="bar-label">sandbox overhead p50</span><div class="bar-track"><div class="bar-fill amber" style="--v:96%;"></div></div><span class="bar-value">2.518 ms</span></div>
      </div>
      <p class="kicker" style="margin-top:28px;">解释口径：当前原型里，策略判断本身非常轻；沙箱开销更明显，但仍是毫秒级规则原型结果。</p>
    </div>
    <div class="panel">
      <h3>同步 payload</h3>
      <div class="bar-chart" style="margin-top:28px;">
        <div class="bar-row"><span class="bar-label">raw sync</span><div class="bar-track"><div class="bar-fill red" style="--v:100%;"></div></div><span class="bar-value">1438 B</span></div>
        <div class="bar-row"><span class="bar-label">summary sync</span><div class="bar-track"><div class="bar-fill amber" style="--v:89.1%;"></div></div><span class="bar-value">1281 B</span></div>
        <div class="bar-row"><span class="bar-label">policy sync</span><div class="bar-track"><div class="bar-fill green" style="--v:88.5%;"></div></div><span class="bar-value">1273 B</span></div>
        <div class="bar-row"><span class="bar-label">dp sync</span><div class="bar-track"><div class="bar-fill teal" style="--v:91.0%;"></div></div><span class="bar-value">1308 B</span></div>
      </div>
      <div class="grid-2" style="margin-top:36px;">
        <div class="panel green" style="padding:18px;"><div class="small-title">dp epsilon</div><div class="big-number" style="font-size:46px;">2.0</div></div>
        <div class="panel blue" style="padding:18px;"><div class="small-title">policy tombstone</div><div class="big-number" style="font-size:46px;">1</div></div>
      </div>
    </div>
  </div>
  <p class="footer-note">数据来源：report_pack_v1、real_chunk_guarded_v2、local_dual_device_sync_v1。</p>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这页适合工程追问。强调这些数字来自原型，不代表生产极限；但它说明策略前置本身不是主要性能瓶颈。
</details>

<section class="slide" id="slide-d" data-page="D / 19">
  <p class="eyebrow">备份页 D：可复现实验入口</p>
  <h2>实验、报告和复现路径</h2>
  <div class="grid-2" style="margin-top:38px;">
    <div class="panel">
      <h3>推荐命令</h3>
      <div class="stack" style="margin-top:24px;">
        <div class="panel blue" style="padding:20px;"><span class="tag blue">make story-evals</span><p class="kicker">运行故事导向评估：对象化、防火墙、输出形态、双端同步、审计 trace。</p></div>
        <div class="panel red" style="padding:20px;"><span class="tag red">make attack-eval</span><p class="kicker">运行攻击压力测试：prompt injection、metadata exfiltration、role confusion、third-party export。</p></div>
        <div class="panel green" style="padding:20px;"><span class="tag green">make local-dual-sync-eval</span><p class="kicker">运行本地双设备同步评估：raw、summary、policy、DP 四种路径。</p></div>
        <div class="panel amber" style="padding:20px;"><span class="tag amber">make report-pack</span><p class="kicker">汇总生成分享可用的结果表和指标摘要。</p></div>
      </div>
    </div>
    <div class="panel">
      <h3>关键输出</h3>
      <table class="table" style="margin-top:22px;">
        <tr><th>文件</th><th>用途</th></tr>
        <tr><td>experiments/runs/report_pack_v1/summary.md</td><td>汇报数据包与证据表</td></tr>
        <tr><td>experiments/reports/innovation-support-experiments.md</td><td>创新点支撑实验说明</td></tr>
        <tr><td>experiments/runs/attack_eval_v1/metrics.json</td><td>攻击压力测试结果</td></tr>
        <tr><td>experiments/runs/local_dual_device_sync_v1/metrics.json</td><td>双端同步对照指标</td></tr>
        <tr><td>experiments/runs/story_trace_v1/metrics.json</td><td>端到端审计 trace 指标</td></tr>
      </table>
      <div class="quote" style="margin-top:34px;">复现策略：先跑 <code>make story-evals</code> 得到核心证据，再跑 <code>make report-pack</code> 生成分享表格。</div>
    </div>
  </div>
</section>

<details class="speaker-notes">
<summary>主讲备注</summary>
这页适合最后 Q&A 或会后给同事复现。主讲时不必展开命令细节。
</details>

</div>
