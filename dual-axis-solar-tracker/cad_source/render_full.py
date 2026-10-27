import trimesh, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
sc = trimesh.load("out/solar_tracker_FULL_ASSEMBLY.glb")
T_all, C_all, names = [], [], []
for node in sc.graph.nodes_geometry:
    tf, gname = sc.graph[node]
    m = sc.geometry[gname].copy(); m.apply_transform(tf)
    try: col = np.array(m.visual.material.baseColorFactor[:3]) / 255.0
    except Exception: col = np.array([.8, .8, .8])
    if col.max() > 1: col = col / 255
    T_all.append(m.triangles); C_all.append(np.repeat(col[None], len(m.triangles), 0)); names.append(node)
T = np.concatenate(T_all); Cc = np.concatenate(C_all)
# glTF is Y-up: convert back to Z-up
T = T[..., [0, 2, 1]]; T[..., 1] *= -1
print(len(names), "parts:", sorted(set(n.split("/")[-1] for n in names))[:40])
light = np.array([0.4, -0.6, 0.8]); light /= np.linalg.norm(light)
def draw(ax, cut=False, elev=20, azim=-60):
    TT, CC = T, Cc
    if cut:  # cut-away: hide box/lid front half
        keep = ~((np.all(TT[..., 1] < 0, axis=1)) & (np.all(TT[..., 2] < 56, axis=1)) & np.all(np.isclose(CC, CC[0]), axis=1))
    n = np.cross(TT[:, 1] - TT[:, 0], TT[:, 2] - TT[:, 0]); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
    fc = np.clip(CC * (0.45 + 0.55 * np.abs(n @ light))[:, None], 0, 1)
    ax.add_collection3d(Poly3DCollection(TT, facecolors=fc, edgecolors="none"))
    ax.set_xlim(-85, 85); ax.set_ylim(-85, 85); ax.set_zlim(0, 170); ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev, azim); ax.axis("off")
fig = plt.figure(figsize=(14, 7), dpi=110)
ax = fig.add_subplot(1, 2, 1, projection="3d"); draw(ax, elev=22, azim=-60); ax.set_title("Full assembly")
ax = fig.add_subplot(1, 2, 2, projection="3d"); draw(ax, elev=10, azim=-150); ax.set_title("Side view (Arduino USB side)")
plt.tight_layout(); plt.savefig("out/preview_full_assembly.png", bbox_inches="tight")
