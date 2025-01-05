from src.io.StreamReader import StreamReader
from src.data_types.Generic import *

# https://community.bistudio.com/wiki?title=P3D_File_Format_-_ODOLV4x
class P3dHeader:

    def __init__(self, reader = None):
        if reader is not None:
            self.consume(reader)
        else:
            self.file_type = "ODOL"

    def consume(self, reader: StreamReader):

        self.file_type = reader.read_bytes(4)   # // "ODOL"
        self.version = reader.meta("version", reader.read_ulong())

        # DayZ specifically identified by these versions.
        if self.version in (53, 54):
            self.dayz = reader.meta("dayz", True)
        else:
            self.dayz = reader.meta("dayz", False)

        if self.version >= 75: # // (arma3)
            self.enc1 = reader.read_ulong()
            self.enc2 = reader.read_ulong()
            if self.enc1 or self.enc2:
                reader.print_offset("Encrypted P3d")
                return # encrypted.

            if self.version>=58: # // (arma3)
                self.appid = reader.read_ulong()
            if self.version==58: # // (arma3)
                self.p3d_prefix = reader.read_asciiz(cdn = False)   # P3dPrefix;	// \a3\data_f\proxies\muzzle_flash\muzzle_flash_rifle_mk20
            
        self.n_lods = reader.meta('n_lods', reader.read_ulong())   # // alias NoOfResolutions;

        return True
    
# https://community.bistudio.com/wiki/P3D_Model_Info
class P3dModelInfo:

    def __init__(self, reader:StreamReader = None, n_lods=0, version=0, dayz=True):

        if reader is not None:
            self.consume(reader)
        else:
            self.resolutions=[0.0]*n_lods # float[Header.NoOfLods] ;// alias resolutions
            self.index = 0				# ulong; // appears to be a bit flag, 512, 256 eg
            self.mem_lod_sphere = 0.0	# float;
            self.geo_lod_sphere = 0.0	# float;;             // mostly same as MemLodSphere
            self.remarks = 0			# ulong;            // typically 00 00 00 00  00 00 00 00 00 00 0C 00 eg (last is same as user point flags)
            self.and_hints = 0			# ulong;
            self.or_hints = 0			# ulong;
            self.geo_offset = None		# XYZTriplet;              // model offset (unknown functionality),//mostly same as offset2
            self.map_icon_color = None	# rgba;            // RGBA 32 color
            self.map_selected_color = None# rgba;        // RGBA 32 color
            self.view_density	= 0.0	# float;        //-1 -> default shape values will be used (default value)  / 0 -> opaque / 1 -> transparent (DO NOT add this to an opaque object)
            self.bbox_min_position = None	# XYZTriplet;         // minimum coordinates of bounding box
            self.bbox_max_position	= None	# XYZTriplet;         // maximum coordinates of bounding box. Generally the complement of the 1st
                                            #        // pew.GeometryBounds in Pew is bboxMinPosition-bboxMaxPosition for X and Z
                                            #        // pew.ResolutionBounds mostly the same
            if version >=70:
                self.lod_density_coef = 0.0	# float;
            if version >=71:
                self.draw_importance = 0.0	# float;
            if version >=52:
               self.visual_bounds = None     # MinMaxVectors??;
            self.bounding_center = None   	# XYZTriplet;          // pew.GeometryAutoCenterPos (and mostly pew.ResolutionAutoCenterPos too)
            self.geometry_center = None 		# XYZTriplet;                  // mostly same as Offset1 often same as (but it isn't ResolutionPos)
            self.center_of_mass = None 		# XYZTriplet;             //CogOffset see below
            self.p3dinfo_inv_Inertia = None	# XYZTriplet[3];      // for ODOL7 this is a mixture of floats and index values

            self.auto_center = False		# tbool
            self.lock_auto_center = False	# tbool
            self.can_occlude = False		# tbool
            self.can_be_occluded = False	# tbool
            self.allow_animation = False	# tbool
            if version>=73 or dayz:
                self.disable_cover = False	# tbool

            self.thermal_profile = None		# float[24]; 
            if dayz:
                self.dayz_thermal_extra = 0.0   # float
            self.forceNot_alpha_model = 0		# ulong;    // V48 and beyond
            self.sb_source = 0				    # ulong;
            self.prefer_shadow_volume = False	# tbool;
            if version==48:
                self.shadow_offset = 0.0  	# float;
            self.allow_animation = False    # ******* DUPLICATE?? bool (there is a difference?)
            self.map_type = 0               # byte;
            if dayz:
                self.dayz_mass_array = []    # [] ?? how long, what type?

            self.mass = 0.0        			# float;
            self.mass_reciprocal = 0.0		# float;    // see note
            self.armor_mass = 0.0 			# float;    // see note
            self.armor_reciprocal = 0.0		# float;    // see note
            if version>=72:
                self.explosion_shielding = 0.0# float
            if version>=56:
                self.unknown_byte_indices = [] # byte[14]    // see note generally FF FF FF FF FF FF FF FF FF FF FF FF
            else:
                self.unknown_byte_indices = [] # byte[12]    // see note generally FF FF FF FF FF FF FF FF FF FF FF FF
            
            #///////////ARMA (V4x) ONLY ////////////
            self.unknown_long = 0 			# ulong;    // often same as NoOfLods
            self.can_blend = False    	    # tbool;    // generally set if ascii below has strings
            if version==54:             # Docs said "if (dayz==53" ??
                self.dayzv126 = 0            # byte;
            self.class_type = ""              # asciiz;   // class="House" See Named Properties
            self.destruct_type = ""           # asciiz    // ;damage="Tent" See Named Properties
            self.frequent = False	        # tbool;;                 // rarely true
            self.always0 = 0					# ulong;                  //
            if version >= 54:
                self.preferred_shadows = None # byte [NoOfLods][12]; //generally FF FF FF FF FF FF FF FF FF FF FF FF
            #///////////////////////////////////////

    def consume(self, reader: StreamReader):

        version = reader.meta("version")
        if version is None: reader.print_offset("P3d P3dModelInfo requires reader.meta('version')!", type="exception")
        dayz = reader.meta("dayz")
        if dayz is None: reader.print_offset("P3d P3dModelInfo requires reader.meta('dayz')!", type="exception")
        n_lods = reader.meta("n_lods")
        if n_lods is None: reader.print_offset("P3d P3dModelInfo requires reader.meta('n_lods')!", type="exception")


        self.resolutions = reader.read_float_array(n_lods,1)
        self.index = reader.read_ulong()
        self.mem_lod_sphere = reader.read_float()
        self.geo_lod_sphere = reader.read_float()
        self.remarks = reader.read_ulong()
        self.and_hints = reader.read_ulong()
        self.or_hints = reader.read_ulong()
        self.geo_offset = reader.read_xyz_triplet()
        self.map_icon_color = reader.read_rgba()
        self.map_selected_color = reader.read_rgba()
        self.view_density = reader.read_ulong()
        self.bbox_min_position = reader.read_xyz_triplet()
        self.bbox_max_position = reader.read_xyz_triplet()

        if version >= 70:
            self.lod_density_coef = reader.read_float()
        if version >= 71:
            self.draw_importance = reader.read_float()
        if version >= 70:
            reader.print_offset("TODO: Impliment MinMaxVectors!", type="exception")
            self.visual_bounds = 0
        
        self.bounding_center = reader.read_xyz_triplet()
        self.geometry_center = reader.read_xyz_triplet()
        self.center_of_mass = reader.read_xyz_triplet()
        reader.print_offset("inertia")
        self.p3dinfo_inv_Inertia = reader.read_xyz_triplet(n=3)
        reader.print_offset("bools")
        self.auto_center = reader.read_tbool()
        self.lock_auto_center = reader.read_tbool()
        self.can_occlude = reader.read_tbool()
        self.can_be_occluded = reader.read_tbool()
        self.allow_animation = reader.read_tbool()
        
        if version>=73 or dayz:
            self.disable_cover = reader.read_tbool()
        reader.print_offset("thermal")
        self.thermal_profile = reader.read_float_array(n=24)
        reader.print_offset("thermal_extra")
        if dayz:
            self.dayz_thermal_extra = reader.read_float()
        self.forceNot_alpha_model = reader.read_ulong()
        self.sb_source = reader.read_ulong()
        self.prefer_shadow_volume = reader.read_tbool()
        if version==48:
            self.shadow_offset = reader.read_float()
        self.allow_animation = reader.read_tbool()
        self.map_type = reader.read_byte()



        reader.print_offset(f"{self.map_type}")
        exit()

        return True
    
    


class P3d:

    def __init__(self, reader = None):
        if reader is not None:
            self.consume(reader)
        else:
            self.header = P3dHeader()


    def consume(self, reader: StreamReader):

        self.header = P3dHeader(reader)
        self.info = P3dModelInfo(reader)
        return True