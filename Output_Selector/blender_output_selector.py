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
import glob

# File Selector
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

class RenderOutputSettings(bpy.types.PropertyGroup):
    """Global output settings"""
    file_path: bpy.props.StringProperty(name="Output Folder",
                                        description="Export location",
                                        default="//render/",
                                        maxlen=1024,
                                        subtype="FILE_PATH")                                   
    include_version: bpy.props.BoolProperty(default=True,
                                        description="Include the version number in subfolder names")
    
class OutputSettings(bpy.types.PropertyGroup):
    """Output specific settings"""
    
    def scene_outputcamera_poll(self, object):
        return object.type == 'CAMERA'
    
    id: bpy.props.IntProperty()
    camera: bpy.props.PointerProperty(type=bpy.types.Object,
                                    poll=scene_outputcamera_poll,
                                    name="Override Camera")
    version: bpy.props.IntProperty(name='Version',
                                    default=0)
    file_name: bpy.props.StringProperty(name="Filename")
    render_engine: bpy.props.EnumProperty(name="Override Engine",
                                        description="Override Render Engine",
                                        items={
                                        ('NONE', 'None', 'Don´t override engine', 0),
                                        ('BLENDER_WORKBENCH', 'Workbench', 'Render with workbench', 1),
                                        ('BLENDER_EEVEE', 'Eevee', 'Render with eevee', 2),
                                        ('CYCLES', 'Cylces', 'Render with cycles', 3),
                                        ('OPEN_GL', 'Open Gl', 'Render the viewport', 4)},
                                        default='NONE')
    custom_range: bpy.props.BoolProperty(name='Custom Range')
    in_point: bpy.props.IntProperty(name='In')
    out_point: bpy.props.IntProperty(name='Out')
    
    #filetype: bpy.props.CollectionProperty(type=bpy.types.ImageFormatSettings.bl_rna)
    
    
class RenderOutputPanel(bpy.types.Panel):
    """Creates a Panel in the output properties window"""
    
    bl_label = "Render Outputs"
    bl_idname = "OUTPUT_PT_RenderOutputPanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    def draw(self, context):
        layout = self.layout
        
        #Main output folder
        split = layout.split(factor=0.4)
        col1 = split.column()
        col2 = split.column()
        
        ros = context.scene.render_output_settings
        
        col1.label(text="Main Folder")
        col2.prop(ros, "file_path", text='')
        col1.label(text="Version in Subfolders")
        col2.prop(ros, 'include_version', text="")
        
        row = layout.row()
        row.operator("render_output.add", icon="PLUS")
        
        #Individual outputs
        for item in context.scene.render_outputs:
            #Spacer
            layout.row().separator()
            #Header
            row = layout.row()      
            row.label(text="Output {}:".format(item.id), icon="FILE_MOVIE") 
            #Filename
            row = layout.row()
            split = row.split(factor=0.25)  
            labels = split.column()    
            props = split.column() 
            labels.label(text="File Name:")
            s = props.split(factor=0.6)
            r1 = s.column()
            r2 = s.column()
            r1.prop(item, "file_name", text='', icon="FILE")  
            r2.prop(item, "version")    
            
            #Camera override      
            labels.label(text='Override Camera')  
            props.prop(item, "camera", icon="CAMERA_DATA", text='')  
                        
            #Render engine override
            labels.label(text='Override Engine')
            props.prop(item, "render_engine", icon='SHADING_RENDERED', text='')
            
            #In and out
            labels.prop(item, "custom_range")
            r = props.row()
            r.prop(item, "in_point")
            r.prop(item, "out_point")
            
            #Operators
            split = layout.split(factor=0.75)
            c1 = split.column()
            c2 = split.column()
            c1.operator("render_output.render", 
                         text="Render Output", icon="RENDER_ANIMATION").id = item.id
            c2.operator("render_output.remove",
                         text="Remove", icon="CANCEL").id = item.id
            #image_settings = context.scene.render.image_settings
            #layout.template_image_settings(image_settings, color_management=False) 
                         
        
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
    bl_label = "Override existing files?"
    
    id: bpy.props.IntProperty()
    
    def combine_path(self, context=bpy.context):        
        scene = context.scene
        
        render_settings = None        
        for item in scene.render_outputs:
            if item.id is self.id:
                render_settings = item
                
        output_path = scene.render_output_settings.file_path
        if not(output_path.endswith("/") or output_path.endswith("\\")):
            output_path += "/"  
        version = ""
        if render_settings.version > 0:
            version = "_v{0:03d}".format(render_settings.version)
        filename = render_settings.file_name
        filename_with_version = filename + version
        if scene.render_output_settings.include_version:
            output_path += "{0}\\{0}_".format(filename_with_version)
        else:
            output_path += "{0}\\{1}_".format(filename, filename_with_version)     
        
        return output_path 
    
    def invoke(self, context, event):
        #Check if files exists                
        files = glob.glob(bpy.path.abspath(self.combine_path(context)) + "*")
        if len(files)> 0:
            #Override existing files?        
            return context.window_manager.invoke_confirm(self, event)
        return self.execute(context)
        
        
    def execute(self, context):        
        scene = context.scene
        render_settings = None
        
        for item in scene.render_outputs:
            if item.id is self.id:
                render_settings = item
        
        if not render_settings:
            return {'CANCELLED'}
        #Safe current settings
        camera_tmp = scene.camera
        output_path_tmp = scene.render.filepath      
        render_engine_tmp = scene.render.engine
        in_tmp = scene.frame_start
        out_tmp = scene.frame_end 
        
        def reset_settings(dummy):
            scene.camera = camera_tmp
            scene.render.filepath = output_path_tmp
            scene.render.engine = render_engine_tmp
            scene.frame_start = in_tmp
            scene.frame_end = out_tmp
            bpy.app.handlers.render_complete.remove(reset_settings)
            bpy.app.handlers.render_cancel.remove(reset_settings)
        #Set camera
        if render_settings.camera is not None:      
            print("NOT NONE")      
            scene.camera = render_settings.camera
        
        #Set output path
        scene.render.filepath = self.combine_path(context)
        
        #Override render engine
        open_gl = False
        if render_settings.render_engine == 'OPEN_GL':
            open_gl = True
        elif render_settings.render_engine != 'NONE':
            scene.render.engine = render_settings.render_engine
        #Override in and out
        if render_settings.custom_range:
            scene.frame_start = render_settings.in_point
            scene.frame_end = render_settings.out_point
        
        #Start render
        if open_gl:
            area = bpy.context.area
            areatype = bpy.context.area.type               
            bpy.context.area.type = "VIEW_3D"
            bpy.ops.view3d.view_axis()
            bpy.ops.view3d.view_camera()
            
            bpy.ops.render.opengl('INVOKE_DEFAULT', animation=True)
            area.type = areatype            
            
        else:
            bpy.ops.render.render('INVOKE_DEFAULT', animation=True)  
        
        bpy.app.handlers.render_complete.append(reset_settings)
        bpy.app.handlers.render_cancel.append(reset_settings)
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

if __name__ == "__main__":
    register()
