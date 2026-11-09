"""Mute button enclosure: a hand-held cylinder with a 30mm arcade button on top.

Run inside FreeCAD (Python console, macro, or via the FreeCAD MCP addon):
    exec(open("/path/to/cad/enclosure.py").read())

Builds three printable parts plus transparent reference "ghosts":
  Base   - floor, lower wall, RP2040-Zero cradle, USB-C port, spigot + bayonet pins
  Top    - upper shell with the button hole, bayonet L-slots
  Plate  - retainer that pins onto the cradle and clamps the board down

Coordinates: Z up, origin at the bottom centre. USB-C exits toward +X.
All dimensions in mm. Edit the parameters below and re-run.
Tuned for PETG on a 0.6mm nozzle (looser fits, no sub-1.2mm features).
"""

import math
import os

import FreeCAD as App
import Part
from FreeCAD import Vector as V

# ---------------------------------------------------------------- parameters
ID = 54.0               # inner diameter of the body
WALL = 3.0              # wall thickness
OD = ID + 2 * WALL      # outer diameter of the grip
H_TOTAL = 70.0          # overall height (base + top)
SPLIT_Z = 20.0          # where top shell meets base
FLOOR = 3.0             # base floor thickness
TOP_PLATE = 3.0         # thickness of the panel the button goes through
TOP_FILLET = 3.0        # rounding of the top outer edge
BOTTOM_CHAMFER = 0.8    # bottom outer edge (also hides elephant's foot)

# Arcade button (Adafruit 3489-style 30mm screw-in; verify with calipers)
BTN_HOLE_D = 30.6       # panel hole; thread is M28
BTN_BEZEL_D = 33.3
BTN_BEZEL_T = 4.7
BTN_CAP_D = 22.65
BTN_CAP_H = 4.85
BTN_BODY_D = 28.0
BTN_DEPTH = 33.3        # below panel to terminal tips
NUT_AF = 36.0           # nut across flats (GUESS - not in any datasheet)
NUT_T = 6.0             # nut thickness (GUESS)

# Joint: spigot on the base slides inside the top shell; 2-pin bayonet
FIT = 0.25              # radial clearance for the spigot slip fit
SPIGOT_H = 8.0
SPIGOT_T = 2.0
PIN_D = 3.0
PIN_Z = SPLIT_Z + 4.0
PIN_PROTRUDE = 1.15     # beyond spigot OD
SLOT_CLEAR = 0.4        # radial clearance of pin in slot
SLOT_VCLEAR = 0.25      # vertical clearance above/below pin
TWIST_DEG = 30.0        # how far you twist to lock
DETENT_H = 0.5          # bump the pin clicks over (0 to disable)
PIN_ANGLES = (90.0, 270.0)

# Waveshare RP2040-Zero
PCB_L, PCB_W, PCB_T = 23.5, 18.0, 1.0
USB_OVERHANG = 1.21
USB_W, USB_L = 9.58, 7.35
USB_BELOW, USB_ABOVE = 0.91, 3.25  # shell extent relative to PCB top surface
BOARD_FIT = 0.25        # clearance around PCB in the cradle
BOARD_LIFT = 4.0        # PCB bottom height above floor (room for solder blobs)
WALL_GAP = 0.3          # min gap between PCB corners / USB face and inner wall
CRADLE_WALL = 2.0       # back wall
CRADLE_SIDE = 4.5       # side walls (hold the plate pins)
LEDGE_X = 1.3           # end ledges the PCB rests on
NOTCH_MARGIN = 0.5      # clearance each side of the spigot notch the board/plate drop through
LEDGE_PAD_GAP = 6.2     # |y| below which ledges are cut away (keeps pads clear)

# Retainer plate
PLATE_T = 2.5
PLATE_BRIDGE_X = 3.0    # width of the bar that presses on the USB shell
PLATE_PIN_D = 2.6
PLATE_PIN_L = 2.5
PLATE_HOLE_D = 2.95
PLATE_PIN_XS = (2.8, 17.8)   # measured from the PCB's far end

# USB-C cable opening
USB_POCKET_W = 13.5     # plug overmold clearance
USB_POCKET_H = 7.5
USB_POCKET_R = 2.0
USB_CHAMFER = 2.5       # chamfer depth at the outer surface (45 deg)

DOC_NAME = "MuteButton"
EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__))
                          if "__file__" in globals() else os.getcwd(), "stl")

# ---------------------------------------------------------------- derived
R = OD / 2
RI = R - WALL
PCB_BOT = FLOOR + BOARD_LIFT
# push the board as close to the wall as its corners and the USB shell allow
BOARD_END_X = min(math.sqrt((RI - WALL_GAP) ** 2 - (PCB_W / 2 + BOARD_FIT) ** 2) - BOARD_FIT,
                  RI - WALL_GAP - USB_OVERHANG)
PCB_TOP = PCB_BOT + PCB_T
USB_ZC = PCB_TOP + (USB_ABOVE - USB_BELOW) / 2
USB_FACE_X = BOARD_END_X + USB_OVERHANG
CRADLE_TOP = PCB_TOP + USB_ABOVE         # plate sits here, touching USB shell
BOARD_X0 = BOARD_END_X - PCB_L
POCKET_X0 = BOARD_X0 - BOARD_FIT
POCKET_X1 = BOARD_END_X + BOARD_FIT
POCKET_HW = PCB_W / 2 + BOARD_FIT
CRADLE_X0 = POCKET_X0 - CRADLE_WALL
CRADLE_HW = POCKET_HW + CRADLE_SIDE
PLATE_PIN_Y = POCKET_HW + CRADLE_SIDE / 2
USB_NOTCH_HW = CRADLE_HW + NOTCH_MARGIN
SPIGOT_RO = RI - FIT
SPIGOT_RI = SPIGOT_RO - SPIGOT_T


# ---------------------------------------------------------------- helpers
def cyl(r, h, z0=0.0, x=0.0, y=0.0, axis=V(0, 0, 1), angle=360.0):
    return Part.makeCylinder(r, h, V(x, y, z0), axis, angle)


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def rotz(shape, deg):
    s = shape.copy()
    s.rotate(V(0, 0, 0), V(0, 0, 1), deg)
    return s


def rrect_yz(x, w, h, r, zc):
    """Closed rounded-rectangle wire in the plane X=x, centred at (y=0, z=zc)."""
    hw, hh, s = w / 2, h / 2, math.sqrt(0.5)
    P = lambda y, z: V(x, y, z)
    corners = [  # (centre y, centre z, start dir, end dir) going CCW
        (hw - r, zc - hh + r, (0, -1), (1, 0)),
        (hw - r, zc + hh - r, (1, 0), (0, 1)),
        (-hw + r, zc + hh - r, (0, 1), (-1, 0)),
        (-hw + r, zc - hh + r, (-1, 0), (0, -1)),
    ]
    edges, prev_end = [], None
    for cy, cz, d0, d1 in corners:
        a = P(cy + r * d0[0], cz + r * d0[1])
        m = P(cy + r * s * (d0[0] + d1[0]), cz + r * s * (d0[1] + d1[1]))
        b = P(cy + r * d1[0], cz + r * d1[1])
        if prev_end is not None:
            edges.append(Part.LineSegment(prev_end, a).toShape())
        edges.append(Part.Arc(a, m, b).toShape())
        prev_end = b
    first = P(corners[0][0] + r * corners[0][2][0], corners[0][1] + r * corners[0][2][1])
    edges.append(Part.LineSegment(prev_end, first).toShape())
    return Part.Wire(Part.__sortEdges__(edges))


def circ_edges(shape, z, r, tol=0.05):
    out = []
    for e in shape.Edges:
        c = e.Curve
        if isinstance(c, Part.Circle) and abs(c.Radius - r) < tol \
                and abs(c.Center.z - z) < tol:
            out.append(e)
    return out


# ---------------------------------------------------------------- base
def make_base():
    body = cyl(R, SPLIT_Z)
    if BOTTOM_CHAMFER > 0:
        body = body.makeChamfer(BOTTOM_CHAMFER, circ_edges(body, 0, R))
    spigot = cyl(SPIGOT_RO, SPIGOT_H, SPLIT_Z)
    body = body.fuse(spigot)

    # interior: bore, 45deg transition to spigot ID, spigot bore
    trans = RI - SPIGOT_RI
    bore = cyl(RI, SPLIT_Z - trans - FLOOR, FLOOR)
    cone = Part.makeCone(RI, SPIGOT_RI, trans, V(0, 0, SPLIT_Z - trans))
    sbore = cyl(SPIGOT_RI, SPIGOT_H + trans + 1, SPLIT_Z - trans)
    body = body.cut(bore.fuse(cone).fuse(sbore))

    # notch the spigot (and the transition under it) above the board's USB end,
    # so the board can be lowered straight into the cradle past the spigot
    notch = box(0, R, -USB_NOTCH_HW, USB_NOTCH_HW,
                SPLIT_Z - trans - 0.5, SPLIT_Z + SPIGOT_H + 1).common(cyl(RI, 100, -1))
    body = body.cut(notch)

    # bayonet pins
    pin_r0 = SPIGOT_RI + 0.3
    for a in PIN_ANGLES:
        pin = cyl(PIN_D / 2, SPIGOT_RO + PIN_PROTRUDE - pin_r0, 0,
                  x=0, y=0, axis=V(1, 0, 0))
        pin.translate(V(pin_r0, 0, PIN_Z))
        body = body.fuse(rotz(pin, a))

    # board cradle
    cradle = box(CRADLE_X0, POCKET_X1, -CRADLE_HW, CRADLE_HW, FLOOR, CRADLE_TOP)
    cradle = cradle.common(cyl(RI + 0.5, CRADLE_TOP))
    pocket = box(POCKET_X0, POCKET_X1 + 5, -POCKET_HW, POCKET_HW, FLOOR, CRADLE_TOP + 1)
    cradle = cradle.cut(pocket)
    # end ledges the PCB rests on, cut away in the middle so solder/pads are clear
    for x0, x1 in ((POCKET_X0, POCKET_X0 + LEDGE_X), (POCKET_X1 - LEDGE_X, POCKET_X1)):
        for sgn in (1, -1):
            y0, y1 = sorted((sgn * LEDGE_PAD_GAP, sgn * POCKET_HW))
            cradle = cradle.fuse(box(x0, x1, y0, y1, FLOOR, PCB_BOT))
    for x in (BOARD_X0 + px for px in PLATE_PIN_XS):
        for y in (PLATE_PIN_Y, -PLATE_PIN_Y):
            cradle = cradle.cut(cyl(PLATE_HOLE_D / 2, 3.0, CRADLE_TOP - 3.0, x, y))
    body = body.fuse(cradle)

    # USB-C opening: straight pocket for the plug overmold + 45deg chamfer
    w_in = rrect_yz(USB_FACE_X - 0.5, USB_POCKET_W, USB_POCKET_H, USB_POCKET_R, USB_ZC)
    plug = Part.Face(w_in).extrude(V(R + 5 - (USB_FACE_X - 0.5), 0, 0))
    x_a, x_b = R - USB_CHAMFER, R + 3
    grow = 2 * (x_b - x_a)
    funnel = Part.makeLoft([
        rrect_yz(x_a, USB_POCKET_W, USB_POCKET_H, USB_POCKET_R, USB_ZC),
        rrect_yz(x_b, USB_POCKET_W + grow, USB_POCKET_H + grow,
                 USB_POCKET_R + grow / 2, USB_ZC),
    ], True)
    body = body.cut(plug.fuse(funnel))
    return body.removeSplitter()


# ---------------------------------------------------------------- top
def make_top():
    h = H_TOTAL - SPLIT_Z
    body = cyl(R, h, SPLIT_Z)
    if TOP_FILLET > 0:
        body = body.makeFillet(TOP_FILLET, circ_edges(body, H_TOTAL, R))
    body = body.cut(cyl(RI, h - TOP_PLATE, SPLIT_Z - 0.01))
    body = body.cut(cyl(BTN_HOLE_D / 2, TOP_PLATE + 2, H_TOTAL - TOP_PLATE - 1))

    # bayonet L-slots
    r_slot = SPIGOT_RO + PIN_PROTRUDE + SLOT_CLEAR
    z_lo = PIN_Z - PIN_D / 2 - SLOT_VCLEAR
    z_hi = PIN_Z + PIN_D / 2 + SLOT_VCLEAR
    half_w = PIN_D / 2 + 0.3
    half_deg = math.degrees(half_w / RI)
    for a in PIN_ANGLES:
        entry = box(RI - 0.5, r_slot, -half_w, half_w, SPLIT_Z - 0.1, z_hi)
        leg = cyl(r_slot, z_hi - z_lo, z_lo, angle=TWIST_DEG + half_deg)
        leg = rotz(leg.cut(cyl(RI - 0.5, z_hi - z_lo + 1, z_lo - 0.5)), -half_deg)
        body = body.cut(rotz(entry.fuse(leg), a))
        if DETENT_H > 0:
            br = 0.6
            bump = cyl(br, r_slot - RI + 0.2, 0, axis=V(1, 0, 0))
            bump.translate(V(RI - 0.1, 0, z_lo + DETENT_H - br))
            body = body.fuse(rotz(bump, a + TWIST_DEG * 0.6))
    return body.removeSplitter()


# ---------------------------------------------------------------- plate
def make_plate():
    p = box(CRADLE_X0, POCKET_X1 - 0.3, -CRADLE_HW, CRADLE_HW,
            CRADLE_TOP, CRADLE_TOP + PLATE_T)
    p = p.common(cyl(RI - 0.3, CRADLE_TOP + PLATE_T + 1))
    window_x1 = POCKET_X1 - 0.3 - PLATE_BRIDGE_X
    p = p.cut(box(POCKET_X0, window_x1, -POCKET_HW, POCKET_HW,
                  CRADLE_TOP - 1, CRADLE_TOP + PLATE_T + 1))
    for x in (BOARD_X0 + px for px in PLATE_PIN_XS):
        for y in (PLATE_PIN_Y, -PLATE_PIN_Y):
            p = p.fuse(cyl(PLATE_PIN_D / 2, PLATE_PIN_L, CRADLE_TOP - PLATE_PIN_L, x, y))
    return p.removeSplitter()


# ---------------------------------------------------------------- ghosts
def make_ghosts():
    zt = H_TOTAL
    btn = cyl(BTN_BEZEL_D / 2, BTN_BEZEL_T, zt)
    btn = btn.fuse(cyl(BTN_CAP_D / 2, BTN_CAP_H, zt + BTN_BEZEL_T))
    btn = btn.fuse(cyl(BTN_BODY_D / 2, BTN_DEPTH - 4.7, zt - BTN_DEPTH + 4.7))
    for y in (-2.8, 2.8):
        btn = btn.fuse(box(-1.4, 1.4, y - 0.25, y + 0.25, zt - BTN_DEPTH, zt - BTN_DEPTH + 4.7))
    nut = Part.makePolygon([V(NUT_AF / math.sqrt(3) * math.cos(math.radians(60 * i)),
                              NUT_AF / math.sqrt(3) * math.sin(math.radians(60 * i)), 0)
                            for i in range(7)])
    nut = Part.Face(nut).extrude(V(0, 0, NUT_T))
    nut = nut.cut(cyl(BTN_BODY_D / 2, NUT_T + 1, -0.5))
    nut.translate(V(0, 0, zt - TOP_PLATE - NUT_T))
    pcb = box(BOARD_X0, BOARD_END_X, -PCB_W / 2, PCB_W / 2, PCB_BOT, PCB_TOP)
    usb = box(USB_FACE_X - USB_L, USB_FACE_X, -USB_W / 2, USB_W / 2,
              PCB_TOP - USB_BELOW, PCB_TOP + USB_ABOVE)
    return {"Ghost_Button": btn, "Ghost_Nut": nut, "Ghost_Board": pcb.fuse(usb)}


# ---------------------------------------------------------------- build
def build():
    if DOC_NAME in App.listDocuments():
        doc = App.getDocument(DOC_NAME)
        for o in list(doc.Objects):
            doc.removeObject(o.Name)
    else:
        doc = App.newDocument(DOC_NAME)

    parts = {
        "Base": (make_base(), (0.30, 0.55, 0.85), 0),
        "Top": (make_top(), (0.85, 0.45, 0.20), 0),
        "Plate": (make_plate(), (0.30, 0.75, 0.35), 0),
    }
    for name, shp in make_ghosts().items():
        parts[name] = (shp, (0.6, 0.6, 0.6), 70)

    for name, (shp, color, transp) in parts.items():
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shp
        if App.GuiUp:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.Transparency = transp
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.ActiveDocument.ActiveView.viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    return doc


def export_stl(doc=None):
    import Mesh
    doc = doc or App.getDocument(DOC_NAME)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    for name in ("Base", "Top", "Plate"):
        shp = doc.getObject(name).Shape.copy()
        if name == "Top":   # print upside down: top face on the bed
            shp.rotate(V(0, 0, 0), V(1, 0, 0), 180)
        mesh = Mesh.Mesh(shp.tessellate(0.02))
        path = os.path.join(EXPORT_DIR, f"mutebutton_{name.lower()}.stl")
        mesh.write(path)
        print("wrote", path)


DOC = build()
for _n in ("Base", "Top", "Plate"):
    _s = DOC.getObject(_n).Shape
    print(f"{_n}: valid={_s.isValid()} solids={len(_s.Solids)} vol={_s.Volume:.0f}mm3")
