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
        x, y, z, color, key = False, False, False, False, False
        x_bound = selectors['x_bound'] if 'x_bound' in selectors else None
        y_bound = selectors['y_bound'] if 'y_bound' in selectors else None
        z_bound = selectors['z_bound'] if 'z_bound' in selectors else None
        colorkey = selectors['colorkey'] if 'colorkey' in selectors else None
        groupkey = selectors['groupkey'] if 'groupkey' in selectors else None
        for voxel in self.contents['voxels']:
            if x_bound:
                if type(x_bound) == int:
                    if x_bound == voxel['x']:
                        x = True
                    else:
                        x = False
                else:
                    if x_bound[0] <= voxel['x'] <= x_bound[1]:
                        x = True
                    else:
                        x = False
            else:
                x = True
            if y_bound:
                if type(y_bound) == int:
                    if y_bound == voxel['y']:
                        y = True
                    else:
                        y = False
                else:
                    if y_bound[0] <= voxel['y'] <= y_bound[1]:
                        y = True
                    else:
                        y = False
            else:
                y = True
            if z_bound:
                if type(z_bound) == int:
                    if z_bound == voxel['z']:
                        z = True
                    else:
                        z = False
                else:
                    if z_bound[0] <= voxel['z'] <= z_bound[1]:
                        z = True
                    else:
                        z = False
            else:
                z = True
            if colorkey:
                if type(colorkey) == str:
                    if voxel['c'].upper() == colorkey.upper():
                        color = True
                    else:
                        color = False
                else:
                    if voxel['c'].upper() in [c.upper() for c in colorkey]:
                        color = True
                    else:
                        color = False
            else:
                color = True
            if groupkey:
                if type(groupkey) == str:
                    try:
                        if voxel['group'] == groupkey:
                            key = True
                        else:
                            key = False
                    except KeyError:
                        key = False
                else:
                    try:
                        if voxel['group'] in groupkey:
                            key = True
                        else:
                            key = False
                    except KeyError:
                        key = False
            else:
                key = True
            if x and y and z and color and key:
                affected.append(voxel)
        addtl = selectors['voxels'] if 'voxels' in selectors else []
        for item in addtl:
            if item not in affected:
                affected.append(item)
        return affected
    @selection_info
    def resize(self, resizeTo):
        '''Does NOT transform the size of the model itself, but resizes the model's building frame.'''
        self.contents['size'] = resizeTo
    @selection_info
    def recolor(self, colormap, **selectors):
        '''Change all colors in the affected area according to the colormap parameter.
The colormap should be a dict with the keys as the original colors and the values as the
new colors you want to set them to. Colors are case insensitive.'''
        affected = self.select(**selectors)
        for item in colormap:
            colormap[item] = colormap[item].upper()
        for voxel in affected:
            try:
                voxel['c'] = colormap[voxel['c'].upper()]
            except KeyError:
                pass
    @selection_info(self):
    def rotate(self):
        '''WORK IN PROGRESS HERE'''
        ...
    @selection_info
    def reflect(self, x=False, y=False, z=False, **selectors):
        '''Reflect the selected area along the X, Y, and/or Z axes. Set X, Y, or Z to 1 to flip that axis.'''
        affected = self.select(**selectors)
        sx = [d['x'] for d in affected]
        xin, xax = min(sx), max(sx)
        sy = [d['y'] for d in affected]
        yin, yax = min(sy), max(sy)
        sz = [d['z'] for d in affected]
        zin, zax = min(sz), max(sz)
        for voxel in affected:
            if x == 1:
                add = xax - voxel['x']
                voxel['x'] += -voxel['x'] + xin + add
            if y == 1:
                add = yax - voxel['y']
                voxel['y'] += -voxel['y'] + yin + add
            if z == 1:
                add = zax - voxel['z']
                voxel['z'] += -voxel['z'] + zin + add
    @selection_info
    def group(self, groupname, **selectors):
        '''Assign the selected voxels to a group. This function overwrites previous group names.'''
        affected = self.select(**selectors)
        for voxel in affected:
            voxel['group'] = groupname
    @selection_info
    def ungroup(self, groupname, **selectors):
        '''Remove all group names from the selection.'''
        affected = self.select(**selectors)
        for voxel in affected:
            voxel.pop('group', None)
    @selection_info
    def transform(self, x_inc, y_inc, z_inc, **selectors):
        '''Move the selection along each dimension according to the xyz increment paramaters.'''
        affected = self.select(**selectors)
        for voxel in affected:
            voxel['x'] += x_inc
            voxel['y'] += y_inc
            voxel['z'] += z_inc
    @selection_info
    def remove(self, **selectors):
        '''Erase all voxels in the selection. Remember when you spent five hours working on an extensively
detailed model, and then ruined it just before it was finished by accidentally paint filling
a massive rectangle? No? Well, this is for you anyways.'''
        affected = self.select(**selectors)
        for voxel in affected:
            self.contents['voxels'].remove(voxel)
    @selection_info
    def clone(self, copy_group, **selectors):
        '''Creates a copy of the selection and returns a list of the copied voxels. copy_group (T/F) determines
 whether or not the selection's group name(s) will also be copied.'''
        affected = self.select(**selectors)
        cloned = []
        for voxel in affected:
            coxel = dict(voxel)
            if copy_group:
                coxel.pop('group', None)
            cloned.append(coxel)
            self.contents['voxels'].append(coxel)
        return cloned
    @selection_info
    def push(self):
        '''Push changes from the editor version of the model to the VPP file itself. Changes are irreversible, so make sure to have a backup
copy in case something goes wrong.''' 
        filec = open(self.filename, 'w')
        filec.write(json.dumps(self.contents))
        filec.close()
    def __repr__(self):
        return str(self)
    def __str__(self):
        return str(self.contents)
