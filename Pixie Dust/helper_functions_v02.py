from pathlib import Path

def create_asset_folders(main_folder_path: Path, asset_type: str, asset_name: str):
    asset_path = main_folder_path / "assets" / asset_type / asset_name
    asset_path.mkdir()

    asset_parts = []

    if asset_type == "camera":
        asset_parts = ["layout", "rig"]
    elif asset_type == "character":
        asset_parts = ["animation", "art", "charfx", "model", "rig", "surfacing"]
    elif asset_type == "charfx":
        asset_parts = ["charfx"]
    elif asset_type == "fx":
        asset_parts = ["art", "fx", "model", "rig", "surfacing"]
    elif asset_type == "prop":
        asset_parts = ["art", "model", "rig", "surfacing"]
    elif asset_type == "set":
        asset_parts = ["art", "model", "surfacing"]
    elif asset_type == "setPiece":
        asset_parts = ["art", "fx", "model", "surfacing"]

    for asset_part in asset_parts:
        asset_part_path = asset_path / asset_part
        asset_part_path.mkdir()
        publishes_path = asset_part_path / "publishes"
        publishes_path.mkdir()
        wip_path = asset_part_path / "wip"
        wip_path.mkdir()

def create_shot_folders(shot_path: Path):
    shot_path.mkdir()

    shot_assets_path = shot_path / "assets"
    shot_assets_path.mkdir()

    asset_types = ["audio", "camera", "character", "charfx", "fx", "lighting", "mattePainting", "production", "prop", "set", "setPiece", "vehicle"]
    for asset_type in asset_types:
        shot_asset_path = shot_assets_path / asset_type
        shot_asset_path.mkdir()

    shot_departments_path = shot_path / "departments"
    shot_departments_path.mkdir()

    departments = ["animation", "charfx", "comp", "editorial", "fx", "layout", "light"]
    for department in departments:
        shot_department_path = shot_departments_path / department
        shot_department_path.mkdir()
        publishes_path = shot_department_path / "publishes"
        publishes_path.mkdir()
        wip_path = shot_department_path / "wip"
        wip_path.mkdir()
