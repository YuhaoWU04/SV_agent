"""Generate the interactive SV Investigator field-lineage canvas.

The editable source of truth is architecture/data_lineage.json.  This script has
no third-party dependencies so updating the diagram stays cheap and reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_DIR / "architecture" / "data_lineage.json"
HTML_PATH = PROJECT_DIR / "docs" / "system_flow.html"
DICTIONARY_PATH = PROJECT_DIR / "docs" / "field_dictionary.md"
SOURCE_PATHS = [
    PROJECT_DIR / "agent.py",
    PROJECT_DIR / "prompts.py",
    PROJECT_DIR / "tools.py",
    PROJECT_DIR / "schemas.py",
    PROJECT_DIR / "config.py",
    PROJECT_DIR / "scripts" / "generate_flow_diagram.py",
]


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    stages = data.get("stages", [])
    fields = data.get("fields", [])
    transforms = data.get("transformations", [])

    def unique_ids(items: list[dict[str, Any]], label: str) -> set[str]:
        ids = [str(item.get("id", "")) for item in items]
        missing = [index for index, value in enumerate(ids) if not value]
        duplicates = sorted({value for value in ids if value and ids.count(value) > 1})
        if missing:
            errors.append(f"{label} entries missing id at indexes {missing}")
        if duplicates:
            errors.append(f"duplicate {label} ids: {duplicates}")
        return set(ids)

    stage_ids = unique_ids(stages, "stage")
    field_ids = unique_ids(fields, "field")
    transform_ids = unique_ids(transforms, "transformation")
    if field_ids & transform_ids:
        errors.append(f"field/transformation id collision: {sorted(field_ids & transform_ids)}")

    orders = [stage.get("order") for stage in stages]
    if orders != list(range(len(stages))):
        errors.append("stage order must be contiguous and already sorted from zero")

    for field in fields:
        if field.get("stage") not in stage_ids:
            errors.append(f"field {field.get('id')} uses unknown stage {field.get('stage')}")
        for required in ("path", "type", "meaning", "missing"):
            if not field.get(required):
                errors.append(f"field {field.get('id')} missing {required}")

    produced: set[str] = set()
    consumed: set[str] = set()
    for transform in transforms:
        if transform.get("stage") not in stage_ids:
            errors.append(
                f"transformation {transform.get('id')} uses unknown stage "
                f"{transform.get('stage')}"
            )
        for direction in ("inputs", "outputs"):
            values = transform.get(direction, [])
            if not isinstance(values, list) or not values:
                errors.append(f"transformation {transform.get('id')} has no {direction}")
                continue
            for field_id in values:
                if field_id not in field_ids:
                    errors.append(
                        f"transformation {transform.get('id')} references unknown "
                        f"{direction[:-1]} field {field_id}"
                    )
            if direction == "inputs":
                consumed.update(values)
            else:
                produced.update(values)

    non_input_fields = {
        field["id"] for field in fields if field.get("stage") != "input"
    }
    unproduced = sorted(non_input_fields - produced)
    if unproduced:
        errors.append(f"non-input fields without a producing transformation: {unproduced}")

    # Confirm the sequential state keys documented in the manifest still exist in agent.py.
    agent_source = (PROJECT_DIR / "agent.py").read_text(encoding="utf-8")
    for stage in stages:
        state_key = stage.get("state_key")
        if stage["id"] == "input":
            continue
        if f'output_key="{state_key}"' not in agent_source:
            errors.append(
                f"stage {stage['id']} state_key {state_key!r} not found in agent.py"
            )

    if not consumed:
        errors.append("manifest contains no field consumption edges")
    return errors


def source_fingerprint() -> str:
    digest = hashlib.sha256()
    digest.update(MANIFEST_PATH.read_bytes())
    for path in SOURCE_PATHS:
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def render_dictionary(data: dict[str, Any], fingerprint: str) -> str:
    stages = {stage["id"]: stage for stage in data["stages"]}
    lines = [
        "# SV Investigator 字段词典",
        "",
        f"> 自动生成自 `architecture/data_lineage.json`；源指纹 `{fingerprint[:12]}`。",
        "> 请勿直接编辑本文件。",
        "",
    ]
    for stage in data["stages"]:
        lines.extend([f"## {stage['order']}. {stage['title']}", "", stage["behavior"], ""])
        lines.extend([
            "| 字段路径 | 类型 | 含义 | 缺失或失败时 |",
            "|---|---|---|---|",
        ])
        for field in [item for item in data["fields"] if item["stage"] == stage["id"]]:
            values = [field["path"], field["type"], field["meaning"], field["missing"]]
            escaped = [str(value).replace("|", "\\|").replace("\n", " ") for value in values]
            lines.append("| " + " | ".join(escaped) + " |")
        lines.append("")
        lines.append("处理规则：")
        lines.append("")
        for transform in [
            item for item in data["transformations"] if item["stage"] == stage["id"]
        ]:
            kind = transform["kind"]
            lines.append(f"- **{transform['title']}**（{kind}）：{transform['operation']}")
            for branch in transform.get("branches", []):
                lines.append(f"  - 分支/约束：{branch}")
        if not any(item["stage"] == stage["id"] for item in data["transformations"]):
            lines.append("- 此阶段只提供外部输入字段。")
        lines.extend(["", f"实现位置：`{stages[stage['id']]['source']}`", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_html(data: dict[str, Any], fingerprint: str) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    title = html.escape(data["metadata"]["title"])
    template = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root {
  color-scheme: light dark;
  --bg: light-dark(#f4f6f8, #0e1116);
  --panel: light-dark(#ffffff, #171c24);
  --panel-2: light-dark(#f8fafc, #202733);
  --text: light-dark(#17202a, #edf2f7);
  --muted: light-dark(#617080, #a8b3c2);
  --border: light-dark(#cfd7e1, #3b4655);
  --primary: light-dark(#235ea7, #79b8ff);
  --field: light-dark(#e9f2ff, #18314e);
  --det: light-dark(#e7f6ed, #173d2a);
  --model: light-dark(#fff3d6, #4a3512);
  --external: light-dark(#f1eafe, #342555);
  --schema: light-dark(#feecee, #4b2028);
  --danger: light-dark(#b42318, #ff8a80);
  --shadow: light-dark(rgba(20, 35, 55, .14), rgba(0, 0, 0, .35));
}
* { box-sizing: border-box; }
html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: var(--bg); color: var(--text); font-family: Inter, "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif; }
button, input { font: inherit; }
.app { height: 100%; display: grid; grid-template-rows: auto 1fr; }
.toolbar { z-index: 30; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; padding: 12px 16px; background: var(--panel); border-bottom: 1px solid var(--border); box-shadow: 0 2px 12px var(--shadow); }
.title-block { min-width: 270px; margin-right: auto; }
.title-block h1 { font-size: 17px; font-weight: 600; margin: 0 0 2px; }
.title-block p { margin: 0; color: var(--muted); font-size: 12px; }
.control { border: 1px solid var(--border); color: var(--text); background: var(--panel-2); border-radius: 7px; min-height: 36px; padding: 7px 10px; }
button.control { cursor: pointer; }
button.control:hover { border-color: var(--primary); }
.search { width: min(320px, 42vw); }
.toggle { display: inline-flex; align-items: center; gap: 7px; color: var(--muted); font-size: 13px; }
.workspace { position: relative; overflow: hidden; touch-action: none; cursor: grab; }
.workspace.dragging { cursor: grabbing; }
.world { position: absolute; left: 0; top: 0; transform-origin: 0 0; padding: 92px 70px 120px; display: flex; gap: 105px; align-items: flex-start; }
.edges { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; pointer-events: none; z-index: 1; }
.stage { position: relative; z-index: 3; width: 410px; flex: 0 0 410px; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 8px 24px var(--shadow); overflow: hidden; }
.stage-header { padding: 15px 17px; border-bottom: 1px solid var(--border); background: var(--panel-2); }
.stage-index { color: var(--primary); font-size: 12px; font-weight: 700; letter-spacing: .08em; }
.stage h2 { margin: 3px 0 2px; font-size: 19px; font-weight: 600; }
.stage-subtitle { color: var(--muted); font-size: 12px; }
.stage-summary { padding: 12px 17px; color: var(--muted); font-size: 13px; border-bottom: 1px solid var(--border); }
.section { padding: 11px 12px 14px; }
.section + .section { border-top: 1px solid var(--border); }
.section h3 { margin: 0 4px 8px; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.node { width: 100%; text-align: left; border: 1px solid transparent; border-radius: 8px; color: var(--text); padding: 9px 10px; margin: 6px 0; cursor: pointer; transition: opacity .14s, border-color .14s, transform .14s; }
.node:hover, .node:focus-visible { border-color: var(--primary); outline: none; transform: translateY(-1px); }
.field-node { background: var(--field); }
.transform-node { background: var(--det); }
.transform-node[data-kind="model-controlled"], .transform-node[data-kind="model-structured"] { background: var(--model); }
.transform-node[data-kind="external-query"] { background: var(--external); }
.transform-node[data-kind="schema-validation"] { background: var(--schema); }
.node-path { display: block; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }
.node-meta { display: block; margin-top: 4px; color: var(--muted); font-size: 11px; }
.node.dim { opacity: .16; }
.node.related { border-color: var(--primary); }
.node.selected { border-color: var(--primary); box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary) 30%, transparent); }
.stage-limit { margin: 0; padding: 11px 16px 14px; color: var(--muted); font-size: 12px; border-top: 1px dashed var(--border); }
.edge { fill: none; stroke: var(--border); stroke-width: 1.4; opacity: .20; }
.edge.active { stroke: var(--primary); stroke-width: 2.2; opacity: .82; }
.edge.stage-edge { opacity: .42; stroke-width: 2; }
.edge.external.active { stroke: light-dark(#6b45b5, #b39cff); }
.edge.model.active { stroke: light-dark(#a56500, #ffc766); }
.detail { position: absolute; z-index: 25; top: 14px; right: 14px; width: min(390px, calc(100% - 28px)); max-height: calc(100% - 28px); overflow: auto; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; box-shadow: 0 12px 32px var(--shadow); padding: 16px; }
.detail[hidden] { display: none; }
.detail h2 { margin: 0 34px 4px 0; font-size: 17px; }
.detail .path { color: var(--primary); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }
.detail dl { margin: 14px 0 0; }
.detail dt { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .07em; margin-top: 12px; }
.detail dd { margin: 4px 0 0; font-size: 13px; line-height: 1.55; }
.detail ul { margin: 5px 0 0; padding-left: 18px; }
.close { position: absolute; right: 10px; top: 10px; border: 0; background: transparent; color: var(--muted); cursor: pointer; font-size: 20px; }
.legend { position: absolute; z-index: 20; left: 14px; bottom: 14px; display: flex; flex-wrap: wrap; gap: 8px 14px; max-width: calc(100% - 28px); padding: 9px 12px; background: color-mix(in srgb, var(--panel) 92%, transparent); border: 1px solid var(--border); border-radius: 8px; font-size: 11px; color: var(--muted); }
.key { display: inline-flex; align-items: center; gap: 5px; }
.swatch { width: 12px; height: 12px; border-radius: 3px; border: 1px solid var(--border); }
.swatch.field { background: var(--field); }.swatch.det { background: var(--det); }.swatch.model { background: var(--model); }.swatch.external { background: var(--external); }.swatch.schema { background: var(--schema); }
.empty { color: var(--muted); padding: 8px; font-size: 12px; }
@media (max-width: 720px) {
  .title-block { width: 100%; }
  .search { width: 100%; }
  .stage { width: 350px; flex-basis: 350px; }
  .world { gap: 75px; padding-left: 35px; }
  .legend { display: none; }
}
</style>
</head>
<body>
<main class="app">
  <header class="toolbar">
    <div class="title-block">
      <h1>__TITLE__</h1>
      <p>点击字段或处理节点，追踪完整上下游；拖动画布，滚轮缩放。</p>
    </div>
    <input id="search" class="control search" type="search" aria-label="搜索字段或处理" placeholder="搜索字段、含义、数据库或规则">
    <button id="zoomOut" class="control" type="button" aria-label="缩小">−</button>
    <button id="zoomIn" class="control" type="button" aria-label="放大">＋</button>
    <button id="fit" class="control" type="button">适合窗口</button>
    <button id="reset" class="control" type="button">清除选择</button>
    <label class="toggle"><input id="showAll" type="checkbox">显示全部字段连线</label>
  </header>
  <section id="workspace" class="workspace" aria-label="SV Investigator 字段级流程图">
    <div id="world" class="world">
      <svg id="edges" class="edges" aria-hidden="true"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"></path></marker></defs></svg>
    </div>
    <aside id="detail" class="detail" aria-live="polite" hidden><button id="closeDetail" class="close" type="button" aria-label="关闭详情">×</button><div id="detailBody"></div></aside>
    <div class="legend" aria-label="图例">
      <span class="key"><span class="swatch field"></span>字段</span>
      <span class="key"><span class="swatch det"></span>固定规则</span>
      <span class="key"><span class="swatch model"></span>模型整理</span>
      <span class="key"><span class="swatch external"></span>外部查询</span>
      <span class="key"><span class="swatch schema"></span>Schema 验证</span>
      <span class="key">源指纹 __FINGERPRINT__</span>
    </div>
  </section>
</main>
<script id="lineage-data" type="application/json">__DATA__</script>
<script>
(() => {
  const data = JSON.parse(document.getElementById('lineage-data').textContent);
  const workspace = document.getElementById('workspace');
  const world = document.getElementById('world');
  const svg = document.getElementById('edges');
  const detail = document.getElementById('detail');
  const detailBody = document.getElementById('detailBody');
  const search = document.getElementById('search');
  const showAll = document.getElementById('showAll');
  const nodes = new Map();
  const fields = new Map(data.fields.map(x => [x.id, {...x, nodeType: 'field'}]));
  const transforms = new Map(data.transformations.map(x => [x.id, {...x, nodeType: 'transform'}]));
  const stages = [...data.stages].sort((a, b) => a.order - b.order);
  const stageMap = new Map(stages.map(x => [x.id, x]));
  const edges = [];
  let selected = null;
  let scale = 0.72;
  let panX = 24;
  let panY = 30;
  let dragging = false;
  let dragStart = null;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const nodeButton = (item, type) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `node ${type}-node`;
    button.dataset.id = item.id;
    if (type === 'transform') button.dataset.kind = item.kind;
    const main = type === 'field' ? item.path : item.title;
    const meta = type === 'field' ? item.type : item.kind;
    button.innerHTML = `<span class="node-path">${esc(main)}</span><span class="node-meta">${esc(meta)}</span>`;
    button.addEventListener('click', event => {
      event.stopPropagation();
      selectNode(item.id);
    });
    nodes.set(item.id, button);
    return button;
  };

  for (const stage of stages) {
    const card = document.createElement('article');
    card.className = 'stage';
    card.dataset.stage = stage.id;
    card.innerHTML = `<header class="stage-header"><div class="stage-index">阶段 ${stage.order}</div><h2>${esc(stage.title)}</h2><div class="stage-subtitle">${esc(stage.subtitle)}</div></header><div class="stage-summary">${esc(stage.behavior)}</div>`;
    const fieldSection = document.createElement('section');
    fieldSection.className = 'section';
    fieldSection.innerHTML = '<h3>字段</h3>';
    const stageFields = data.fields.filter(item => item.stage === stage.id);
    if (!stageFields.length) fieldSection.insertAdjacentHTML('beforeend', '<div class="empty">无字段节点</div>');
    stageFields.forEach(item => fieldSection.appendChild(nodeButton(item, 'field')));
    card.appendChild(fieldSection);
    const transformSection = document.createElement('section');
    transformSection.className = 'section';
    transformSection.innerHTML = '<h3>处理与查询</h3>';
    const stageTransforms = data.transformations.filter(item => item.stage === stage.id);
    if (!stageTransforms.length) transformSection.insertAdjacentHTML('beforeend', '<div class="empty">外部输入，不执行处理</div>');
    stageTransforms.forEach(item => transformSection.appendChild(nodeButton(item, 'transform')));
    card.appendChild(transformSection);
    card.insertAdjacentHTML('beforeend', `<p class="stage-limit"><strong>边界：</strong>${esc(stage.limitations)}<br><strong>状态键：</strong>${esc(stage.state_key)}</p>`);
    world.appendChild(card);
  }

  for (const transform of data.transformations) {
    transform.inputs.forEach(fieldId => edges.push({from: fieldId, to: transform.id, type: transform.kind}));
    transform.outputs.forEach(fieldId => edges.push({from: transform.id, to: fieldId, type: transform.kind}));
  }

  function applyTransform() {
    world.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
  }

  function resizeWorld() {
    const cards = [...world.querySelectorAll('.stage')];
    const width = 140 + cards.reduce((sum, card) => sum + card.offsetWidth, 0) + Math.max(0, cards.length - 1) * 105;
    const height = 220 + Math.max(...cards.map(card => card.offsetHeight), 600);
    world.style.width = `${width}px`;
    world.style.height = `${height}px`;
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    drawEdges();
  }

  function centerOf(element) {
    const er = element.getBoundingClientRect();
    const wr = world.getBoundingClientRect();
    return {x: (er.left - wr.left + er.width / 2) / scale, y: (er.top - wr.top + er.height / 2) / scale};
  }

  function createPath(from, to, active, edgeType, stageEdge = false) {
    const dx = Math.max(36, Math.abs(to.x - from.x) * .42);
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M ${from.x} ${from.y} C ${from.x + dx} ${from.y}, ${to.x - dx} ${to.y}, ${to.x} ${to.y}`);
    path.setAttribute('marker-end', 'url(#arrow)');
    path.setAttribute('class', `edge${active ? ' active' : ''}${stageEdge ? ' stage-edge' : ''}${edgeType?.startsWith('model') ? ' model' : ''}${edgeType === 'external-query' ? ' external' : ''}`);
    svg.appendChild(path);
  }

  function relatedSet(rootId) {
    if (!rootId) return new Set();
    const forward = new Map();
    const backward = new Map();
    for (const edge of edges) {
      if (!forward.has(edge.from)) forward.set(edge.from, []);
      if (!backward.has(edge.to)) backward.set(edge.to, []);
      forward.get(edge.from).push(edge.to);
      backward.get(edge.to).push(edge.from);
    }
    const seen = new Set([rootId]);
    const walk = (map, start) => {
      const queue = [start];
      while (queue.length) {
        const current = queue.shift();
        for (const next of map.get(current) || []) {
          if (!seen.has(next)) { seen.add(next); queue.push(next); }
        }
      }
    };
    walk(forward, rootId);
    walk(backward, rootId);
    return seen;
  }

  function drawEdges() {
    [...svg.querySelectorAll('path.edge')].forEach(path => path.remove());
    const related = relatedSet(selected);
    const cards = [...world.querySelectorAll('.stage')];
    for (let i = 0; i < cards.length - 1; i++) {
      const a = centerOf(cards[i].querySelector('.stage-header'));
      const b = centerOf(cards[i + 1].querySelector('.stage-header'));
      createPath({x: a.x + cards[i].offsetWidth / 2, y: a.y}, {x: b.x - cards[i + 1].offsetWidth / 2, y: b.y}, false, '', true);
    }
    for (const edge of edges) {
      const fromEl = nodes.get(edge.from);
      const toEl = nodes.get(edge.to);
      if (!fromEl || !toEl) continue;
      const active = selected && related.has(edge.from) && related.has(edge.to);
      if (!showAll.checked && !active) continue;
      createPath(centerOf(fromEl), centerOf(toEl), active, edge.type);
    }
  }

  function connections(id, direction) {
    const ids = edges.filter(edge => direction === 'up' ? edge.to === id : edge.from === id).map(edge => direction === 'up' ? edge.from : edge.to);
    return ids.map(value => fields.get(value)?.path || transforms.get(value)?.title || value);
  }

  function showDetail(item) {
    const stage = stageMap.get(item.stage);
    if (item.nodeType === 'field') {
      detailBody.innerHTML = `<h2>字段</h2><div class="path">${esc(item.path)}</div><dl><dt>阶段</dt><dd>${esc(stage.title)}</dd><dt>类型</dt><dd>${esc(item.type)}</dd><dt>含义</dt><dd>${esc(item.meaning)}</dd><dt>缺失或失败时</dt><dd>${esc(item.missing)}</dd><dt>直接上游</dt><dd>${list(connections(item.id, 'up'))}</dd><dt>直接下游</dt><dd>${list(connections(item.id, 'down'))}</dd></dl>`;
    } else {
      detailBody.innerHTML = `<h2>${esc(item.title)}</h2><div class="path">${esc(item.kind)}</div><dl><dt>阶段</dt><dd>${esc(stage.title)}</dd><dt>处理</dt><dd>${esc(item.operation)}</dd><dt>输入字段</dt><dd>${list(item.inputs.map(id => fields.get(id)?.path || id))}</dd><dt>输出字段</dt><dd>${list(item.outputs.map(id => fields.get(id)?.path || id))}</dd><dt>分支与约束</dt><dd>${list(item.branches || [])}</dd><dt>实现位置</dt><dd><code>${esc(item.source)}</code></dd></dl>`;
    }
    detail.hidden = false;
  }

  function list(values) {
    if (!values.length) return '<span class="node-meta">无</span>';
    return `<ul>${values.map(value => `<li>${esc(value)}</li>`).join('')}</ul>`;
  }

  function selectNode(id) {
    selected = id;
    const related = relatedSet(id);
    for (const [nodeId, element] of nodes) {
      element.classList.toggle('selected', nodeId === id);
      element.classList.toggle('related', nodeId !== id && related.has(nodeId));
      element.classList.toggle('dim', !related.has(nodeId));
    }
    const item = fields.get(id) || transforms.get(id);
    if (item) showDetail(item);
    drawEdges();
  }

  function clearSelection() {
    selected = null;
    for (const element of nodes.values()) element.classList.remove('selected', 'related', 'dim');
    detail.hidden = true;
    drawEdges();
  }

  function fit() {
    const bounds = workspace.getBoundingClientRect();
    const wanted = Math.min((bounds.width - 40) / world.offsetWidth, (bounds.height - 50) / world.offsetHeight, 1);
    scale = Math.max(.18, wanted);
    panX = 20;
    panY = 20;
    applyTransform();
    drawEdges();
  }

  search.addEventListener('input', () => {
    const query = search.value.trim().toLocaleLowerCase();
    if (!query) { clearSelection(); return; }
    let first = null;
    for (const [id, element] of nodes) {
      const item = fields.get(id) || transforms.get(id);
      const haystack = JSON.stringify(item).toLocaleLowerCase();
      const match = haystack.includes(query);
      element.classList.toggle('dim', !match);
      element.classList.toggle('related', match);
      if (match && !first) first = id;
    }
    selected = null;
    detail.hidden = true;
    drawEdges();
  });
  showAll.addEventListener('change', drawEdges);
  document.getElementById('reset').addEventListener('click', () => { search.value = ''; clearSelection(); });
  document.getElementById('closeDetail').addEventListener('click', clearSelection);
  document.getElementById('fit').addEventListener('click', fit);
  document.getElementById('zoomIn').addEventListener('click', () => { scale = Math.min(1.6, scale * 1.18); applyTransform(); drawEdges(); });
  document.getElementById('zoomOut').addEventListener('click', () => { scale = Math.max(.18, scale / 1.18); applyTransform(); drawEdges(); });
  workspace.addEventListener('wheel', event => {
    event.preventDefault();
    const rect = workspace.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    const beforeX = (mouseX - panX) / scale;
    const beforeY = (mouseY - panY) / scale;
    scale = Math.max(.18, Math.min(1.6, scale * (event.deltaY < 0 ? 1.1 : .9)));
    panX = mouseX - beforeX * scale;
    panY = mouseY - beforeY * scale;
    applyTransform();
    drawEdges();
  }, {passive: false});
  workspace.addEventListener('pointerdown', event => {
    if (event.target.closest('.node, .detail, .toolbar')) return;
    dragging = true;
    dragStart = {x: event.clientX, y: event.clientY, panX, panY};
    workspace.classList.add('dragging');
    workspace.setPointerCapture(event.pointerId);
  });
  workspace.addEventListener('pointermove', event => {
    if (!dragging) return;
    panX = dragStart.panX + event.clientX - dragStart.x;
    panY = dragStart.panY + event.clientY - dragStart.y;
    applyTransform();
  });
  workspace.addEventListener('pointerup', event => {
    dragging = false;
    workspace.classList.remove('dragging');
    if (workspace.hasPointerCapture(event.pointerId)) workspace.releasePointerCapture(event.pointerId);
  });
  window.addEventListener('resize', resizeWorld);
  applyTransform();
  requestAnimationFrame(() => { resizeWorld(); fit(); });
})();
</script>
</body>
</html>
'''
    return (
        template.replace("__TITLE__", title)
        .replace("__FINGERPRINT__", fingerprint[:12])
        .replace("__DATA__", payload)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and fail if generated files are stale; do not write.",
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Validate the manifest only."
    )
    args = parser.parse_args()
    data = load_manifest()
    errors = validate_manifest(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if args.validate_only:
        print("data_lineage.json is valid")
        return 0

    fingerprint = source_fingerprint()
    expected = {
        HTML_PATH: render_html(data, fingerprint),
        DICTIONARY_PATH: render_dictionary(data, fingerprint),
    }
    if args.check:
        stale = [
            str(path.relative_to(PROJECT_DIR))
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            print("Generated architecture files are stale: " + ", ".join(stale))
            return 1
        print("Generated architecture files are current")
        return 0

    for path, content in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(path.relative_to(PROJECT_DIR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
