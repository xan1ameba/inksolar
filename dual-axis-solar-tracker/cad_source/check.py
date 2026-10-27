from tracker import *
import cadquery as cq

YOKE_Z = LID_TOP + 2.5 + HORN_GAP
AX_Z = YOKE_Z + Z_AXIS

# dummy servos
def sg90():
    b = cq.Workplane("XY").box(SG_BODY_L, SG_BODY_W, 22.7, centered=(True, True, False)).translate((0, 0, -SG_TAB_TO_BOTTOM))
    t = cq.Workplane("XY").box(SG_TAB_L, SG_BODY_W, 2.5, centered=(True, True, False))
    hump = cq.Workplane("XY").workplane(offset=22.7 - SG_TAB_TO_BOTTOM).center(SG_SHAFT_OFF, 0).circle(5.9).extrude(4)
    shaft = cq.Workplane("XY").workplane(offset=10).center(SG_SHAFT_OFF, 0).circle(2.4).extrude(2.6)
    # tab-top at z=2.5 ; shaft at x=+SHAFT_OFF ; here tab bottom z=0
    return b.union(t).union(hump).union(shaft).translate((-SG_SHAFT_OFF, 0, 0))
pan_servo = sg90().translate((0, 0, LID_TOP))
# tilt servo: shaft along -X, tab shaft-side face at x=ARM_P_OUT, shaft end up (+Z)
tilt = (sg90().translate((0, 0, -2.5))            # tab top face at z=0
        .rotate((0, 0, 0), (0, 1, 0), -90)        # +Z -> -X
        .rotate((0, 0, 0), (1, 0, 0), 0))
bb = tilt.val().BoundingBox()
# ensure shaft ends up at z=+0 offset: find shaft offset direction via bbox after transforms
tilt = tilt.translate((ARM_P_OUT, 0, AX_Z))

yoke_a = yoke.translate((0, 0, YOKE_Z))
lid_a = lid.translate((0, 0, BOX_H))
statics = {"yoke": yoke_a, "lid": lid_a, "pan_servo": pan_servo, "tilt_servo": tilt}

if __name__ == "__main__":
    print("tilt servo bbox", tilt.val().BoundingBox().zmin - AX_Z, tilt.val().BoundingBox().zmax - AX_Z)
    print("pan servo vs lid:", pan_servo.intersect(lid_a).val().Volume() if True else 0)
    print("pan servo vs yoke:", pan_servo.intersect(yoke_a).val().Volume())
    print("tilt servo vs yoke:", tilt.intersect(yoke_a).val().Volume())
    for ang in range(-90, 91, 10):
        f = frame.rotate((0, 0, 0), (1, 0, 0), ang).translate((0, 0, AX_Z))
        hits = []
        for n, s in statics.items():
            try:
                v = f.intersect(s).val().Volume()
            except Exception:
                v = 0
            if v > 0.5: hits.append(f"{n}:{v:.0f}")
        print(ang, hits)
