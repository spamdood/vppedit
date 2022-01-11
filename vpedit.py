import json

#Written by spamdude, 2021

class VPPEditor():
    def __init__(self, filename):
        '''Opens a VPPEditor instance bound to the file specified in filename. Changes to the actual file are executed with instance method "push."'''
        self.filename = filename
        self.contents = json.loads(open(self.filename).read())
        
    def selection_info(func):
        func.__doc__ += '''

selectors (kwargs) guide:

Rectangular (dimensional) selection:
x_bound: iterable[int, int] OR int -> An iterable of two ints (ascending order) or a single int to filter out voxels using their X coordinate.
y_bound: iterable[int, int] OR int -> An iterable of two ints (ascending order) or a single int to filter out voxels using their Y coordinate.
z_bound: iterable[int, int] OR int -> An iterable of two ints (ascending order) or a single int to filter out voxels using their Z coordinate.

Color-based selection:
colorkey: iterable[strings] OR string -> An iterable of hexadecimal color strings or an individual color string (prefixed with #) to filter voxels with. Color strings are case-insensitive.
opacity:  iterable[int, int] OR float -> An iterable of ints or a single int (between 0 and 100 inclusive) to further filter voxels with based on their opacity.
metallic: bool -> Can be True of False; filters voxels in the selection based on whether they are metallic or not
emissive: iterable[int, int] OR float OR bool -> An iterable of ints or a single ints or False to filter voxels based on whether or not they emit light, and if so, how much light they emit.

*emissive selection has not been implemented yet*

Group key selection:
groupkey: iterable[strings] OR string -> An iterable of group name strings or an individual group name string to filter voxels with. Default voxels have no group tag, which can be set or erased using the "group" and "ungroup" methods and persist indefinitely.

Previous selection:
voxels: iterable[dicts] -> An iterable of voxel dict objects to process instead of (or including) other selectors.

IMPORTANT NOTE: Rectangular, color-based, and group key selectors compound with each other, while previous selection is not subject to these.
'''
        return func

    @selection_info
    def select(self, **selectors):
        '''Returns a list of voxels that match the specified conditions, or all of them if no
parameters have been set.'''
        affected = []
        x_bound = selectors['x_bound'] if 'x_bound' in selectors else None
        y_bound = selectors['y_bound'] if 'y_bound' in selectors else None
        z_bound = selectors['z_bound'] if 'z_bound' in selectors else None
        colorkey = selectors['colorkey'] if 'colorkey' in selectors else None
        groupkey = selectors['groupkey'] if 'groupkey' in selectors else None
        opacity = selectors['opacity'] if 'opacity' in selectors else None
        metallic = selectors['metallic'] if 'metallic' in selectors else None
        emissive = selectors['emissive'] if 'emissive' in selectors else None
        for voxel in self.contents['voxels']:
            x, y, z, color, key, opac, metal, luminous = True, True, True, True, True, True, True, True
            if x_bound:
                if type(x_bound) == int:
                    if x_bound != voxel['x']:
                        x = False
                else:
                    if not (x_bound[0] <= voxel['x'] <= x_bound[1]):
                        x = False
            if y_bound:
                if type(y_bound) == int:
                    if y_bound != voxel['y']:
                        y = False
                else:
                    if not(y_bound[0] <= voxel['y'] <= y_bound[1]):
                        y = False
            if z_bound:
                if type(z_bound) == int:
                    if z_bound != voxel['z']:
                        z = False
                else:
                    if not (z_bound[0] <= voxel['z'] <= z_bound[1]):
                        z = False
            if colorkey:
                if type(colorkey) == str:
                    if voxel['c'].upper() != colorkey.upper():
                        color = False
                else:
                    if voxel['c'].upper() not in [c.upper() for c in colorkey]:
                        color = False
            if groupkey:
                if type(groupkey) == str:
                    try:
                        if voxel['group'] != groupkey:
                            key = False
                    except KeyError:
                        key = False
                else:
                    try:
                        if voxel['group'] not in groupkey:
                            key = False
                    except KeyError:
                        key = False
            if opacity:
                if type(opacity) == int:
                    if voxel['op'] != opacity:
                        opac = False
                else:
                    if not (opacity[0] <= voxel['op'] <= opacity[1]):
                        opac = False
            if metallic != None:
                if metallic != voxel['me']:
                    metal = False
            if luminous != None:
                pass
            if x and y and z and color and key and opac and metal and luminous:
                affected.append(voxel)
        addtl = selectors['voxels'] if 'voxels' in selectors else []
        affected += [item for item in addtl if item not in affected]
        return affected
    
    def resize(self, resizeTo):
        '''Does NOT transform the size of the model itself, but resizes the model's building frame.'''
        self.contents['size'] = resizeTo
    
    def recolor(self, selection, **valuemaps):
        '''Change voxel appearances in the affected area based on valuemaps dicts.
The color, opacity (transparency), and metallic effect of voxels can be recolored,
though metallicity can only be true or false. The format of each dict should be
old_value_string: new_value string for each attribute to remap.'''
        ncm = {}
        if 'colormap' in valuemaps:
            for item in valuemaps['colormap']:
                ncm[item.upper()] = colormap[item].upper()
        if 'opacitymap' in valuemaps:
            opacitymap = valuemaps['opacitymap']
        else:
            opacitymap = {}
        if 'metallicmap' in valuemaps:
            metallicmap = valuemaps['metallicmap']
        else:
            metallicmap = {}
        for voxel in selection:
            try:
                voxel['c'] = ncm[voxel['c'].upper()]
                voxel['op'] = opacitymap[voxel['op']]
                voxel['me'] = metallicmap[voxel['me']]
            except KeyError:
                pass
    
    def rotate(self, selection, center='FILL', xd=0, yd=0, zd=0):
        '''Rotate a selection of voxels in 90-degree increments on all three planes.
Center specifies the center of rotation, with the default 'FILL' setting the corners of rotation
as the corners of the rectangular area the selection fills. Otherwise, corners can be set
to a 3-int list representing the 3D coordinates of the center of rotation.

XD rotates the selection on the X-Y plane (side to side), YD rotates the selection
on the Y-Z plane (backwards and forwards), and ZD rotates the selection on the X-Z
plane (side to side but vertical.)'''
        if selection == 'all':
            selection = self.contents['voxels']
        if center == 'FILL':
            corners = [[], []]
            corners[0] = [min([item['x'] for item in selection]), min([item['y'] for item in selection]), min([item['z'] for item in selection])]
            corners[1] = [max([item['x'] for item in selection]), max([item['y'] for item in selection]), max([item['z'] for item in selection])]
            center = [(corners[0][0] + corners[1][0])/2, (corners[0][1] + corners[1][1])/2, (corners[0][2] + corners[1][2])/2]
        if xd != 0:
            xd %= 360
            for voxel in selection:
                dx, dy = center[0] - voxel['x'], center[1] - voxel['y']
                if xd == 270:
                    voxel['x'], voxel['y'] = center[1] - dy, center[0] + dx
                elif xd == 180:
                    voxel['x'], voxel['y'] = center[0] + dx, center[1] + dy
                elif xd == 90:
                    voxel['x'], voxel['y'] = center[1] + dy, center[0] - dx
        if yd != 0:
            yd %= 360
            for voxel in selection:
                dy, dz = center[1] - voxel['y'], center[2] - voxel['z']
                if yd == 270:
                    voxel['y'], voxel['z'] = center[2] - dz, center[1] + dy
                elif yd == 180:
                    voxel['y'], voxel['z'] = center[1] + dy, center[2] + dz
                elif yd == 90:
                    voxel['y'], voxel['z'] = center[2] + dz, center[0] - dy
        if zd != 0:
            zd %= 360
            for voxel in selection:
                dx, dz = center[0] - voxel['x'], center[2] - voxel['z']
                if zd == 270:
                    voxel['x'], voxel['z'] = center[2] - dz, center[0] + dx
                elif zd == 180:
                    voxel['x'], voxel['z'] = center[0] + dx, center[2] + dz
                elif zd == 90:
                    voxel['x'], voxel['z'] = center[2] + dz, center[0] - dx
        
    def reflect(self, selection, x=False, y=False, z=False):
        '''Reflect the selected area along the X, Y, and Z axes, or across an arbitrary point.
To reflect the selected area on itself, set X, Y, or Z to True.
To reflect across a certain point, set X, Y, or Z to an integer.'''
        if selection == 'all':
            selection = self.contents['voxels']
        sx = [d['x'] for d in selection]
        xmin, xmax = min(sx), max(sx)
        sy = [d['y'] for d in selection]
        ymin, ymax = min(sy), max(sy)
        sz = [d['z'] for d in selection]
        zmin, zmax = min(sz), max(sz)
        for voxel in selection:
            if x:
                if x == True:
                    add = xmax - voxel['x']
                    voxel['x'] = xmin + add
                else:
                    voxel['x'] = 2 * x - voxel['x']
            if y:
                if y == True:
                    add = ymax - voxel['y']
                    voxel['y'] = ymin + add
                else:
                    voxel['y'] = 2 * y - voxel['y']
            if z:
                if z == True:
                    add = zmax - voxel['z']
                    voxel['z'] = zmin + add
                else:
                    voxel['z'] = 2 * z - voxel['z']

    def group(self, selection, groupname):
        '''Assign the selected voxels to a group. This function overwrites previous group names.'''
        if selection == 'all':
            selection = self.contents['voxels']
        for voxel in selection:
            voxel['group'] = groupname

    def ungroup(self, selection):
        '''Remove all group names from the selection.'''
        if selection == 'all':
            selection = self.contents['voxels']
        for voxel in selection:
            voxel.pop('group', None)

    def translate(self, selection, x_inc, y_inc, z_inc):
        '''Move the selection along each dimension according to the xyz increment paramaters.'''
        if selection == 'all':
            selection = self.contents['voxels']
        for voxel in selection:
            voxel['x'] += x_inc
            voxel['y'] += y_inc
            voxel['z'] += z_inc

    def transform(self, selection, x_inc, y_inc, z_inc):
        '''see VPPEditor.translate'''
        self.translate(selection, x_inc, y_inc, z_inc)

    def remove(self, selection):
        '''Erase all voxels in the selection. Remember when you spent five hours working on an extensively
detailed model, and then ruined it just before it was finished by accidentally paint filling
a massive rectangle? No? Well, this is for you anyways.'''
        if selection == 'all':
            selection = self.contents['voxels']
        for voxel in selection:
            self.contents['voxels'].remove(voxel)

    def clone(self, selection, copy_group = False):
        '''Creates a copy of the selection and returns a list of the copied voxels. copy_group (T/F) determines
 whether or not the selection's group name(s) will also be copied.'''
        if selection == 'all':
            selection = self.contents['voxels']
        cloned = []
        for voxel in selection:
            coxel = dict(voxel)
            if not copy_group:
                coxel.pop('group', None)
            cloned.append(coxel)
            self.contents['voxels'].append(coxel)
        return cloned

    def paint(self, corners, **appearance):
        '''Fill all empty spaces between each corner (inclusive) with voxels. Acceptable values for appearance are
"color" -> hex string, opacity -> int between 0 and 100 inclusive, and metallic -> True or False. Corners should be a list
of 2 3-length sublists representing the X, Y, and Z values of each (opposite) corner.'''
        if 'color' in appearance:
            color = appearance['color']
        else:
            raise TypeError('A color must be specified for the voxels.')
        if 'opacity' in appearance:
            opc = appearance['opacity']
        else:
            opc = 100
        if 'metallic' in appearance:
            met = appearance['metallic']
        else:
            met = False
        for x in range(corners[0][0], corners[1][0] + 1):
            for y in range(corners[0][1], corners[1][1] + 1):
                for z in range(corners[0][2], corners[1][2] + 1):
                    vac = False
                    for voxel in self.contents['voxels']:
                        if voxel['x'] == x and voxel['y'] == y and voxel['z'] == z:
                            vac = True
                    if vac == False:
                        template = {"x": x, "y": y, "z": z, "c": color, "me": met, "op": opc, "es": False}
                        self.contents['voxels'].append(template)

    def push(self):
        '''Push changes from the editor version of the model to the VPP file itself. Changes are irreversible, so make sure to have a backup
copy in case something goes wrong.''' 
        filec = open(self.filename, 'w')
        filec.write(json.dumps(self.contents))
        filec.close()
        
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        return str(f'{self.filename}: {self.contents}')
