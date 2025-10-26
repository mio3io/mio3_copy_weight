import bpy
from . import op_copy_weight


class MIO3CW_PT_main(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_label = "Mio3 Copy Weight"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == "EDIT"

    def draw(self, context):
        layout = self.layout
        for op in ops:
            if hasattr(op, "menu"):
                op.menu(self, context)
        row = layout.row(align=True)
        row.operator("object.vertex_weight_normalize_active_vertex", text="Normalize")
        row.operator("object.mio3_vertex_weight_copy", text="Copy Weight")


def update_panel(self, context):
    is_exist = hasattr(bpy.types, "MIO3CW_PT_main")
    category = bpy.context.preferences.addons[__package__].preferences.category
    if is_exist:
        try:
            bpy.utils.unregister_class(MIO3CW_PT_main)
        except:
            pass

    MIO3CW_PT_main.bl_category = category
    bpy.utils.register_class(MIO3CW_PT_main)


class MIO3CW_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    category: bpy.props.StringProperty(
        name="Tab Name",
        default="Item",
        update=update_panel,
    )

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, "category")


translation_dict = {
    "ja_JP": {
        ("*", "The active object has no selected vertices"): "アクティブオブジェクトに選択された頂点がありません",
        ("Operator", "Copy Weight"): "ウェイトをコピー",
    }
}  # fmt: skip


ops = [
    op_copy_weight,
]


def register():
    bpy.app.translations.register(__name__, translation_dict)
    bpy.utils.register_class(MIO3CW_Preferences)
    bpy.utils.register_class(MIO3CW_PT_main)
    for op in ops:
        op.register()


def unregister():
    for op in reversed(ops):
        op.unregister()
    bpy.utils.unregister_class(MIO3CW_PT_main)
    bpy.utils.unregister_class(MIO3CW_Preferences)
    bpy.app.translations.unregister(__name__)
