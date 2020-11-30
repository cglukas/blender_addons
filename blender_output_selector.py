bl_info = {
    "name": "Multiple Render Outputs",
    "author": "Lukas Wieg",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Output Properties > Render Outputs",
    "description": "Adds presets for quick rendering of differend Cameras",
    "warning": "",
    "doc_url": "",
    "category": "Render",
}


import bpy

# File Selector
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

class RenderOutputSettings(bpy.types.PropertyGroup):
    """Global output settings"""
    file_path: bpy.props.StringProperty(name="Output Folder",
                                        description="Export location",
                                        default="//",
                                        maxlen=1024,
                                        subtype="FILE_PATH")                                   


class OutputSettings(bpy.types.PropertyGroup):
    """Output specific settings"""
    
    def scene_outputcamera_poll(self, object):
        return object.type == 'CAMERA'
    
    id: bpy.props.IntProperty()
    camera: bpy.props.PointerProperty(type=bpy.types.Object,
                                    poll=scene_outputcamera_poll,
                                    name="Camera Override")
    viewport: bpy.props.BoolProperty(name="OpenGL Render")
    file_name: bpy.props.StringProperty(name="Filename")
    
    
class RenderOutputPanel(bpy.types.Panel):
    """Creates a Panel in the output properties window"""
    
    bl_label = "Render Outputs"
    bl_idname = "OUTPUT_PT_RenderOutputPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout

        row = layout.row()        
        ros = context.scene.render_output_settings
        row.prop(ros, "file_path")
        
        row = layout.row()
        row.operator("render_output.add", icon="PLUS")
        
        for item in context.scene.render_outputs:
            layout.row().separator()
            row = layout.row()      
            row.label(text="Output {}:".format(item.id), icon="FILE_MOVIE") 
            row = layout.row()
            row.prop(item, "file_name", icon="FILE")      
            row = layout.row()            
            row.prop(item, "camera", icon="CAMERA_DATA")
            row = layout.row()
            row.prop(item, "viewport")            
            row = layout.row()
            row.operator("render_output.render", 
                         text="Render Output", icon="RENDER_ANIMATION").id = item.id
            row.operator("render_output.remove",
                         text="Remove Output", icon="CANCEL").id = item.id
                         
        
class AddOutput(bpy.types.Operator):
    """Adds an output to the render_outputs collection"""
    bl_idname = "render_output.add"
    bl_label = "Add Output"
    
    def execute(self, context):
        id = len(context.scene.render_outputs)
        new = context.scene.render_outputs.add()
        new.name = str(id)
        new.id = id
        new.file_name="render_" + str(id)        
        return {'FINISHED'}

class RemoveOutput(bpy.types.Operator):
    """Remove an output from the render_outputs collection"""
    bl_idname = "render_output.remove"
    bl_label = "Remove Output"
    
    id: bpy.props.IntProperty()
    
    def execute(self, context):
        for x, item in enumerate(context.scene.render_outputs):
            if item.id is self.id:
                context.scene.render_outputs.remove(x)
        return {'FINISHED'}
    
class RenderOutput(bpy.types.Operator):
    """Starts the rendering of an output"""
    bl_idname = "render_output.render"
    bl_label = "Render Output "
    
    id: bpy.props.IntProperty()
    
    def execute(self, context):
        print("Pressed Button ", self.id)
        render_settings = None
        
        for item in context.scene.render_outputs:
            if item.id is self.id:
                render_settings = item
        
        if not render_settings:
            return {'CANCELLED'}
        
        #Set camera
        camera_tmp = context.scene.camera
        if render_settings.camera is not None:      
            print("NOT NONE")      
            context.scene.camera = render_settings.camera
        
        #Combine output path
        output_path = context.scene.render_output_settings.file_path
        if not(output_path.endswith("/") or output_path.endswith("\\")):
            output_path += "/"        
        output_path += "{0}\\{0}_".format(render_settings.file_name)
        def fuck(dummy):
            print("fuck")
            
        bpy.app.handlers.render_pre.append(fuck)
        
        
        #Set output path
        context.scene.render.filepath = output_path
        
        #Start render
        if render_settings.viewport:
            area = bpy.context.area
            areatype = bpy.context.area.type
            if render_settings.camera is not None:                
                bpy.context.area.type = "VIEW_3D"
                bpy.ops.view3d.view_axis()
                bpy.ops.view3d.view_camera()
            
            bpy.ops.render.opengl('INVOKE_DEFAULT', animation=True)
            area.type = areatype
  
        else:
            bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
        
        def reset_camera(dummy):
            context.scene.camera = camera_tmp
            
            
            
        bpy.app.handlers.render_complete.append(reset_camera)
        bpy.app.handlers.render_cancel.append(reset_camera)
        return {'FINISHED'}
   


classes = (RenderOutputPanel,
           RenderOutputSettings,
           OutputSettings,
           AddOutput,
           RemoveOutput,
           RenderOutput) 
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls) 
        
    bpy.types.Scene.render_outputs = bpy.props.CollectionProperty(type=OutputSettings)
    bpy.types.Scene.render_output_settings = bpy.props.PointerProperty(type=RenderOutputSettings)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls) 
    del bpy.types.Scene.render_output_settings
    del bpy.types.Scene.render_outputs
    del bpy.types.Scene.area

if __name__ == "__main__":
    register()
