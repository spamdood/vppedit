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
opacity:  iterable[float, float] OR float -> An iterable of floats or a single float (between 0 and 1) to further filter voxels with based on their opacity.
metallic: bool -> Can be True of False; filters voxels in the selection based on whether they are metallic or not
emissive: iterable[float, float] OR float OR bool -> An iterable of floats or a single float or False to filter voxels based on whether or not they emit light, and if so, how much light they emit.

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
                #raise NotImplementedError('Emissive-based selection doesn\'t save to files yet.')
                ...
            if x and y and z and color and key and opac and metal and luminous:
                affected.append(voxel)
        addtl = selectors['voxels'] if 'voxels' in selectors else []
        affected += [item for item in addtl if item not in affected]
        return affected
    
    def resize(self, resizeTo):
        '''Does NOT transform the size of the model itself, but resizes the model's building frame.'''
        self.contents['size'] = resizeTo
    
    def recolor(self, selection, colormap, opacitymap, metallicmap):
        '''Change all colors and/or voxel effects in the affected area according to the colormap parameter.
All maps should be a dict with the keys as the original colors, opacities, etc. and the values as the
new colors/opacity values you want to set them to. Everything is case insensitive and each colormap is applied
independently of the others.'''
        for item in colormap:
            colormap[item] = colormap[item].upper()
        for voxel in selection:
            try:
                voxel['c'] = colormap[voxel['c'].upper()]
                voxel['op'] = colormap[voxel['op']]
                voxel['me'] = colormap[voxel['me']]
            except KeyError:
                pass
    
    def rotate(self):
        '''WORK IN PROGRESS HERE'''
        ...
    
    def reflect(self, selection, x=False, y=False, z=False):
        '''Reflect the selected area along the X, Y, and/or Z axes. Set X, Y, or Z to 1 to flip that axis.'''
        if selection == 'all':
            selection = self.contents['voxels']
        sx = [d['x'] for d in selection]
        xmin, xmax = min(sx), max(sx)
        sy = [d['y'] for d in selection]
        ymin, ymax = min(sy), max(sy)
        sz = [d['z'] for d in selection]
        zmin, zmax = min(sz), max(sz)
        for voxel in selection:
            if x == 1:
                add = xmax - voxel['x']
                voxel['x'] = xmin + add
            if y == 1:
                add = ymax - voxel['y']
                voxel['y'] = ymin + add
            if z == 1:
                add = zmax - voxel['z']
                voxel['z'] = zmin + add

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
            if copy_group:
                coxel.pop('group', None)
            cloned.append(coxel)
            self.contents['voxels'].append(coxel)
        return cloned

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
