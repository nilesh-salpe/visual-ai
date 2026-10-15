"""Render a steppable box-and-arrow diagram from YAML (the `::: diagram` block in deck.md).

    ::: diagram 660x300
    nodes:
      user: {at: [20, 120, 110, 56], text: User, sub: goal, color: f, step: 1}
      loop: {at: [200, 110, 150, 76], text: Agent loop, sub: LLM decides, color: a, step: 2}
    edges:
      - {from: user, to: loop, label: task, step: 1}
      - {from: loop, to: user, label: answer, step: 3, style: back}   # style: dash | back
    steps:
      - The user states a goal.
      - ...
    :::

`at` is [x, y, width, height] in the viewBox; colours are the deck palette letters a-e, or f (faint).
An element appears when the stepper reaches its `step` (0 = always shown); steps[i] captions step i + 1.
All styling comes from the .dg classes in shared/deck.css; stepping is in shared/diagram.js.
"""
import html, json, sys
import yaml

_count = [0]


def _clip(cx, cy, w, h, tx, ty):
    """Point where the segment from a box centre toward (tx, ty) leaves the box."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2) / abs(dx) if dx else float('inf')
    sy = (h / 2) / abs(dy) if dy else float('inf')
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def _crosses(n, x1, y1, x2, y2):
    x, y, w, h = n['at']
    return any(x - 2 <= x1 + (x2 - x1) * t / 40 <= x + w + 2 and y - 2 <= y1 + (y2 - y1) * t / 40 <= y + h + 2 for t in range(1, 40))


def _inside(a, b):
    ax, ay, aw, ah = a['at']; bx, by, bw, bh = b['at']
    return bx <= ax and ax + aw <= bx + bw and by <= ay and ay + ah <= by + bh


def render(args, body, where=''):
    W, H = (int(v) for v in (args or '660x300').split('x'))
    spec = yaml.safe_load(body)
    nodes, edges, steps = spec['nodes'], spec.get('edges') or [], spec.get('steps') or []
    _count[0] += 1
    mid = f'dga{_count[0]}'                      # unique marker id: duplicate ids hide arrowheads on pages with several diagrams
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="diagram">',
           f'<defs><marker id="{mid}" class="dg-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker></defs>']
    labels = []
    for e in edges:
        a, b = nodes[e['from']], nodes[e['to']]
        (axx, ayy, aw, ah), (bxx, byy, bw, bh) = a['at'], b['at']
        ax, ay, bx, by = axx + aw / 2, ayy + ah / 2, bxx + bw / 2, byy + bh / 2
        style = e.get('style', '')
        if style == 'back':                      # parallel return arrow, shifted to the other side of the forward arrow's label
            vx, vy = bx - ax, by - ay
            L = (vx * vx + vy * vy) ** 0.5 or 1
            px, py = vy / L * 10, -vx / L * 10
            ax, ay, bx, by = ax + px, ay + py, bx + px, by + py
        x1, y1 = _clip(ax, ay, aw + 4, ah + 4, bx, by)
        x2, y2 = _clip(bx, by, bw + 8, bh + 8, ax, ay)
        for k, n in nodes.items():               # layout check: an arrow should not cross a box it does not connect
            if k in (e['from'], e['to']) or _inside(a, n) or _inside(b, n):
                continue
            if _crosses(n, x1, y1, x2, y2):
                print(f'  LAYOUT {where}: edge {e["from"]}->{e["to"]} crosses box {k}', file=sys.stderr)
        cls = 'dg-edge' + (' dash' if style in ('dash', 'back') else '')
        step = e.get('step', 0)
        out.append(f'<g class="{cls}" data-step="{step}"><line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" marker-end="url(#{mid})"/></g>')
        if e.get('label'):
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ly = my + 15 if style == 'back' else my - 5
            labels.append(f'<g data-step="{step}"><text class="dg-label" x="{mx:.1f}" y="{ly:.1f}" text-anchor="middle">{html.escape(str(e["label"]))}</text></g>')
    for k, n in nodes.items():
        x, y, w, h = n['at']
        sub = n.get('sub')
        out.append(f'<g class="dg-node {n.get("color", "f")}" data-step="{n.get("step", 0)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>'
                   f'<text class="dg-text" x="{x + w / 2}" y="{y + (h / 2 - 2 if sub else h / 2 + 5)}" text-anchor="middle">{html.escape(str(n["text"]))}</text>'
                   + (f'<text class="dg-sub" x="{x + w / 2}" y="{y + h / 2 + 14}" text-anchor="middle">{html.escape(str(sub))}</text>' if sub else '') + '</g>')
    out.extend(labels)                           # labels last, so boxes never hide them
    out.append('</svg>')
    caps = html.escape(json.dumps(steps, ensure_ascii=False), quote=True)
    return (f'<div class="visual dgm" data-steps="{caps}"><div class="controls"><button class="btn primary" data-dg="next">next step</button>'
            f'<button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div>{"".join(out)}<p class="readout dgcap"></p></div>')
