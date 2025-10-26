import bpy
import bmesh
from bpy.types import Operator
from bpy.props import EnumProperty


class MIO3_OT_copy_weight(Operator):
    bl_idname = "object.mio3_vertex_weight_copy"
    bl_label = "Copy Weights"
    bl_description = "Copy weights"
    bl_options = {"REGISTER", "UNDO"}

    subset: EnumProperty(
        name="Subset",
        items=[
            ("ALL", "All", "Copy every vertex group"),
            ("DEFORM", "Deform Pose Bones", "Copy only deforming bone groups"),
            ("ACTIVE", "Active Only", "Copy the currently active vertex group"),
        ],
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mode == "EDIT" and obj.type == "MESH"

    def execute(self, context):
        active_obj = context.active_object
        active_obj.update_from_editmode()

        active_bm = bmesh.from_edit_mesh(active_obj.data)
        active_bm.verts.ensure_lookup_table()
        active_vert = active_bm.select_history.active
        if not active_vert:
            return {"CANCELLED"}

        vertex_groups = self.get_vgroups(active_obj, active_bm, active_vert)

        if active_obj.data.total_vert_sel > 1:
            selected_verts = [v for v in active_bm.verts if v.select and v != active_vert]
            self.copy_weight(active_obj, active_bm, vertex_groups, selected_verts)

            if active_obj.use_mesh_mirror_x:
                mirror_source = active_obj.data.vertices[selected_verts[0].index]
                self.apply_paste_from_mirror(active_obj, mirror_source)

            bmesh.update_edit_mesh(active_obj.data)

        target_obj = self.get_sub_object(context, active_obj)
        if target_obj and vertex_groups:
            target_obj.update_from_editmode()

            target_bm = bmesh.from_edit_mesh(target_obj.data)
            target_bm.verts.ensure_lookup_table()
            selected_verts = [v for v in target_bm.verts if v.select]

            if selected_verts:
                self.copy_weight(target_obj, target_bm, vertex_groups, selected_verts)

                if target_obj.use_mesh_mirror_x:
                    context.view_layer.objects.active = target_obj
                    mirror_source = target_obj.data.vertices[selected_verts[0].index]
                    self.apply_paste_from_mirror(target_obj, mirror_source)
                    context.view_layer.objects.active = active_obj

                if active_obj.vertex_groups.active:
                    target_group_name = active_obj.vertex_groups.active.name
                    if target_group_name in target_obj.vertex_groups:
                        target_obj.vertex_groups.active_index = target_obj.vertex_groups[
                            target_group_name
                        ].index

                bmesh.update_edit_mesh(target_obj.data)

        return {"FINISHED"}

    def get_vgroups(self, obj, bm, active_vert):
        deform_layer = bm.verts.layers.deform.verify()

        deform_groups = self.get_deform_vertex_groups(obj)
        deform_indices = {vg.index for vg in deform_groups}

        vertex_groups = []
        for group_index, weight in active_vert[deform_layer].items():
            if self.subset == "DEFORM" and group_index not in deform_indices:
                continue
            if self.subset == "ACTIVE" and group_index != obj.vertex_groups.active_index:
                continue
            vertex_groups.append((obj.vertex_groups[group_index], weight))
        return vertex_groups

    def copy_weight(self, obj, bm, vertex_groups, selected_verts):
        deform_layer = bm.verts.layers.deform.verify()

        source_group_indices = set()
        for group, _ in vertex_groups:
            if group.name not in obj.vertex_groups:
                vgroup = obj.vertex_groups.new(name=group.name)
            else:
                vgroup = obj.vertex_groups[group.name]
            if not vgroup.lock_weight:
                source_group_indices.add(vgroup.index)

        if not source_group_indices:
            return

        for vert in selected_verts:
            deform = vert[deform_layer]
            current_weights = dict(deform)

            for index in list(current_weights):
                if index not in source_group_indices and index in deform:
                    deform[index] = 0.0

            for group, weight in vertex_groups:
                vgroup = obj.vertex_groups[group.name]
                if not vgroup.lock_weight:
                    deform[vgroup.index] = weight

    @staticmethod
    def get_deform_vertex_groups(obj):
        deform_groups = []
        armature = obj.find_armature()
        if not armature or not hasattr(armature, "pose"):
            return deform_groups

        for vg in obj.vertex_groups:
            if any(b for b in armature.pose.bones if b.bone.use_deform and b.name == vg.name):
                deform_groups.append(vg)
        return deform_groups

    @staticmethod
    def get_sub_object(context, active_obj):
        for obj in context.selected_objects:
            if obj.type in {"MESH"} and obj != active_obj:
                return obj
        return None

    @staticmethod
    def apply_paste_from_mirror(obj, vert):
        if not vert.groups:
            return
        for g in vert.groups:
            vg = obj.vertex_groups[g.group]
            if vg.lock_weight:
                continue
            bpy.ops.object.vertex_weight_paste(weight_group=g.group)


classes = [
    MIO3_OT_copy_weight,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
