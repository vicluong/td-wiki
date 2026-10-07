"""
Auto Material Builder for Maya + Arnold
========================================

Point it at a folder of textures and it will:
  - Scan the folder for texture files
  - Match them against a naming convention (BaseColor, Roughness,
    Metalness, Normal, Height/Displacement, Emission, Opacity, AO,
    Specular, Coat, SSS, ...)
  - Create ONE aiStandardSurface (+ shading group)
  - Create a file node per matched texture and connect it to the
    correct attribute
  - Set the correct color space per map (sRGB for color data,
    Raw for non-color/data maps)
  - Route normal maps through aiNormalMap, bump maps through bump2d
  - Route height/displacement maps to the shading group's
    displacement slot via a displacementShader
  - Multiply an AO map into base color if one is found
  - Detect UDIM tile sequences (e.g. tex_1001.png, tex_1002.png)
    and set the file node to tiled mode instead of making one
    node per tile


NAMING CONVENTION
------------------
Files should contain a keyword somewhere in the name, separated by
underscore/dash/dot from the rest, e.g.:

    Rock_BaseColor.png     Rock_Roughness.png     Rock_Normal.png
    Rock_Metallic.png      Rock_Height.png        Rock_AO.png
    Rock_Emissive.png      Rock_Opacity.png

Matching is case-insensitive and covers common synonyms (see
TEXTURE_RULES below) including Substance Painter's default Arnold
export naming and generic alternatives (Albedo/Diffuse, Metallic/
Metalness, Displacement/Height, etc).

MAYA SCRIPT
------------------
from pathlib import Path
import sys

code_dir = Path("/path/to/code/dir")

if str(code_dir) not in sys.path:
    sys.path.append(str(code_dir))


import auto_material_builder as amb

amb.show_ui()


"""

import os
import re
import maya.cmds as cmds
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".tx", ".exr", ".hdr", ".bmp", ".tga"
}

# key -> (list of regex patterns to match against the texture's
#         descriptor token, is_color_data)
# Order matters: more specific patterns are listed before generic ones.
TEXTURE_RULES = [
    ("baseColor",         [r"base_?colou?r", r"albedo", r"diffuse", r"^colou?r$", r"_col$", r"_diff(use)?$"], True),
    ("specularColor",     [r"spec(ular)?_?colou?r"], True),
    ("specular",          [r"spec(ular)?(?!.*colou?r)"], False),
    ("metalness",         [r"metal(ness|lic)?"], False),
    #specularRoughness is standard roughness
    ("specularRoughness", [r"rough(ness)?"], False),
    ("coatRoughness",     [r"coat_?rough(ness)?"], False),
    ("coat",              [r"clear_?coat", r"(?<!coat_)\bcoat\b"], False),
    ("normal",            [r"normal(_?gl|_?dx|_?ogl)?", r"_nrm$", r"_nor$", r"^nmap$"], False),
    ("bump",              [r"bump(_?map)?"], False),
    ("height",            [r"height", r"displace(ment)?", r"_disp$"], False),
    ("emission",          [r"emiss(ive|ion)"], True),
    ("opacity",           [r"opacity", r"alpha", r"transparency"], False),
    ("sss",               [r"\bsss\b", r"subsurface"], True),
    ("ao",                [r"\bao\b", r"ambient_?occlusion", r"occlusion"], False),
]

# Data maps (non-color) get colorSpace "Raw" and alphaIsLuminance=1
# so we can pull a clean scalar out of .outAlpha.
COLOR_SPACE_RAW = "Raw"
COLOR_SPACE_SRGB = "sRGB"

# Need more research into how accurate this UDIM representation is
UDIM_RE = re.compile(r"(?<![0-9])([1-9][0-9]{3})(?![0-9])")


# ---------------------------------------------------------------------------
# Texture discovery
# ---------------------------------------------------------------------------

def scan_folder(folder):
    """Return list of dicts: {path, template, is_udim, tokens} for each
    distinct texture (UDIM tiles collapsed into a single templated entry)."""
    if not os.path.isdir(folder):
        raise RuntimeError("Not a valid folder: %s" % folder)

    files = [f for f in os.listdir(folder)
             if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]

    groups = {}  # key -> {"paths": [...], "template": str, "is_udim": bool}
    for file in files:
        full = os.path.join(folder, file)
        name, ext = os.path.splitext(file)
        m = UDIM_RE.search(name)
        if m:
            key = name[:m.start()] + "<UDIM>" + name[m.end():] + ext
            templ = os.path.join(folder, key)
            groups.setdefault(key, {"paths": [], "template": templ, "is_udim": True})
            groups[key]["paths"].append(full)
        else:
            key = file
            groups.setdefault(key, {"paths": [], "template": full, "is_udim": False})
            groups[key]["paths"].append(full)

    result = []
    for key, data in groups.items():
        descriptor = re.sub(r"<UDIM>", "", key)
        descriptor = os.path.splitext(descriptor)[0]
        result.append({
            "template": data["template"],
            "is_udim": data["is_udim"] and len(data["paths"]) > 1,
            "sample_path": data["paths"][0],
            "descriptor": descriptor,
        })
    return result

def classify(descriptor):
    """Return matched attribute key (or None) for a filename descriptor."""
    tokens = re.split(r"[ _\-.]+", descriptor.lower())
    joined = "_".join(tokens)
    for key, patterns, _is_color in TEXTURE_RULES:
        for pat in patterns:
            for tok in tokens:
                if re.search(pat, tok):
                    return key
            if re.search(pat, joined):
                return key
    return None

def is_color_map(key):
    for rule_key, _patterns, is_color in TEXTURE_RULES:
        if rule_key == key:
            return is_color
    return False

# ---------------------------------------------------------------------------
# Shader building
# ---------------------------------------------------------------------------

def make_file_node(name_base, path, is_udim, color_data, log):
    file_node = cmds.shadingNode("file", asTexture=True, isColorManaged=True,
                                  name=name_base + "_file")
    p2d = cmds.shadingNode("place2dTexture", asUtility=True,
                            name=name_base + "_p2d")
    for src, dst in [
        ("coverage", "coverage"), ("translateFrame", "translateFrame"),
        ("rotateFrame", "rotateFrame"), ("mirrorU", "mirrorU"),
        ("mirrorV", "mirrorV"), ("stagger", "stagger"), ("wrapU", "wrapU"),
        ("wrapV", "wrapV"), ("repeatUV", "repeatUV"), ("offset", "offset"),
        ("rotateUV", "rotateUV"), ("noiseUV", "noiseUV"),
        ("vertexUvOne", "vertexUvOne"), ("vertexUvTwo", "vertexUvTwo"),
        ("vertexUvThree", "vertexUvThree"), ("vertexCameraOne", "vertexCameraOne"),
        ("outUV", "uvCoord"), ("outUvFilterSize", "uvFilterSize"),
    ]:
        cmds.connectAttr(p2d + "." + src, file_node + "." + dst, force=True)

    cmds.setAttr(file_node + ".fileTextureName", path, type="string")
    if is_udim:
        cmds.setAttr(file_node + ".uvTilingMode", 3)
    cmds.setAttr(file_node + ".colorSpace",
                 COLOR_SPACE_SRGB if color_data else COLOR_SPACE_RAW,
                 type="string")
    if not color_data:
        cmds.setAttr(file_node + ".alphaIsLuminance", 1)

    log.append("  file node: %s  (%s, %s)" % (
        file_node, "UDIM" if is_udim else "single",
        "sRGB" if color_data else "Raw"))
    return file_node


def build_material(folder, mat_name, assign_to_selection, log):
    textures = scan_folder(folder)
    if not textures:
        raise RuntimeError("No texture files found in: %s" % folder)

    matched = {}   # key -> texture dict
    unmatched = []
    for tex in textures:
        key = classify(tex["descriptor"])
        if key is None:
            unmatched.append(tex["descriptor"])
            continue
        if key in matched:
            log.append("  WARNING: multiple files matched '%s' - keeping first (%s), "
                        "ignoring %s" % (key, matched[key]["descriptor"], tex["descriptor"]))
            continue
        matched[key] = tex

    if not matched:
        raise RuntimeError("Found %d texture(s) but none matched a known naming "
                            "pattern." % len(textures))

    log.append("Matched maps: %s" % ", ".join(sorted(matched.keys())))
    if unmatched:
        log.append("Unmatched files (skipped): %s" % ", ".join(unmatched))

    # --- shader + shading group -------------------------------------------------
    shader = cmds.shadingNode("aiStandardSurface", asShader=True, name=mat_name)
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True,
                   name=mat_name + "SG")
    cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", force=True)
    log.append("Created shader: %s  /  shading group: %s" % (shader, sg))

    base_color_file = None
    ao_file = None

    for key, tex in matched.items():
        color_data = is_color_map(key)
        node_base = mat_name + "_" + key
        f = make_file_node(node_base, tex["template"], tex["is_udim"], color_data, log)

        if key == "baseColor":
            base_color_file = f
            cmds.connectAttr(f + ".outColor", shader + ".baseColor", force=True)

        elif key == "specularColor":
            cmds.connectAttr(f + ".outColor", shader + ".specularColor", force=True)

        elif key in (
            "specular",
            "metalness",
            "specularRoughness",
            "coat",
            "coatRoughness"
        ):
            cmds.connectAttr(f + ".outAlpha", shader + f".{key}", force=True)

        elif key == "normal":
            normal_node = cmds.shadingNode("aiNormalMap", asUtility=True,
                                            name=mat_name + "_normalMap")
            cmds.connectAttr(f + ".outColor", normal_node + ".input", force=True)
            cmds.connectAttr(normal_node + ".outValue", shader + ".normalCamera", force=True)
            log.append("  routed through aiNormalMap: %s" % normal_node)

        elif key == "bump":
            # only used if there's no normal map already driving normalCamera
            if not cmds.listConnections(shader + ".normalCamera", source=True):
                bump_node = cmds.shadingNode("bump2d", asUtility=True,
                                              name=mat_name + "_bump2d")
                cmds.setAttr(bump_node + ".bumpInterp", 0)
                cmds.connectAttr(f + ".outAlpha", bump_node + ".bumpValue", force=True)
                cmds.connectAttr(bump_node + ".outNormal", shader + ".normalCamera", force=True)
                log.append("  routed through bump2d: %s" % bump_node)
            else:
                log.append("  skipped bump map: normalCamera already driven by a normal map")

        elif key == "height":
            disp_node = cmds.shadingNode("displacementShader", asShader=True,
                                          name=mat_name + "_dispShader")
            cmds.connectAttr(f + ".outAlpha", disp_node + ".displacement", force=True)
            cmds.connectAttr(disp_node + ".displacement", sg + ".displacementShader", force=True)
            log.append("  routed through displacementShader: %s" % disp_node)

        elif key == "emission":
            cmds.connectAttr(f + ".outColor", shader + ".emissionColor", force=True)
            cmds.setAttr(shader + ".emission", 1)

        elif key == "opacity":
            cmds.connectAttr(f + ".outColor", shader + ".opacity", force=True)

        elif key == "sss":
            cmds.connectAttr(f + ".outColor", shader + ".subsurfaceColor", force=True)
            cmds.setAttr(shader + ".subsurface", 1)

        elif key == "ao":
            ao_file = f  # handled after the loop, needs base_color_file

    if ao_file is not None:
        if base_color_file is not None:
            mult = cmds.shadingNode("multiplyDivide", asUtility=True,
                                     name=mat_name + "_ao_mult")
            cmds.setAttr(mult + ".operation", 1)  # multiply
            cmds.connectAttr(base_color_file + ".outColor", mult + ".input1", force=True)
            cmds.connectAttr(ao_file + ".outColor", mult + ".input2", force=True)
            cmds.connectAttr(mult + ".output", shader + ".baseColor", force=True)
            log.append("  multiplied AO into baseColor via: %s" % mult)
        else:
            log.append("  WARNING: AO map found but no baseColor map to multiply it into; "
                        "left AO file node unconnected (%s)" % ao_file)

    if assign_to_selection:
        sel = cmds.ls(selection=True, long=True)
        if sel:
            cmds.sets(sel, edit=True, forceElement=sg)
            log.append("Assigned %s to: %s" % (sg, ", ".join(sel)))
        else:
            log.append("Assign-to-selection was checked but nothing is selected.")

    return shader, sg

# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    return None


class AutoMaterialBuilderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AutoMaterialBuilderDialog, self).__init__(parent or maya_main_window())
        self.setObjectName("autoMaterialBuilderDialog")
        self.setWindowTitle("Auto Material Builder")
        self.setMinimumWidth(460)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

        self._build_ui()
        self._connect_signals()

    # -- UI construction ------------------------------------------------

    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Folder row
        main_layout.addWidget(QtWidgets.QLabel("Texture folder:"))
        folder_row = QtWidgets.QHBoxLayout()
        self.folder_field = QtWidgets.QLineEdit()
        self.browse_btn = QtWidgets.QPushButton("Browse...")
        folder_row.addWidget(self.folder_field)
        folder_row.addWidget(self.browse_btn)
        main_layout.addLayout(folder_row)

        # Material name
        main_layout.addWidget(QtWidgets.QLabel("Material name:"))
        self.name_field = QtWidgets.QLineEdit()
        main_layout.addWidget(self.name_field)

        # Assign checkbox
        self.assign_checkbox = QtWidgets.QCheckBox("Assign to selected objects")
        main_layout.addWidget(self.assign_checkbox)

        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)

        # Build button
        self.build_btn = QtWidgets.QPushButton("Build Material")
        self.build_btn.setMinimumHeight(34)
        main_layout.addWidget(self.build_btn)

        # Log
        main_layout.addWidget(QtWidgets.QLabel("Log:"))
        self.log_field = QtWidgets.QTextEdit()
        self.log_field.setReadOnly(True)
        self.log_field.setMinimumHeight(220)
        main_layout.addWidget(self.log_field)
        # self.log_field.setVisible(False)

    def _connect_signals(self):
        self.browse_btn.clicked.connect(self.browse_folder)
        self.build_btn.clicked.connect(self.do_build)

    # -- Slots ------------------------------------------------------------

    def browse_folder(self):
        result = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Texture Folder", self.folder_field.text() or os.path.expanduser("~")
        )
        if result:
            self.folder_field.setText(result)
            if not self.name_field.text().strip():
                base = os.path.basename(os.path.normpath(result))
                self.name_field.setText(base + "_MAT")

    def do_build(self):
        folder = self.folder_field.text().strip()
        mat_name = self.name_field.text().strip()
        assign_sel = self.assign_checkbox.isChecked()

        self.log_field.clear()
        log = []

        if not folder:
            self.log_field.setPlainText("Please choose a folder.")
            return
        if not mat_name:
            mat_name = "autoMaterial"

        orig = mat_name
        i = 1
        while cmds.objExists(mat_name) or cmds.objExists(mat_name + "SG"):
            mat_name = "%s_%d" % (orig, i)
            i += 1

        try:
            shader, sg = build_material(folder, mat_name, assign_sel, log)
            log.append("")
            log.append("DONE. Shader: %s   Shading group: %s" % (shader, sg))
        except Exception as exc:
            log.append("ERROR: %s" % str(exc))

        self.log_field.setPlainText("\n".join(log))

def show_ui():
    global _auto_material_builder_dialog
    try:
        _auto_material_builder_dialog.close()
        _auto_material_builder_dialog.deleteLater()
    except NameError:
        pass
    except RuntimeError:
        pass

    _auto_material_builder_dialog = AutoMaterialBuilderDialog()
    _auto_material_builder_dialog.show()
