bl_info = {
    "name": "SL Helper",
    "author": "Reiikz",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "version": (1, 0, 0),
    "description": "It makes exporting in Second Life's special Snowflake formats easier",
    "dependencies": {
        "addons": ["io_scene_bvh"],
    },
}

import bpy
from bpy_extras.io_utils import ExportHelper
import os
import math

def strReplaceInFile(file_path, old_string, new_string):
    with open(file_path, 'r') as f:
        file_content = f.read()

    new_content = file_content.replace(old_string, new_string)

    with open(file_path, 'w') as f:
        f.write(new_content)


class ColladaExportOperator(bpy.types.Operator, ExportHelper):
    bl_label = "Snowflake SL collada"
    bl_idname = "export.sl_helper_export_collada"
    bl_description = "Exports all selected meshes in the selected object hirearchy in the Collada format using SecondLife specific settings"

    # Use the ExportHelper subclass to define the file path property
    filename_ext = ".dae"
    filter_glob: bpy.props.StringProperty(default="*.dae", options={'HIDDEN'})
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    # Define the options for the export
    # my_option: bpy.props.BoolProperty(name="My Option", default=False)
    
    def execute(self, context):
        
        targetPath = self.properties.filepath

        active_object = bpy.context.view_layer.objects.active

        # Traverse up the hierarchy to find the topmost parent
        while active_object.parent is not None:
            active_object = active_object.parent

        # Now active_object contains the highest parent in the hierarchy
        print("Highest parent object:", active_object.name)

        bpy.context.view_layer.objects.active = active_object

        bpy.ops.object.select_hierarchy(direction='CHILD', extend=True)

        print("Snowflake collada export for Second Life, Path:", f"{targetPath}")
        print()

        if os.path.isfile(targetPath):
            os.remove(targetPath)
        elif os.path.isdir(targetPath):
            self.report({'ERROR'}, f"The selected path is a directory {targetPath}")
            return {'CANCELLED'}

        bpy.ops.wm.collada_export(
            filepath=targetPath,
            use_object_instantiation=False,
            use_blender_profile=True,
            sort_by_name=True,
            keep_bind_info=True,
            limit_precision=False,
            include_animations=False,
            deform_bones_only=True,
            open_sim=True,
            triangulate=True,
            export_object_transformation_type_selection='matrix',
            selected=True,
            include_children=True,
            include_armatures=True,
            include_shapekeys=False,
            apply_global_orientation=True,
            export_global_forward_selection='Y',
            export_global_up_selection='Z',
            use_texture_copies=True,
            active_uv_only=True
        )
        
        return {'FINISHED'}




class BVHBulkExportOperator(bpy.types.Operator, ExportHelper):
    bl_label = "Bulk export BVH for SL"
    bl_description = "Exports all the animations in the scene on the BVH format with all of the Snowflake requirements to make it work PROPERLY in Second Life"
    bl_idname = "export.sl_helper_bulk_bvh"

    # Use the ExportHelper subclass to define the file path property
    filename_ext = ".bvh"
    filter_glob: bpy.props.StringProperty(default="*.bvh", options={'HIDDEN'})
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    # Define the options for the export
    # my_option: bpy.props.BoolProperty(name="My Option", default=False)

    def execute(self, context):

        userpath = self.properties.filepath
        if(not os.path.isdir(userpath)):
            userpath = os.path.dirname(userpath)
        print("BULK EXPORT (BVH)______>Export path:", userpath)
        print()

        scene = context.scene
        # Get all objects with animations
        objects = [ob for ob in scene.objects if ob.animation_data]
        
        actions = bpy.data.actions
        for obj in objects:

            animationDurations = f"list {obj.name}AnimationDurations = ["
            animationNames = f"list {obj.name}AnimationNames = ["
            
            print("---------->Exporting BVH animations For: ", obj.name)
            selectedAction = obj.animation_data.action
            for action in actions:
                animationNames += f" \"{action.name}\","
                obj.animation_data.action = action
                print("Exporting: ", action.name)
                print("Start to finish: ", action.curve_frame_range)
                targetPath = userpath + f"/{obj.name}/{action.name}.bvh"
                print("Target: ", targetPath)
                print()

                if os.path.isfile(targetPath):
                    os.remove(targetPath)
                elif os.path.isdir(targetPath):
                    shutil.rmtree(targetPath)

                if not os.path.exists(os.path.dirname(targetPath)):
                    os.makedirs(os.path.dirname(targetPath))

                bpy.ops.export_anim.bvh(
                    filepath=targetPath,
                    check_existing=False,
                    filter_glob="*.bvh",
                    root_transform_only=True,
                    frame_start=int(action.curve_frame_range[0]),
                    frame_end=int(action.curve_frame_range[1]),
                    rotate_mode='NATIVE',
                    global_scale=1.0,
                )

                strReplaceInFile(targetPath, "Xrotation Yrotation Zrotation", "Zrotation Xrotation Yrotation")
                print("Patched: ", targetPath)
                print()
                
                frameCount = ((action.curve_frame_range[1]) - ((action.curve_frame_range[0]) - 1))
                duration = frameCount / bpy.context.scene.render.fps
                duration = math.ceil(duration * 100) / 100
                animationDurations += " " + str(duration) + ","

            animationDurations = animationDurations[:-1] + " ];"
            animationNames = animationNames[:-1] + " ];"

            lslScript=f"{animationDurations}\n{animationNames}\n"
            lslScript += "float getAnimationDuration(string name){ integer index = llListFindList(" + obj.name + "AnimationNames, (list)name); return llList2Float(" + obj.name + "AnimationDurations, index); }"
            print(lslScript)
            
            with open(f"{userpath}/{obj.name}.lsl", 'w') as file:
                file.write(lslScript)

            obj.animation_data.action = selectedAction

        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(BVHBulkExportOperator.bl_idname, text=BVHBulkExportOperator.bl_label, text_ctxt=BVHBulkExportOperator.bl_description)
    self.layout.operator(ColladaExportOperator.bl_idname, text=ColladaExportOperator.bl_label, text_ctxt=ColladaExportOperator.bl_description)

def register():
    bpy.utils.register_class(BVHBulkExportOperator)
    bpy.utils.register_class(ColladaExportOperator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(BVHBulkExportOperator)
    bpy.utils.unregister_class(ColladaExportOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()