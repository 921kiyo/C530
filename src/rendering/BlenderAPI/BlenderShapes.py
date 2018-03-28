import bpy
import math
import random
import mathutils as mathU
import itertools

from rendering.BlenderAPI.BlenderObjects import *
from rendering.BlenderAPI.BlenderNodes import *
from rendering.BlenderAPI.BlenderExceptions import *


class BlenderMesh(BlenderObject):

    def __init__(self, **kwargs):
        super(BlenderMesh, self).__init__(**kwargs)
        self.nodes = {}
        self.links = None
        self.node_tree = None
        self.material = None
        self.setup_node_tree()

    def setup_node_tree(self):
        """ 
        node tree built according to the following structure                  

        node_mat <--(surface-shader)-- node_mix <--(shader-bsdf)-- (node_diff + node_gloss)

        node_diff + node_gloss just means outputs of both nodes go into mix shader
        The pairs in the parantheses define input-output pairs
        """
        obj_name = self.reference.name
        if (len(self.reference.data.materials) == 0):
            mat = bpy.data.materials.new(name="Mat" + "_" + obj_name)  # set new material to variable
            self.reference.data.materials.append(mat)  # add the material to the object
        self.material = self.reference.data.materials[0]
        self.reference.data.materials[0].use_nodes = True

        self.node_tree = self.material.node_tree
        for node in self.node_tree.nodes:
            if node == self.node_tree.nodes['Material Output'] or node == self.node_tree.nodes['Diffuse BSDF']:
                continue
            self.node_tree.nodes.remove(node)
        self.nodes['node_mat'] = BlenderMaterialOutputNode(self.node_tree,
                                                           reference=self.node_tree.nodes['Material Output'])
        self.nodes['node_diff'] = BlenderDiffuseBSDFNode(self.node_tree, reference=self.node_tree.nodes['Diffuse BSDF'])
        self.nodes['node_gloss'] = BlenderGlossyBSDFNode(self.node_tree)
        self.nodes['node_mix'] = BlenderMixShaderNode(self.node_tree)
        self.links = self.node_tree.links
        self.links.new(self.nodes['node_mix'].get_shader_output(), self.nodes['node_mat'].get_surface_input())
        self.links.new(self.nodes['node_diff'].get_bsdf_output(), self.nodes['node_mix'].get_shader1_input())
        self.links.new(self.nodes['node_gloss'].get_bsdf_output(), self.nodes['node_mix'].get_shader2_input())

    def set_diffuse(self, color=(0.5, 0.5, 0.5, 1), rough=0.5):
        """
        set the roughness and color of the diffuse shader node
        :param color: 4-tuple defining the RGBA channels in [0,1]
        :param roughness: [0,1] value defininf relative roughness of shader
        """
        if not check_vector_elements_normalized(color):
            raise InvalidInputError('Diffuse color needs to be normalized!')
        if not check_scalar_normalized(rough):
            raise InvalidInputError('Diffuse roughness needs to be normalized!')
        self.nodes['node_diff'].set_color(*color)
        self.nodes['node_diff'].set_roughness(rough)

    def set_gloss(self, color=(0.5, 0.5, 0.5, 1), rough=0.5):
        """
        set the roughness and color of the glossy shader node
        :param color: 4-tuple defining the RGBA channels in [0,1]
        :param roughness: [0,1] value defininf relative roughness of shader
        """
        if not check_vector_elements_normalized(color):
            raise InvalidInputError('Gloss color needs to be normalized!')
        if not check_scalar_normalized(rough):
            raise InvalidInputError('Gloss roughness needs to be normalized!')
        self.nodes['node_gloss'].set_color(*color)
        self.nodes['node_gloss'].set_roughness(rough)

    def set_mixer(self, factor):
        """
        set the mixing factor of the mixed shader node
        :param factor: [0,1] value defining the diffuse-glossy shader ratio
        """
        if not check_scalar_normalized(factor):
            raise InvalidInputError('mixer factor needs to be normalized!')
        self.nodes['node_mix'].set_fac(factor)

    def add_image_texture(self, image_path, projection='FLAT', mapping='UV'):
        """
        :param image_path: path to texture image file
        :param projection: defines projection type
        :param mapping: defines coordinate mapping
        adds an image texture node and texture coordinate node (required to define mapping of texture)
        """
        if not 'node_imgtex' in self.nodes.keys():
            self.nodes['node_imgtex'] = BlenderImageTextureNode(self.node_tree)
            self.links.new(self.nodes['node_imgtex'].get_color_output(), self.nodes['node_diff'].get_color_input())
            self.links.new(self.nodes['node_imgtex'].get_color_output(), self.nodes['node_gloss'].get_color_input())

        if mapping not in ['UV', 'Generated']:
            return False

        if not 'node_texcoord' in self.nodes.keys():
            self.nodes['node_texcoord'] = BlenderTexCoordNode(self.node_tree)

        if mapping == 'Generated':
            vector = self.nodes['node_texcoord'].get_Generated_output()
        else:
            vector = self.nodes['node_texcoord'].get_UV_output()
        self.links.new(vector, self.nodes['node_imgtex'].get_vector_input())

        try:
            img = bpy.data.images.load(image_path)
        except:
            return False

        success = self.nodes['node_imgtex'].set_projection(projection) and self.nodes['node_imgtex'].set_image(img)
        if not success:
            return success

        return True

    def toggle_smooth(self):
        for poly in self.reference.data.polygons:
            poly.use_smooth = True

    def compute_mesh_bbvol(self):
        VX = [v.co[0] for v in self.reference.data.vertices]
        VY = [v.co[1] for v in self.reference.data.vertices]
        VZ = [v.co[2] for v in self.reference.data.vertices]
        return (max(VX) - min(VX))*(max(VY) - min(VY))*(max(VZ) - min(VZ))

    def compute_mesh_bbvol_diagonal(self):
        VX = [v.co[0] for v in self.reference.data.vertices]
        VY = [v.co[1] for v in self.reference.data.vertices]
        VZ = [v.co[2] for v in self.reference.data.vertices]
        return math.sqrt(
            (max(VX) - min(VX))**2+(max(VY) - min(VY))**2+(max(VZ) - min(VZ))**2)

    def set_mesh_bbvol(self, VReq):
        if not check_scalar_non_negative (VReq):
            raise InvalidInputError('Mesh BB Volume has to be positive!')
        self.set_scale((1.0,1.0,1.0))
        VNom = self.compute_mesh_bbvol()
        scale = math.pow(VReq/VNom, 1./3.)
        self.set_scale((scale, scale, scale))
        
    def turn_off(self):
        """
        push it to second layer to hide
        """
        self.reference.layers[1] = True
        self.reference.layers[0] = False

    def turn_on(self):
        """
        push it to the topmost layer to show
        """
        self.reference.layers[0] = True
        self.reference.layers[1] = False



class BlenderCube(BlenderMesh):
    def __init__(self, **kwargs):
        super(BlenderCube, self).__init__(**kwargs)

    def blender_create_operation(self):
        bpy.ops.mesh.primitive_cube_add()


class BlenderPlane(BlenderMesh):
    def __init__(self, **kwargs):
        super(BlenderPlane, self).__init__(**kwargs)

    def blender_create_operation(self):
        bpy.ops.mesh.primitive_plane_add()


class BlenderImportedShape(BlenderMesh):
    def __init__(self, **kwargs):
        """
        :required obj_path: defines path to obj file
        """
        super(BlenderImportedShape, self).__init__(**kwargs)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

    def blender_create_operation(self, obj_path=None):
        assert obj_path is not None, "Required keyword argument for importing shape: obj_path=[filepath]"
        bpy.ops.import_scene.obj(filepath=obj_path)




