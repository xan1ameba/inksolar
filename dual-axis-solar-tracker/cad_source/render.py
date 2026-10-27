from check import *
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def tris(wp, tol=0.3):
    vs, ts = wp.val().tessellate(tol, 0.3)
    v = np.array([(p.x, p.y, p.z) for p in vs]); return v[np.array(ts)]

panel = (cq.Workplane("XY").workplane(offset=-AXIS_ABOVE_TRAY + 2.5)
         .rect(PANEL_W, PANEL_L).extrude(PANEL_T))
def assembly(tilt_deg, pan_deg):
    fr = frame.union(panel) if False else None
    items = [(box, "#d8dde3"), (lid_a, "#c4ccd6"), (pan_servo, "#2f6fd6")]
    rot = lambda w: w.rotate((0, 0, 0), (0, 0, 1), pan_deg)
    items += [(rot(yoke_a), "#f2a33a"), (rot(tilt), "#2f6fd6")]
    t = lambda w: rot(w.rotate((0, 0, 0), (1, 0, 0), tilt_deg).translate((0, 0, AX_Z)))
    items += [(t(frame), "#f2a33a"), (t(panel), "#1b2a4a")]
    return items

def draw(ax, items, elev, azim):
    light = np.array([0.4, -0.5, 0.8]); light /= np.linalg.norm(light)
    for wp, col in items:
        T = tris(wp)
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-9)
        shade = 0.45 + 0.55 * np.abs(n @ light)
        base = np.array(matplotlib.colors.to_rgb(col))
        fc = np.clip(base[None, :] * shade[:, None], 0, 1)
        pc = Poly3DCollection(T, facecolors=fc, edgecolors="none", linewidths=0)
        ax.add_collection3d(pc)
    ax.set_xlim(-90, 90); ax.set_ylim(-90, 90); ax.set_zlim(0, 180)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.axis("off")

fig = plt.figure(figsize=(14, 7), dpi=110)
for i, (tl, pn, el, az, title) in enumerate([
        (0, 0, 22, -60, "Panel flat (servo tilt 90°)"),
        (-45, 30, 18, -50, "Tracking: tilted 45° toward sun, turned 30°")]):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    draw(ax, assembly(tl, pn), el, az); ax.set_title(title)
plt.tight_layout(); plt.savefig("out/preview_assembly.png", bbox_inches="tight")

# individual part sheet
fig = plt.figure(figsize=(14, 4), dpi=100)
for i, (wp, n) in enumerate([(box, "1 base box"), (lid, "2 lid"), (yoke, "3 yoke"), (frame, "4 panel frame")]):
    ax = fig.add_subplot(1, 4, i + 1, projection="3d")
    bb = wp.val().BoundingBox(); c = bb.center; r = max(bb.xlen, bb.ylen, bb.zlen) / 2
    draw(ax, [(wp, "#f2a33a")], 30, -55)
    ax.set_xlim(c.x - r, c.x + r); ax.set_ylim(c.y - r, c.y + r); ax.set_zlim(c.z - r, c.z + r)
    ax.set_title(n)
plt.tight_layout(); plt.savefig("out/preview_parts.png", bbox_inches="tight")
