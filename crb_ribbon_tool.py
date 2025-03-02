import maya.cmds as cm
import maya.api.OpenMaya as OpenMaya

def parent_group(item):
    """Creates a parent group for the specified object."""
    group0 = cm.group(item, r=True, n=item + "_move")
    cm.copyAttr(item, group0, at="offsetParentMatrix", v=True)
    cm.setAttr(item + ".offsetParentMatrix", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, typ="matrix")

def offset_parent_matrix(*joints):
    for obj in joints:
         p = cmds.xform(obj, query=True, matrix=True)
         parent = cmds.getAttr(obj+".offsetParentMatrix")
         matrix_p = OpenMaya.MMatrix(p)
         offset_parent=OpenMaya.MMatrix(parent)
         result = matrix_p*offset_parent
         cmds.setAttr(obj + ".offsetParentMatrix", result, type="matrix")
         cmds.setAttr(obj+".translate", 0,0,0), cmds.setAttr(obj+".rotate", 0,0,0), cmds.setAttr(obj+".scale", 1,1,1), cmds.setAttr(obj+".shear", 0,0,0)
         if cmds.objectType(obj) == "joint":
             cmds.setAttr(obj+".jointOrient", 0,0,0)

def create_curve(ribbon_name):
    """Creates a deformation curve for the ribbon."""
    crv = cm.curve(p=[(-7.5, 0, 0), (-2.5, 0, 0), (0, 0, 0), (2.5, 0, 0), (7.5, 0, 0)], n="crv_" + ribbon_name + "deform")
    cm.rebuildCurve(crv, rt=0, s=1, d=2)
    return crv

def create_bindskin_joints(ribbon_name, number_of_joints):
    """Creates the bindskin joints and their connections."""
    cm.group(n="grp_bindskin_" + ribbon_name, em=True)
    for iter in range(int(number_of_joints)):
        joint_name = "bindskin_" + ribbon_name + "_" + str(iter)
        cm.joint(p=(0, 0, 0), n=joint_name)
        cm.createNode("pointOnCurveInfo", n="pointOnCurveInfo_" + ribbon_name + "_" + str(iter))
        cm.createNode("decomposeMatrix", n="dcmpMat_" + ribbon_name + str(iter))
        cm.setAttr("pointOnCurveInfo_" + ribbon_name + "_" + str(iter) + ".turnOnPercentage", 1)
        cm.setAttr("pointOnCurveInfo_" + ribbon_name + "_" + str(iter) + ".parameter", iter /(int(number_of_joints)-1))
        cm.shadingNode("fourByFourMatrix", n="by4_" + ribbon_name + str(iter), asUtility=True)
        cm.connectAttr("crv_" + ribbon_name + "deform.worldSpace", "pointOnCurveInfo_" + ribbon_name + "_" + str(iter) + ".inputCurve")
        cm.connectAttr("by4_" + ribbon_name + str(iter) + ".output", "dcmpMat_" + ribbon_name + str(iter) + ".inputMatrix")
        cm.connectAttr("dcmpMat_" + ribbon_name + str(iter) + ".outputTranslate", joint_name + ".translate")
        cm.connectAttr("dcmpMat_" + ribbon_name + str(iter) + ".outputRotate", joint_name + ".rotate")
        cm.connectAttr("pointOnCurveInfo_"+ribbon_name+"_"+str(iter)+".result.position.positionX","by4_"+ribbon_name+str(iter)+".in30")
        cm.connectAttr("pointOnCurveInfo_"+ribbon_name+"_"+str(iter)+".result.position.positionY","by4_"+ribbon_name+str(iter)+".in31")
        cm.connectAttr("pointOnCurveInfo_"+ribbon_name+"_"+str(iter)+".result.position.positionZ","by4_"+ribbon_name+str(iter)+".in32")
        cm.connectAttr("pointOnCurveInfo_"+ribbon_name+"_"+str(iter)+".result.normalizedTangent.normalizedTangentX","by4_"+ribbon_name+str(iter)+".in00")
        cm.connectAttr("pointOnCurveInfo_"+ribbon_name+"_"+str(iter)+".result.normalizedTangent.normalizedTangentY","by4_"+ribbon_name+str(iter)+".in01")
        cm.connectAttr("pointOnCurveInfo_"+ribbon_name+"_"+str(iter)+".result.normalizedTangent.normalizedTangentZ","by4_"+ribbon_name+str(iter)+".in02")
        if iter == 0:
            pass
        else:
            cm.parent(joint_name, "grp_bindskin_"+ribbon_name)

def create_driven_joints(ribbon_name):
    """Creates the driven joints."""
    cm.select(cl=True)
    cm.joint(p=(-7.5, 0, 0), n="drvjnt_" + ribbon_name + "_01")
    cm.select(cl=True)
    cm.joint(p=(0, 0, 0), n="drvjnt_" + ribbon_name + "_02")
    cm.select(cl=True)
    cm.joint(p=(7.5, 0, 0), n="drvjnt_" + ribbon_name + "_03")
    parent_group("drvjnt_" + ribbon_name + "_02")
    offset_parent_matrix("drvjnt_" + ribbon_name + "_01","drvjnt_" + ribbon_name + "_03")
    cm.skinCluster("drvjnt_" + ribbon_name + "_01", "drvjnt_" + ribbon_name + "_02", "drvjnt_" + ribbon_name + "_03", "crv_" + ribbon_name + "deform", tsb=True)

def create_controller(name, joint_name):
    """Creates a controller for a given joint."""
    cm.nurbsSquare(c=(0, 0, 0), nr=(0, 1, 0), sl1=1, sl2=1, sps=1, d=3, ch=1, n=name)
    cm.bakePartialHistory(name)
    cm.attachCurve("top" + name, "left" + name, "bottom" + name, "right" + name)
    cm.parent("top" + name, w=True)
    cm.bakePartialHistory("top" + name)
    cm.delete(name, "left" + name, "bottom" + name, "right" + name)
    cm.rename("top" + name, name)
    cm.matchTransform(name, joint_name)
    cm.setAttr(name + ".overrideEnabled", 1)
    cm.setAttr(name + ".overrideColor", 17)
    cm.scale(2, 1, 2)
    cm.refresh()
    cm.makeIdentity(name, apply=1, s=1, t=1, r=1)

def CrvRibbonTool(*args):
    """Creates a Ribbon tool using a curve, joints, and controllers."""
    ribbon_name = cm.textField("RibbonName", query=True, text=True)
    number_of_joints = cm.textField("numberOfJoints", query=True, text=True)

    # Input validation
    if not ribbon_name or not number_of_joints:
        cm.warning("Please fill in all fields.")
        return

    # Create the curve
    crv = create_curve(ribbon_name)

    # Create the bindskin joints
    create_bindskin_joints(ribbon_name, number_of_joints)

    # Create the driven joints
    create_driven_joints(ribbon_name)

    # Create the controllers
    create_controller("ctrl_" + ribbon_name + "_01", "drvjnt_" + ribbon_name + "_01")
    create_controller("ctrl_" + ribbon_name + "_02", "drvjnt_" + ribbon_name + "_02")
    create_controller("ctrl_" + ribbon_name + "_03", "drvjnt_" + ribbon_name + "_03")

    parent_group("ctrl_" + ribbon_name + "_02")

    # Controller connections
    cm.connectAttr("ctrl_" + ribbon_name + "_01.translate", "drvjnt_" + ribbon_name + "_01.translate")
    cm.connectAttr("ctrl_" + ribbon_name + "_02.translate", "drvjnt_" + ribbon_name + "_02.translate")
    cm.connectAttr("ctrl_" + ribbon_name + "_03.translate", "drvjnt_" + ribbon_name + "_03.translate")

    # Create the hierarchy
    cm.group("crv_" + ribbon_name + "deform", n="grp_curves_" + ribbon_name)
    cm.group("drvjnt_" + ribbon_name + "_01", "drvjnt_" + ribbon_name + "_02_move", "drvjnt_" + ribbon_name + "_03", n="grp_drv_jnts_" + ribbon_name)
    cm.group("ctrl_" + ribbon_name + "_01", "ctrl_" + ribbon_name + "_02_move", "ctrl_" + ribbon_name + "_03", n="grp_ctrl_" + ribbon_name)
    cm.group("grp_curves_" + ribbon_name, "grp_drv_jnts_" + ribbon_name, "grp_bindskin_" + ribbon_name, "grp_ctrl_" + ribbon_name, n=ribbon_name)

    # Parent constraints for movements
    cm.parentConstraint("drvjnt_" + ribbon_name + "_01", "drvjnt_" + ribbon_name + "_03", "drvjnt_" + ribbon_name + "_02_move")
    cm.parentConstraint("ctrl_" + ribbon_name + "_01", "ctrl_" + ribbon_name + "_03", "ctrl_" + ribbon_name + "_02_move")

    # Create the root controller
    cm.nurbsSquare(c=(0, 0, 0), nr=(0, 1, 0), sl1=1, sl2=1, sps=1, d=3, ch=1, n="ctrl_root_" + ribbon_name)
    cm.bakePartialHistory("ctrl_root_" + ribbon_name)
    cm.attachCurve("topctrl_root_" + ribbon_name, "leftctrl_root_" + ribbon_name, "bottomctrl_root_" + ribbon_name, "rightctrl_root_" + ribbon_name)
    cm.parent("topctrl_root_" + ribbon_name, w=True)
    cm.bakePartialHistory("topctrl_root_" + ribbon_name)
    cm.delete("ctrl_root_" + ribbon_name, "leftctrl_root_" + ribbon_name, "bottomctrl_root_" + ribbon_name, "rightctrl_root_" + ribbon_name)
    cm.rename("topctrl_root_" + ribbon_name, "ctrl_root_" + ribbon_name)
    cm.matchTransform("ctrl_root_" + ribbon_name, "drvjnt_" + ribbon_name + "_02")
    cm.setAttr("ctrl_root_" + ribbon_name + ".overrideEnabled", 1)
    cm.setAttr("ctrl_root_" + ribbon_name + ".overrideColor", 17)
    cm.scale(7, 1, 4)
    cm.bakePartialHistory("ctrl_root_" + ribbon_name)
    cm.refresh()
    cm.makeIdentity("ctrl_root_" + ribbon_name, apply=1, s=1, t=1, r=1)
    cm.parent("ctrl_root_" + ribbon_name, ribbon_name)
    cm.parent("grp_drv_jnts_" + ribbon_name, "grp_ctrl_" + ribbon_name, "ctrl_root_" + ribbon_name)

# User interface
RibbonWindowID = "RibbonWindow"
if cm.window(RibbonWindowID, exists=True):
    cm.deleteUI(RibbonWindowID)
cm.window(RibbonWindowID, t="Ribbon Tool Creator")
cm.columnLayout(columnAttach=('both', 10), rowSpacing=10, columnWidth=250)
cm.text(label='Name')
RibbonName = cm.textField("RibbonName")
cm.text(label='Number of skinned joints')
numberOfJoints = cm.textField("numberOfJoints")
cm.button(label="Create", command=CrvRibbonTool)
cm.button(label='Close', command=('cmds.deleteUI(\"' + RibbonWindowID + '\", window=True)'))
cm.showWindow(RibbonWindowID)
