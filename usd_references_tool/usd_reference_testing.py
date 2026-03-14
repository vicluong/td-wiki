from pxr import Usd, Tf, UsdUtils, Sdf
import maya.cmds as cmds
import mayaUsd.lib as mayaUsdLib
import mayaUsd.ufe as mayaUsdUfe
import os

def getFirstStage():
    for base_prim in cmds.ls(type = "mayaUsdProxyShapeBase"):
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()

        return stage

def getAllStages():
    stages = []

    for base_prim in cmds.ls(type = "mayaUsdProxyShapeBase"):
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()
        stages.append(stage)

    return stages

def getAllGeoPrimPaths():
    """Prints path of all Geo Prims
    """
    stage = getFirstStage()
        
    prim_paths = []
    for prim in stage.Traverse():
        if prim.IsA(Tf.Type.FindByName('UsdGeomMesh')):
            prim_paths.append(prim.GetPath())
            # print(prim.GetPath())
    return prim_paths 

def getFirstGeoPrim():
    stage = getFirstStage()
        
    for prim in stage.Traverse():
        if prim.IsA(Tf.Type.FindByName('UsdGeomMesh')):
            print(f"Prim: {prim}")
            print(f"Prim Path: {prim.GetPath()}")
            print(f"Info: {prim.GetPrimTypeInfo()}")
            return stage, prim

def getFirstGeoPrimReferences():
    # When getFirstGeoPrim() finishes, stage_ref goes out of scope and gets destroyed.
    # When the stage is destroyed, all prim handles from it become invalid.
    stage, prim = getFirstGeoPrim()
    print(f"Prim: {prim}")
    print(f"References: {prim.GetReferences()}")
    # prim_refs = prim.GetReferences().GetAddedItems()

    # print(prim_refs)

    prim_spec = stage.GetEditTarget().GetSpecForScenePath(prim.GetPath())
    print(prim_spec)

    # prim_refs.GetAssetPath()

# -----------------------------------------------------

def getInfo():
    print("-----------------------")
    for base_prim in cmds.ls(type="mayaUsdProxyShape"):
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()
        rootLayer = stage.GetRootLayer()

        print(f"mayaUsdProxyShape: {base_prim}")
        print(f"Long name: {cmds.ls(base_prim, long=True)[0]}")
        print(f"Stage: {stage}")
        print(f"RootLayer: {rootLayer}")
        print(f"Is Dirty: {rootLayer.dirty}")
    print("-----------------------")

# -----------------------------------------------------

def removePrim(prim_path):
    stage = getFirstStage()
    root = stage.GetRootLayer()
    stage.SetEditTarget(root)
    stage.RemovePrim(prim_path)

def removeAllPrims(prim_path_list):
    for prim in prim_path_list:
        removePrim(prim)

# -----------------------------------------------------

def activateAllPrims(activate=True):
    base_prims = cmds.ls(type = "mayaUsdProxyShapeBase")

    for base_prim in base_prims:
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()
        
        for prim in stage.Traverse():
            # if prim.IsA(Tf.Type.FindByName('UsdGeomMesh')):
            prim.SetActive(activate)

def getPrimAttributes():
    base_prims = cmds.ls(type = "mayaUsdProxyShapeBase")

    for base_prim in base_prims:
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()
        
        for prim in stage.Traverse():
            # if prim.IsA(Tf.Type.FindByName('UsdGeomMesh')):
            print(f"\nPrim: {prim}")
            print(f"Property Names: {prim.GetPropertyNames()}")

            for prim_prop in prim.GetPropertyNames():
                print(prim.GetAttribute(prim_prop))
                print(f"{prim_prop}: {prim.GetAttribute(prim_prop).Get()}")


        # if prim.HasAttribute('radius'):
        #     print(prim.GetAttribute('radius').Get())

def changeRadiusAttribute():
    stage = getFirstStage()
        
    for prim in stage.Traverse():
        print(f"\nPrim: {prim}")

        if prim.HasAttribute('radius'):
            rad_attr = prim.GetAttribute('radius')
            rad_attr.Set(3.0)
            # print(rad_attr.Get())

# -------------------------------------------------------------

def createEmptyPrim():
    empty_prim = Usd.Prim()
    print(empty_prim)
    print(empty_prim.IsValid())

def checkMissingPrim(path):
    stage = getFirstStage()

    prim = stage.GetPrimAtPath(path)

    print(prim)
    print(prim.IsValid())

def checkMissingPrimTotal():
    """
    Check any prims that are not valid
    """
    stage = getFirstStage()

    total_prim = 0
    non_valid = 0

    for prim in stage.Traverse():
        print(prim)
        if not prim.IsValid():
            non_valid += 1
        total_prim += 1

    print(non_valid)
    print(total_prim)

# -------------------------------------------------------------
    """It recognises that there is a missing path when using Usd.PrimCompositionQuery(prim)
    But how do I check it before the warning occurs?
    """

def checkCompositionArc(path):
    # stage = getFirstStage()

    # prim = stage.GetPrimAtPath(path)

    # # print(Usd.PrimCompositionQuery(prim))

    # comp_arc_query = Usd.PrimCompositionQuery(prim)
    # comp_arcs = comp_arc_query.GetCompositionArcs()
    # # print(comp_arc_query.GetDirectReferences())
    # # print(comp_arc_query[0])
    # # print(prim.GetReferences.GetDirectReferences())

    # for comp_arc in comp_arcs:
    #     print(comp_arc.GetArcType().name)
    #     print(comp_arc.GetArcType())
    #     print(comp_arc.GetAssetPath())
    stage = getFirstStage()

    # prim = stage.GetPrimAtPath(path)
    # query = Usd.PrimCompositionQuery(prim)
    # references = query.GetCompositionArcs()
    
    # print(f"References for prim: {prim.GetPath()}")
    # for arc in references:
    #     # Check if the arc is a reference type
    #     # if arc.GetArcType() == Sdf.CompositionArc.Reference:
    #         # Get the asset path as authored in the layer
    #     asset_path = arc.GetAssetPath()
        
    #     # Get the resolved asset path (the actual file path)
    #     resolved_path = arc.GetResolvedAssetPath()
        
    #     print(f"* Authored: {asset_path} -> Resolved: {resolved_path}")

        # Create a default resolver context for the asset
    # This ensures the asset resolver can find the dependencies correctly
    context = UsdUtils.CreateDefaultContextForAsset(stage)
    
    # Compute all dependencies recursively
    # The result includes references, sublayers, payloads, and other asset paths
    dependencies = UsdUtils.ComputeAssetDependencies(stage, context)
    
    print(f"Dependencies for stage: {stage}")
    # The 'dependencies' object contains various asset paths.
    # The key to inspect for this request are the general asset dependencies
    
    # Print the resolved paths (absolute paths to the files)
    print("Resolved Asset Paths:")
    for path in dependencies.resolvedAssetPaths:
        print(f"* {path}")
    
    # Print the authored asset paths (as they appear in the .usd file, could be relative)
    print("\nAuthored Asset Paths:")
    for path in dependencies.authoredAssetPaths:
        print(f"* {path}")

def checkAllCompositionArcs():
    stage = getFirstStage()

    for prim in stage.Traverse():
        comp_arc_query = Usd.PrimCompositionQuery(prim)
        comp_arcs = comp_arc_query.GetCompositionArcs()        
        print("-----------------------------------------------")
        for comp_arc in comp_arcs:
            print(prim)
            print(comp_arc.GetArcType().name)
            print(comp_arc.GetAssetPath())

# -------------------------------------------------------------

def getPrimReferences(prim_path):
    stage = getFirstStage()
    prim = stage.GetPrimAtPath(prim_path)

    print("----------SSSSS-------------")

    layer = stage.GetRootLayer()
    prim_spec = layer.GetPrimAtPath(prim.GetPath())

    print(prim_spec.referenceList)

    for ref in prim_spec.referenceList.GetAppliedItems():
        print("Asset path:", ref.assetPath)
        print("Prim path inside reference:", ref.primPath)

    print("----------SSSSS-------------")

    print(prim)
    print(prim.GetPath())

    print(type(prim_spec))

    print("References:", prim_spec.referenceList)
    print("References_2:", prim_spec.referenceList.GetAppliedItems())

    cwd = os.getcwd()
    print("Current path: " + cwd)

    print("----------SSSSS-------------")

    refs = prim.GetMetadata("references")

    for ref in refs.GetAppliedItems():
        print("Authored asset path:", ref.assetPath)

    print("---------------------------")

# getInfo()
# first_prim_path = getFirstGeoPrim()
# getFirstGeoPrimReferences()
# removePrim(first_prim_path)

# prim_path_list = getAllGeoPrimPaths()
# for prim_path in prim_path_list: 
#     print(prim_path)
# removeAllPrims(prim_path_list)

# prim_path_list = getAllGeoPrimPaths()
# activateAllPrims(True)

# changeRadiusAttribute()
# createEmptyPrim()

# checkMissingPrim("/Kitchen_set/Props_grp/DiningTable_grp/KitchenTable_1")
# checkMissingPrimTotal()
# checkCompositionArc("/Kitchen_set/Props_grp/DiningTable_grp/KitchenTable_1")
# checkAllCompositionArcs()

getPrimReferences("/Kitchen_set/Props_grp/DiningTable_grp/KitchenTable_1")
getPrimReferences("/Kitchen_set/Props_grp/DiningTable_grp/ChairB_1")
