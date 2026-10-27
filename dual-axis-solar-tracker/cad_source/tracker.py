"""
Dual-axis Arduino solar tracker - parametric CAD (CadQuery)
Units: mm. Change the parameters below and re-run to regenerate STL/STEP.

Parts:
  1. base_box   - holds Arduino Uno + mini breadboard, pan servo on the lid
  2. base_lid   - press-fit lid, pan (east-west) SG90 mounts here
  3. yoke       - U-bracket turned by the pan servo, carries the tilt SG90
  4. panel_frame- holds the solar panel + 4-LDR sensor cross (N/S/E/W)
"""
import cadquery as cq
import math, os

# ---------------- PARAMETERS ----------------
PANEL_W, PANEL_L, PANEL_T = 60.0, 110.0, 3.0   # solar panel (X width, Y length, thickness)
CLR = 0.3            # print clearance per side

# SG90 micro servo
SG_BODY_L, SG_BODY_W = 22.8, 12.4
SG_TAB_L = 32.5          # total length incl. mounting tabs
SG_HOLE_SPACING = 27.8
SG_SHAFT_OFF = 5.5       # shaft centre offset from body centre (along length)
SG_TAB_TO_BOTTOM = 15.9  # body below the tabs
HORN_GAP = 11.0          # tab (shaft-side face) -> face of printed part touching the horn
HORN_RECESS = 3.0        # recess depth for the horn arm

# base
BOX_X, BOX_Y, BOX_H = 140.0, 110.0, 52.0   # box without lid
WALL, FLOOR = 2.5, 2.5
LID_T = 3.0

# yoke / tilt
PIVOT_H = 62.0      # height of tilt axis above yoke plate top
PLATE_T = 7.0
LUG_T = 7.0
AXIS_ABOVE_TRAY = 13.5   # tilt axis height above tray bottom

# ---------------- helpers ----------------
def sg90_cutout_len(): return SG_BODY_L + 2 * CLR
def sg90_cutout_w():   return SG_BODY_W + 2 * CLR

def horn_single(wp_plane, depth):
    """single-arm horn recess sketch: hub d8 + arm to d5.5 at 17mm (+ local 'up')."""
    hub = cq.Workplane(wp_plane).circle(4.2).extrude(depth)
    arm = (cq.Workplane(wp_plane)
           .moveTo(0, 0).circle(4.2).moveTo(0, 17).circle(2.9)
           .extrude(depth))
    # hull approximation: loft-free trapezoid
    trap = (cq.Workplane(wp_plane)
            .polyline([(-4.2, 0), (4.2, 0), (2.9, 17), (-2.9, 17)]).close()
            .extrude(depth))
    return hub.union(arm).union(trap)

# =====================================================================
# 1. BASE BOX
# =====================================================================
ix, iy = BOX_X / 2 - WALL, BOX_Y / 2 - WALL
box = (cq.Workplane("XY").box(BOX_X, BOX_Y, BOX_H, centered=(True, True, False))
       .edges("|Z").fillet(6))
cavity = (cq.Workplane("XY").workplane(offset=FLOOR)
          .rect(2 * ix, 2 * iy).extrude(BOX_H)
          .edges("|Z").fillet(4))
box = box.cut(cavity)

# Arduino Uno position (board origin = lower-left, USB edge toward -X wall)
UNO_X0, UNO_Y0 = -ix + 6.8, -iy + 3.0
STANDOFF_H = 6.0
uno_holes = [(13.97, 2.54), (15.24, 50.8), (66.04, 7.62), (66.04, 35.56)]
for hx, hy in uno_holes:
    so = (cq.Workplane("XY").workplane(offset=FLOOR - 0.1)
          .center(UNO_X0 + hx, UNO_Y0 + hy).circle(3.2).extrude(STANDOFF_H + 0.1)
          .faces(">Z").workplane().hole(2.5, STANDOFF_H))
    box = box.union(so)
board_z = FLOOR + STANDOFF_H
# USB-B and DC jack windows in -X wall
def xwall_window(y0, y1, z0, z1, xpos):
    return (cq.Workplane("XY").box(WALL * 4, y1 - y0, z1 - z0, centered=(True, False, False))
            .translate((xpos, y0, z0)))
box = box.cut(xwall_window(UNO_Y0 + 30.5, UNO_Y0 + 45.5, board_z + 0.5, board_z + 14.5, -BOX_X / 2))
box = box.cut(xwall_window(UNO_Y0 + 2.0, UNO_Y0 + 14.0, board_z + 0.5, board_z + 14.0, -BOX_X / 2))
# wire hole for panel output / external 5V on +X wall
box = box.cut(cq.Workplane("YZ").workplane(offset=BOX_X / 2 - 5).center(20, 20).circle(4.5).extrude(10))
# lid support ledge + corner bosses
for sx in (-1, 1):
    for sy in (-1, 1):
        boss = (cq.Workplane("XY").workplane(offset=FLOOR - 0.1)
                .center(sx * (ix - 4), sy * (iy - 4)).circle(4.5)
                .extrude(BOX_H - FLOOR - 4.0 + 0.1))
        boss = boss.cut(cq.Workplane("XY").workplane(offset=BOX_H - 14)
                        .center(sx * (ix - 4), sy * (iy - 4)).circle(1.4).extrude(20))
        box = box.union(boss)

# =====================================================================
# 2. LID  (sits on top of box; lip goes inside the walls)
# =====================================================================
lid = (cq.Workplane("XY").box(BOX_X, BOX_Y, LID_T, centered=(True, True, False))
       .edges("|Z").fillet(6))
lip = (cq.Workplane("XY").rect(2 * ix - 0.6, 2 * iy - 0.6).extrude(-4)
       .cut(cq.Workplane("XY").rect(2 * ix - 4.6, 2 * iy - 4.6).extrude(-4)))
# clear the lip around the corner bosses
for sx in (-1, 1):
    for sy in (-1, 1):
        lip = lip.cut(cq.Workplane("XY").workplane(offset=-5)
                      .center(sx * (ix - 4), sy * (iy - 4)).circle(5.2).extrude(6))
lid = lid.union(lip)
# corner screw holes (optional M3 / servo screws)
for sx in (-1, 1):
    for sy in (-1, 1):
        lid = lid.cut(cq.Workplane("XY").workplane(offset=-1)
                      .center(sx * (ix - 4), sy * (iy - 4)).circle(1.7).extrude(10))
# pan servo cutout: shaft at (0,0), body toward -X
pan_body_cx = -SG_SHAFT_OFF
lid = lid.cut(cq.Workplane("XY").workplane(offset=-10).center(pan_body_cx, 0)
              .rect(sg90_cutout_len(), sg90_cutout_w()).extrude(20))
for s in (-1, 1):
    lid = lid.cut(cq.Workplane("XY").workplane(offset=-5)
                  .center(pan_body_cx + s * SG_HOLE_SPACING / 2, 0).circle(0.9).extrude(20))
# cable pass-through
lid = lid.cut(cq.Workplane("XY").workplane(offset=-5).center(0, 30).circle(8).extrude(20))
# engraved direction marks: arrow + "S" on +Y side, "N" on -Y
arrow = (cq.Workplane("XY").workplane(offset=LID_T - 0.8)
         .polyline([(-3, 38), (3, 38), (3, 43), (7, 43), (0, 50), (-7, 43), (-3, 43)]).close()
         .extrude(2))
lid = lid.cut(arrow)
try:
    for txt, pos in (("S", (15, 44)), ("N", (0, -46)), ("E", (-60, 0)), ("W", (60, 0))):
        t = (cq.Workplane("XY").workplane(offset=LID_T - 0.8).center(*pos)
             .text(txt, 9, 2, kind="bold", combine=False))
        lid = lid.cut(t)
except Exception as e:
    print("text skipped:", e)

LID_TOP = BOX_H + LID_T  # z of lid top in assembly

# =====================================================================
# 3. YOKE (local z=0 = underside of plate, pan axis at x=y=0)
# =====================================================================
Z_AXIS = PLATE_T + PIVOT_H
TRAY_HALF_X = (PANEL_W + 2 * CLR) / 2 + 2.5
LUG_OUT = TRAY_HALF_X + LUG_T                      # lug outer face |x|
ARM_P_OUT = LUG_OUT + HORN_GAP                     # +X arm outer face (servo tabs here)
ARM_P_IN = ARM_P_OUT - 4.0
ARM_N_IN = -(LUG_OUT + 2.0)                        # -X arm (pivot side), 2mm washer gap
ARM_N_OUT = ARM_N_IN - 4.0

plate = (cq.Workplane("XY").center((ARM_N_OUT - 4 + ARM_P_OUT + 4) / 2, 0)
         .rect(ARM_P_OUT - ARM_N_OUT + 8, 28).extrude(PLATE_T))
pads = (cq.Workplane("XY").center((ARM_P_OUT + 4 + TRAY_HALF_X + 4) / 2, 0)
        .rect(ARM_P_OUT + 4 - TRAY_HALF_X - 4, 48).extrude(PLATE_T)
        .union(cq.Workplane("XY").center((ARM_N_OUT - 4 - TRAY_HALF_X - 4) / 2, 0)
               .rect(-(ARM_N_OUT - 4) - TRAY_HALF_X - 4, 48).extrude(PLATE_T)))
yoke = plate.union(pads).edges("|Z").fillet(3)
# pan horn recess (double-arm horn along X) + screwdriver hole
horn2 = (cq.Workplane("XY").workplane(offset=-0.01)
         .polyline([(-17, -2.9), (0, -4.2), (17, -2.9), (17, 2.9), (0, 4.2), (-17, 2.9)]).close()
         .extrude(HORN_RECESS + 0.01))
horn2 = horn2.union(cq.Workplane("XY").workplane(offset=-0.01).pushPoints([(-17, 0), (17, 0)])
                    .circle(2.9).extrude(HORN_RECESS + 0.01))
horn2 = horn2.union(cq.Workplane("XY").workplane(offset=-0.01).circle(4.2).extrude(HORN_RECESS + 0.01))
yoke = yoke.cut(horn2)
yoke = yoke.cut(cq.Workplane("XY").workplane(offset=-1).circle(3.2).extrude(PLATE_T + 2))
# wire holes through plate
yoke = yoke.cut(cq.Workplane("XY").workplane(offset=-1).pushPoints([(ARM_P_IN - 7, 16), (ARM_N_IN + 7, 16)])
                .circle(3.5).extrude(PLATE_T + 2))

# +X arm with tilt servo
arm_top_p = Z_AXIS + 14
arm_p = (cq.Workplane("YZ").workplane(offset=ARM_P_IN)
         .center(0, (PLATE_T - 0.1 + arm_top_p) / 2).rect(26, arm_top_p - PLATE_T + 0.1)
         .extrude(4.0).edges("|X and >Z").fillet(8))
tilt_body_cz = Z_AXIS - SG_SHAFT_OFF   # shaft end up
arm_p = arm_p.cut(cq.Workplane("YZ").workplane(offset=ARM_P_IN - 1).center(0, tilt_body_cz)
                  .rect(sg90_cutout_w(), sg90_cutout_len()).extrude(6))
arm_p = arm_p.cut(cq.Workplane("YZ").workplane(offset=ARM_P_IN - 1)
                  .pushPoints([(0, tilt_body_cz - SG_HOLE_SPACING / 2), (0, tilt_body_cz + SG_HOLE_SPACING / 2)])
                  .circle(0.9).extrude(6))
# -X arm with M3 pivot hole
arm_top_n = Z_AXIS + 11
arm_n = (cq.Workplane("YZ").workplane(offset=ARM_N_OUT)
         .center(0, (PLATE_T - 0.1 + arm_top_n) / 2).rect(22, arm_top_n - PLATE_T + 0.1)
         .extrude(4.0).edges("|X and >Z").fillet(10))
arm_n = arm_n.cut(cq.Workplane("YZ").workplane(offset=ARM_N_OUT - 1).center(0, Z_AXIS).circle(1.7).extrude(6))
yoke = yoke.union(arm_p).union(arm_n)

# gussets (triangles in XZ plane) at both Y edges of each arm, inside and outside
def gusset(x_face, direction, y, h=26, L=9, t=3):
    x2 = x_face + direction * L
    return (cq.Workplane("XZ", origin=(0, y + t / 2, 0))
            .polyline([(x_face, PLATE_T - 0.1), (x2, PLATE_T - 0.1), (x_face, PLATE_T + h)]).close()
            .extrude(t))
for y in (-11.5, 11.5):
    yoke = yoke.union(gusset(ARM_P_IN + 0.1, -1, y))
    yoke = yoke.union(gusset(ARM_P_OUT - 0.1, +1, y, h=22, L=4.5))
for y in (-9.5, 9.5):
    yoke = yoke.union(gusset(ARM_N_IN - 0.1, +1, y))
    yoke = yoke.union(gusset(ARM_N_OUT + 0.1, -1, y, h=22, L=4.5))

# =====================================================================
# 4. PANEL FRAME (local origin = tilt axis; tray bottom at z=-AXIS_ABOVE_TRAY)
# =====================================================================
pw, pl = PANEL_W + 2 * CLR, PANEL_L + 2 * CLR
FLOOR_F = 2.5
tray_h = FLOOR_F + PANEL_T + 0.5
zb = -AXIS_ABOVE_TRAY
tray = (cq.Workplane("XY").workplane(offset=zb).rect(pw + 5, pl + 5).extrude(tray_h)
        .edges("|Z").fillet(2))
tray = tray.cut(cq.Workplane("XY").workplane(offset=zb + FLOOR_F).rect(pw, pl).extrude(tray_h))
window = (cq.Workplane("XY").workplane(offset=zb - 1).rect(pw - 12, pl - 12).extrude(FLOOR_F + 2)
          .cut(cq.Workplane("XY").workplane(offset=zb - 1).rect(pw, 8).extrude(FLOOR_F + 2)))
tray = tray.cut(window)
# finger notches to pop the panel out
tray = tray.cut(cq.Workplane("XY").workplane(offset=zb + FLOOR_F).pushPoints([(0, pl / 2 + 1), (0, -pl / 2 - 1)])
                .rect(14, 4).extrude(10))

def lug(side):
    x0 = TRAY_HALF_X - 0.1 if side > 0 else -TRAY_HALF_X - LUG_T + 0.1
    base = (cq.Workplane("YZ").workplane(offset=x0).center(0, zb / 2).rect(24, -zb).extrude(LUG_T))
    top = (cq.Workplane("YZ").workplane(offset=x0)
           .polyline([(-12, 0), (12, 0), (5.5, 19), (-5.5, 19)]).close().extrude(LUG_T))
    c1 = cq.Workplane("YZ").workplane(offset=x0).circle(12).extrude(LUG_T)
    c2 = cq.Workplane("YZ").workplane(offset=x0).center(0, 19).circle(5.5).extrude(LUG_T)
    return base.union(top).union(c1).union(c2)

frame = tray.union(lug(+1)).union(lug(-1))
# +X lug: horn recess on outer face (single-arm horn pointing up) + screwdriver hole
hr = horn_single(cq.Plane(origin=(LUG_OUT - HORN_RECESS, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0)), HORN_RECESS + 1)
frame = frame.cut(hr)
frame = frame.cut(cq.Workplane("YZ").workplane(offset=TRAY_HALF_X - 2).circle(3.2).extrude(LUG_T + 3))
# -X lug: M3 self-tap hole
frame = frame.cut(cq.Workplane("YZ").workplane(offset=-LUG_OUT - 1).circle(1.45).extrude(LUG_T + 1))

# sensor head at -Y end: 4 LDRs (N, S, E, W) separated by an X-shaped shadow divider
HEAD = 34.0
head_cy = -(pl / 2 + 2.5) - HEAD / 2 + 1
head = (cq.Workplane("XY").workplane(offset=zb).center(0, head_cy).rect(HEAD, HEAD + 2).extrude(4)
        .edges("|Z").fillet(3))
wall_len = HEAD * math.sqrt(2) - 4
for ang in (45, -45):
    w = (cq.Workplane("XY").workplane(offset=zb + 3.9).center(0, head_cy)
         .transformed(rotate=(0, 0, ang)).rect(wall_len, 1.8).extrude(20.1))
    head = head.union(w)
head = head.intersect(cq.Workplane("XY").workplane(offset=zb - 1).center(0, head_cy)
                      .rect(HEAD, HEAD + 2).extrude(40))
ldr_pts = [(0, head_cy - 9), (0, head_cy + 9), (-9, head_cy), (9, head_cy)]  # top(N), bottom(S), E, W
head = head.cut(cq.Workplane("XY").workplane(offset=zb + 4 - 1.5).pushPoints(ldr_pts).circle(2.7).extrude(5))
head = head.cut(cq.Workplane("XY").workplane(offset=zb - 1).pushPoints(ldr_pts).circle(2.1).extrude(10))
frame = frame.union(head)

# =====================================================================
# EXPORT
# =====================================================================
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
parts = {"1_base_box": box, "2_base_lid": lid, "3_yoke": yoke, "4_panel_frame": frame}
if __name__ == "__main__":
    for n, p in parts.items():
        cq.exporters.export(p, f"{OUT}/{n}.stl", tolerance=0.05, angularTolerance=0.2)
        cq.exporters.export(p, f"{OUT}/{n}.step")
        bb = p.val().BoundingBox()
        print(n, "valid" if p.val().isValid() else "INVALID",
              f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")
