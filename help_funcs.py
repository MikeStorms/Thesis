import classes as cls
from copy import deepcopy
import pickle

class SpatialMap():
    def __init__(self,layer_index,OX,OY):
        self.size = [OX,OY]
        self.layer_index = layer_index
        self.map = [[0 for i in range(OX)] for j in range(OY)]
        self.percentage = 0

    def set_true(self, IX, IY):
        self.map[IX][IY] = 1
        self.update_percentage()

    def set_false(self, IX, IY):
        self.map[IX][IY] = 0
        self.update_percentage()

    def load(self, name):
        f = open(name, 'rb')
        loaded_map = pickle.load(f)
        f.close
        assert len(loaded_map) == self.size[0], "Loading map %s has the wrong OX dimension for layer %d " % (name, self.layer_index)
        assert len(loaded_map[0]) == self.size[1], "Loading map %s has the wrong OY dimension for layer %d " % (name, self.layer_index)
        self.map = loaded_map
        self.update_percentage()

    def update_percentage(self):
        number_true = len([item for row in self.map for item in row if item == 1])
        self.percentage = number_true / (self.size[0] * self.size[1])

class SpatialMapList():
    def __init__(self,layer_indices,layer_info):
        map_list = {}
        for index in layer_indices:
            map_list[index] = SpatialMap(index, layer_info[index]['OX'], layer_info[index]['OY'])
        self.map_list = map_list
        self.map_list_input = []

    def load(self, path):
        for index in self.map_list:
            self.map_list[index].load(path + "_%d" % (index))

    def load_extend(self, layer_info):
        self.map_list_input = map_data_extension(self.map_list, layer_info)

def max_pixelwise_unrolling(input_settings, layer_spec):
    max_per_layer = []
    layers = [cls.Layer.extract_layer_info(layer_spec.layer_info[layer_number])
              for layer_number in layer_spec.layer_info]

    first = True
    min_unrolling = 0
    layers_min = []
    for il, layer in enumerate(layers):
        max_unrolling = layer.FX*layer.FY*layer.K*layer.C*layer.B
        max_per_layer.append([il, max_unrolling])
        if first:
            min_unrolling = max_unrolling
            layers_min = [il]
            first = False
        elif max_unrolling == min_unrolling:
            min_unrolling = max_unrolling
            layers_min.append(il)
        elif max_unrolling < min_unrolling:
            min_unrolling = max_unrolling
            layers_min = [il]

    return max_per_layer, [layers_min, min_unrolling]

def pixelwise_layer_spec(layers):
    pixelwise_layers = deepcopy(layers)
    for il,layer in enumerate(pixelwise_layers):
        layer.OX = 1
        layer.OY = 1
        layer.B *= layers[il].OX * layers[il].OY
        if layer.SX != 1:
            layer.B //= layers[il].SX
        if layer.SY != 1:
            layer.B //= layers[il].SY

    return pixelwise_layers

def pixelwise_layer_transform(layer_info, spatial_map):
    pixelwise_layer_info = {}
    for layer_index, layer in layer_info.items():
        percentage = 1
        if layer_index in spatial_map.map_list:
            percentage = spatial_map.map_list[layer_index].percentage
        pixelwise_layer_info[layer_index] = {'B': 1, 'K': 1, 'C': 1, 'OY': 1, 'OX': 1, 'FY': 1, 'FX': 1, 'SY': 1, 'SX': 1,
                                          'SFY': 1, 'SFX': 1, 'PY': 0, 'PX': 0}
        pixelwise_layer_info[layer_index]['B'] = round(percentage * layer['B'] * layer['OY'] * layer['OX'])
        if layer['SX'] != 1:
            pixelwise_layer_info[layer_index]['B'] //= layer['SX']
        if layer['SY'] != 1:
            pixelwise_layer_info[layer_index]['B'] //= layer['SY']
        pixelwise_layer_info[layer_index]['K'] = layer['K']
        pixelwise_layer_info[layer_index]['C'] = layer['C']
        pixelwise_layer_info[layer_index]['FX'] = layer['FX']
        pixelwise_layer_info[layer_index]['FY'] = layer['FY']
        pixelwise_layer_info[layer_index]['SX'] = layer['SX']
        pixelwise_layer_info[layer_index]['SY'] = layer['SY']
    return pixelwise_layer_info

def extract_map_info(layer_info, layer_indices, path):
    spatial_map = SpatialMapList(layer_indices, layer_info)
    spatial_map.load(path)
    spatial_map.load_extend(layer_info)
    return spatial_map

def map_data_extension(spatial_map_list,layer_info):
    '''
    Makes a new variable, which is the spatial map, but with all of the input data that is necessary to operate.
    This is done by extending the current map's boundary with a certain thickness, which is derived from the kernel size
    '''
    spatial_map_list_extended = deepcopy(spatial_map_list)
    spatial_map_list_extended = extend_map_list(spatial_map_list_extended, layer_info)
    spatial_map_reference = deepcopy(spatial_map_list_extended)
    for layer in spatial_map_reference.keys():
        map = spatial_map_reference[layer].map
        extend_factor = int((layer_info[layer]['FX'] - 1) / 2)

        #TODO: currently only unrolling over the points of the original map, but needs to be of all of the point + now need to add edge cases to has_neighbour
        for iy in range(extend_factor, spatial_map_reference[layer].size[1]-extend_factor):
            for ix in range(extend_factor, spatial_map_reference[layer].size[0]-extend_factor):
                if spatial_map_list_extended[layer].map[iy][ix] == 0:
                    if has_neighbour(map, extend_factor, ix, iy):
                        spatial_map_list_extended[layer].map[iy][ix] == 1
    return spatial_map_list_extended

def extend_map_list(map_list,layer_info):
    '''
    Extends the maps in map_list with zeros all around to accommodate for the input data size,
    this is done by extending with the required size according to the kernel size
    '''
    for layer in map_list.keys():
        assert layer_info[layer]['FX'] == layer_info[layer]['FY'], "Assymetrical kernel in layer %d" %(layer)
        extend_factor = int((layer_info[layer]['FX'] - 1)/2)
        [size_x, size_y] = [sum(x) for x in zip(map_list[layer].size, [2*extend_factor,2*extend_factor])]
        for ie in range(extend_factor):
            for iy in range(len(map_list[layer].map)):
                map_list[layer].map[iy].insert(0,0)
                map_list[layer].map[iy].append(0)
        for ie in range(extend_factor):
            map_list[layer].map.insert(0,size_x*[0])
            map_list[layer].map.append(size_x * [0])
        map_list[layer].size = [size_x, size_y]
    return map_list

def has_neighbour(map,extend_factor,ix,iy):
    '''
    checks whether withing the neighbourghood of size extend_factor of (ix,iy) there is a 1
    '''
    for ex in range(-extend_factor,extend_factor+1):
        for ey in range(extend_factor+1):
            if (map[iy+ey][ix+ex] == 1) or (map[iy-ey][ix+ex] == 1):
                return True
    return False