"""Full assembled model: all printed parts + servos, horns, Arduino, breadboard, panel, LDRs, bolt."""
from check import *   # parts + positions (YOKE_Z, AX_Z, sg90, ...)
import cadquery as cq

TILT = 0  # panel angle for the assembly (0 = flat; negative = tilted toward south)

# ---------- purchased parts (simplified) ----------
def uno():
    b = cq.Workplane("XY").box(68.6, 53.3, 1.6, centered=False).edges("|Z").fillet(1)
    usb = cq.Workplane("XY").box(16, 12, 11, centered=False).translate((-6.3, 31.8, 1.6))
    dc = cq.Workplane("XY").box(13.7, 9, 11, centered=False).translate((-1.8, 3.3, 1.6))
    h1 = cq.Workplane("XY").box(38, 2.5, 8.5, centered=False).translate((27, 49.5, 1.6))
    h2 = cq.Workplane("XY").box(35, 2.5, 8.5, centered=False).translate((27, 1.2, 1.6))
    chip = cq.Workplane("XY").box(35, 7.5, 4, centered=False).translate((30, 20, 1.6))
    return {"pcb": b, "connectors": usb.union(dc), "headers": h1.union(h2).union(chip)}

def horn_double(t=1.8):
    return (cq.Workplane("XY")
            .polyline([(-16, -2.5), (0, -3.6), (16, -2.5), (16, 2.5), (0, 3.6), (-16, 2.5)]).close()
            .extrude(t).union(cq.Workplane("XY").circle(3.6).extrude(-3.5)))

def horn_single(t=1.8):
    return (cq.Workplane("XY").polyline([(-3.6, 0), (3.6, 0), (2.5, 16), (-2.5, 16)]).close().extrude(t)
            .union(cq.Workplane("XY").circle(3.6).extrude(t))
            .union(cq.Workplane("XY").center(0, 16).circle(2.5).extrude(t))
            .union(cq.Workplane("XY").circle(3.6).extrude(-3.5)))

def ldr():
    d = cq.Workplane("XY").circle(2.55).extrude(2)
    legs = cq.Workplane("XY").pushPoints([(-1.7, 0), (1.7, 0)]).circle(0.25).extrude(-25)
    return d.union(legs)

# ---------- place everything ----------
A = cq.Assembly(name="solar_tracker")
C = lambda *rgb: cq.Color(*rgb)
PRINT = C(0.95, 0.62, 0.20)
BASEC = C(0.82, 0.85, 0.89)
SERVO = C(0.18, 0.42, 0.85)
BLACK = C(0.1, 0.1, 0.12)
WHITE = C(0.95, 0.95, 0.95)

A.add(box, name="1_base_box", color=BASEC)
A.add(lid_a, name="2_base_lid", color=C(0.72, 0.77, 0.84))

u = uno()
loc_uno = cq.Location(cq.Vector(UNO_X0, UNO_Y0, board_z))
A.add(u["pcb"], name="arduino_uno_pcb", loc=loc_uno, color=C(0.0, 0.45, 0.6))
A.add(u["connectors"], name="arduino_usb_dc", loc=loc_uno, color=C(0.7, 0.7, 0.72))
A.add(u["headers"], name="arduino_headers", loc=loc_uno, color=BLACK)
bb_ = (cq.Workplane("XY").box(47, 35, 8.5, centered=False)
       .faces(">Z").workplane().rarray(2.54, 2.54, 17, 12).rect(1, 1).cutBlind(-3))
A.add(bb_, name="mini_breadboard", loc=cq.Location(cq.Vector(12, 8, FLOOR)), color=WHITE)

A.add(pan_servo, name="servo_pan_SG90", color=SERVO)
A.add(horn_double(), name="horn_pan", loc=cq.Location(cq.Vector(0, 0, LID_TOP + 2.5 + 11.6)), color=WHITE)

# rotating group: yoke + tilt servo + tilt horn + frame + panel + LDRs + bolt
yoke_grp = cq.Assembly(name="rotating_head")
yoke_grp.add(yoke_a, name="3_yoke", color=PRINT)
yoke_grp.add(tilt, name="servo_tilt_SG90", color=SERVO)
th = horn_single().rotate((0, 0, 0), (0, 1, 0), -90).rotate((0, 0, 0), (1, 0, 0), 90)  # plate -> -X, arm up
# horn plate occupies d = 11.6..13.4 inward from arm outer face
yoke_grp.add(th.translate((ARM_P_OUT - 11.6, 0, AX_Z)), name="horn_tilt", color=WHITE)
bolt = (cq.Workplane("YZ").circle(2.75).extrude(-3)
        .union(cq.Workplane("YZ").circle(1.5).extrude(16)))
yoke_grp.add(bolt.translate((ARM_N_OUT, 0, AX_Z)), name="M3x16_pivot_bolt", color=C(0.6, 0.6, 0.62))

tilt_grp = cq.Assembly(name="tilting_panel", loc=cq.Location(cq.Vector(0, 0, AX_Z), cq.Vector(1, 0, 0), TILT))
tilt_grp.add(frame, name="4_panel_frame", color=PRINT)
zb = -AXIS_ABOVE_TRAY
panel = cq.Workplane("XY").workplane(offset=zb + 2.5).rect(PANEL_W, PANEL_L).extrude(PANEL_T)
cells = (cq.Workplane("XY").workplane(offset=zb + 2.5 + PANEL_T).rarray(PANEL_W / 4, PANEL_L / 6, 4, 6)
         .rect(PANEL_W / 4 - 1.5, PANEL_L / 6 - 1.5).extrude(0.2))
tilt_grp.add(panel, name="solar_panel", color=C(0.1, 0.13, 0.25))
tilt_grp.add(cells, name="solar_cells", color=C(0.12, 0.2, 0.45))
for nm, (x, y) in zip(["LDR_top_N", "LDR_bottom_S", "LDR_east", "LDR_west"], ldr_pts):
    tilt_grp.add(ldr(), name=nm, loc=cq.Location(cq.Vector(x, y, zb + 2.5)), color=C(0.85, 0.3, 0.2))
yoke_grp.add(tilt_grp)
A.add(yoke_grp)

import os
os.makedirs("out", exist_ok=True)
A.save("out/solar_tracker_FULL_ASSEMBLY.step")
try:
    A.save("out/solar_tracker_FULL_ASSEMBLY.glb")
except Exception as e:
    print("glb:", e)
print("saved")
