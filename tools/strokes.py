"""Broad-nib stroke engine.

A glyph is a set of strokes. Each stroke is a skeleton path (lines, elliptical
arcs, cubics) swept by an elliptical nib of width v and height h. Vertical
strokes come out v thick and horizontal strokes h thick, which gives the soft
stroke modulation seen in the reference specimen. Because the point structure
depends only on the skeleton, masters of different weight stay interpolation
compatible by construction.

Contours come out counter-clockwise (UFO outer-contour convention).
"""
import math

ARC_STEP = 15  # degrees between samples on arcs
CUBIC_STEPS = 10
CAP_STEPS = 6


class Nib:
    def __init__(self, v: float, h: float):
        self.a, self.b = v / 2, h / 2

    def support(self, nx, ny):
        """Point on the nib boundary whose outward normal is (nx, ny)."""
        s = math.hypot(self.a * nx, self.b * ny)
        return (self.a ** 2 * nx / s, self.b ** 2 * ny / s)

    def point(self, t):
        return (self.a * math.cos(t), self.b * math.sin(t))

    def deriv(self, t):
        return (-self.a * math.sin(t), self.b * math.cos(t))

    def alpha(self, nx, ny):
        return math.atan2(self.b * ny, self.a * nx)


def line(p0, p1):
    return {"kind": "line", "p0": p0, "p1": p1}


def arc(cx, cy, rx, ry, a0, a1):
    """Elliptical arc on the skeleton, angles in degrees; a1 < a0 is clockwise."""
    return {"kind": "arc", "c": (cx, cy), "r": (rx, ry), "a": (a0, a1)}


def cubic(p0, p1, p2, p3):
    return {"kind": "cubic", "p": (p0, p1, p2, p3)}


def _unit(x, y):
    d = math.hypot(x, y)
    return (x / d, y / d)


def _sample_seg(s):
    k = s["kind"]
    if k == "line":
        (x0, y0), (x1, y1) = s["p0"], s["p1"]
        t = _unit(x1 - x0, y1 - y0)
        return [((x0, y0), t), ((x1, y1), t)]
    if k == "arc":
        (cx, cy), (rx, ry), (a0, a1) = s["c"], s["r"], s["a"]
        sweep = a1 - a0
        sign = 1 if sweep > 0 else -1
        n = max(2, math.ceil(abs(sweep) / ARC_STEP))
        out = []
        for i in range(n + 1):
            t = math.radians(a0 + sweep * i / n)
            p = (cx + rx * math.cos(t), cy + ry * math.sin(t))
            out.append((p, _unit(-rx * math.sin(t) * sign, ry * math.cos(t) * sign)))
        return out
    p0, p1, p2, p3 = s["p"]
    out = []
    for i in range(CUBIC_STEPS + 1):
        t = i / CUBIC_STEPS
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        dx = 3 * (mt**2 * (p1[0] - p0[0]) + 2 * mt * t * (p2[0] - p1[0]) + t**2 * (p3[0] - p2[0]))
        dy = 3 * (mt**2 * (p1[1] - p0[1]) + 2 * mt * t * (p2[1] - p1[1]) + t**2 * (p3[1] - p2[1]))
        out.append(((x, y), _unit(dx, dy)))
    return out


def _sample(segs):
    pts, kinds = [], []
    for i, s in enumerate(segs):
        ps = _sample_seg(s)
        kinds.extend([s["kind"]] * (len(ps) - 1))
        pts.extend(ps if i == 0 else ps[1:])
    return pts, kinds


def _edge(ops, a, b, ta, tb, kind):
    if kind == "line":
        ops.append(("line", b))
        return
    d = math.dist(a, b)
    ops.append(("curve", (a[0] + ta[0] * d / 3, a[1] + ta[1] * d / 3),
                (b[0] - tb[0] * d / 3, b[1] - tb[1] * d / 3), b))


def _cap(ops, nib, p, a, b, alpha0, style):
    """Counter-clockwise cap from a to b along the nib boundary (or a flat cut)."""
    if style == "flat":
        ops.append(("line", b))
        return
    da = math.pi / CAP_STEPS
    k = 4 / 3 * math.tan(da / 4)
    prev, prev_t = a, alpha0
    for i in range(1, CAP_STEPS + 1):
        t = alpha0 + da * i
        q = b if i == CAP_STEPS else (p[0] + nib.point(t)[0], p[1] + nib.point(t)[1])
        d0, d1 = nib.deriv(prev_t), nib.deriv(t)
        ops.append(("curve", (prev[0] + k * d0[0], prev[1] + k * d0[1]),
                    (q[0] - k * d1[0], q[1] - k * d1[1]), q))
        prev, prev_t = q, t


def stroke_contour(segs, nib, caps=("round", "round")):
    """Return drawing ops [("move", p), ("line", p), ("curve", c1, c2, p), ...]."""
    pts, kinds = _sample(segs)
    n = len(pts)
    left, right = [], []
    for p, t in pts:
        ex, ey = nib.support(-t[1], t[0])
        left.append((p[0] + ex, p[1] + ey))
        right.append((p[0] - ex, p[1] - ey))
    ops = [("move", right[0])]
    for i in range(n - 1):
        _edge(ops, right[i], right[i + 1], pts[i][1], pts[i + 1][1], kinds[i])
    p, t = pts[-1]
    _cap(ops, nib, p, right[-1], left[-1], nib.alpha(t[1], -t[0]), caps[1])
    for i in range(n - 1, 0, -1):
        ti, tj = pts[i][1], pts[i - 1][1]
        _edge(ops, left[i], left[i - 1], (-ti[0], -ti[1]), (-tj[0], -tj[1]), kinds[i - 1])
    p, t = pts[0]
    _cap(ops, nib, p, left[0], right[0], nib.alpha(-t[1], t[0]), caps[0])
    return ops


def draw_ops(pen, ops, dx=0.0, dy=0.0):
    def r(p):
        return (round(p[0] + dx, 2), round(p[1] + dy, 2))
    for op in ops:
        if op[0] == "move":
            pen.moveTo(r(op[1]))
        elif op[0] == "line":
            pen.lineTo(r(op[1]))
        else:
            pen.curveTo(r(op[1]), r(op[2]), r(op[3]))
    pen.closePath()


def signed_area(ops, steps=8):
    """Approximate signed area (positive = counter-clockwise), for self-checks."""
    pts, cur = [], None
    for op in ops:
        if op[0] in ("move", "line"):
            cur = op[1]
            pts.append(cur)
        else:
            c1, c2, e = op[1], op[2], op[3]
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                pts.append((mt**3 * cur[0] + 3 * mt**2 * t * c1[0] + 3 * mt * t**2 * c2[0] + t**3 * e[0],
                            mt**3 * cur[1] + 3 * mt**2 * t * c1[1] + 3 * mt * t**2 * c2[1] + t**3 * e[1]))
            cur = e
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
