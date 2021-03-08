import classes as cls
from copy import deepcopy
import pickle
import create_map

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

class InputBufferConfig():
    def __init__(self, points_visited, points_stored, cum_count):
        self.points_visited = points_visited
        self.points_stored = points_stored
        self.cum_count = cum_count


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
    buffer = 200
    optimal_spatial_mapping_search(spatial_map.map_list[3].map, spatial_map.map_list_input[3].map, buffer, 1)

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
        for iy in range(spatial_map_reference[layer].size[1]):
            for ix in range(spatial_map_reference[layer].size[0]):
                if spatial_map_list_extended[layer].map[iy][ix] == 0:
                    if has_neighbour(map, extend_factor, ix, iy, spatial_map_reference[layer].size):
                        spatial_map_list_extended[layer].map[iy][ix] = 1
        f = open('map_1', 'wb')
        pickle.dump(spatial_map_list_extended[layer].map, f, 2)
        f.close
        f = open('map_2', 'wb')
        pickle.dump(spatial_map_reference[layer].map, f, 2)
        f.close
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

def has_neighbour(map, extend_factor, ix, iy, size):
    '''
    checks whether withing the neighbourghood of size extend_factor of (ix,iy) there is a 1
    '''
    lowerbound_x = -extend_factor
    upperbound_x = extend_factor+1
    lowerbound_y = -extend_factor
    upperbound_y = extend_factor+1
    if ix < extend_factor:
        for i in range(extend_factor):
            lowerbound_x += 1
    elif ix > size[0] - extend_factor - 1:
        for i in range(extend_factor):
            upperbound_x -= 1

    if iy < extend_factor:
        for i in range(extend_factor):
            lowerbound_y += 1
    elif iy > size[1] - extend_factor - 1:
        for i in range(extend_factor):
            upperbound_y -= 1

    for ex in range(lowerbound_x, upperbound_x):
        for ey in range(lowerbound_y, upperbound_y):
            if map[iy+ey][ix+ex] == 1:
                return True
    return False

def optimal_spatial_mapping_search(output_map, input_map, buffer_size, extend_factor):

    max_points_visited = 0
    best_configs = []
    for iy in range(len(output_map)):
        for ix in range(len(output_map[0])):
            if output_map[iy][ix] == 1:
                cum_count = 0
                points_stored = [[0 for i in range(len(input_map[0]))] for j in range(len(input_map))]
                points_visited = [[0 for i in range(len(output_map[0]))] for j in range(len(output_map))]
                possible_configs = recursive_search(output_map, input_map, points_stored, points_visited, buffer_size, cum_count, ix, iy, extend_factor)
                for ib, config in enumerate(possible_configs):
                    current_points_visited = sum([sum(x) for x in config.points_visited])
                    if current_points_visited == max_points_visited:
                        best_configs.append(config)
                    elif current_points_visited > max_points_visited:
                        max_points_visited = current_points_visited
                        best_configs = [config]


def recursive_search(output_map, input_map, points_stored, points_visited, buffer_size, cum_count, ix, iy, extend_factor):
    if sum([sum(x) for x in points_stored]) != cum_count:
        print('fault')
    #init
    prev_cum_count = deepcopy(cum_count)
    prev_points_stored = deepcopy(points_stored)
    prev_points_visited = deepcopy(points_visited)

    #fill in
    points_visited[iy][ix] = 1

    lowerbound_x = -extend_factor
    upperbound_x = extend_factor + 1
    lowerbound_y = -extend_factor
    upperbound_y = extend_factor + 1

    for ex in range(lowerbound_x, upperbound_x):
        for ey in range(lowerbound_y, upperbound_y):
            if points_stored[iy+extend_factor+ey][ix+extend_factor+ex] == 0:
                cum_count += 1
                points_stored[iy+extend_factor+ey][ix+extend_factor+ex] = 1

    #evaluate
    if cum_count > buffer_size:
        return InputBufferConfig(prev_points_visited, prev_points_stored, sum([sum(x) for x in prev_points_stored]))
    #search for next point
    lowerbound_x = -1
    upperbound_x = 2
    lowerbound_y = -1
    upperbound_y = 2
    if ix == 0:
        lowerbound_x = 0
    elif ix == len(output_map[0])-1:
        upperbound_x = 1

    if iy == 0:
        lowerbound_y = 0
    elif iy == len(output_map)-1:
        upperbound_y = 1

    current_buffer_list = []
    for ex in range(lowerbound_x, upperbound_x):
        for ey in range(lowerbound_y, upperbound_y):
            if output_map[iy+ey][ix+ex] == 1 and points_visited[iy+ey][ix+ex] == 0:
                new_buffer_list = recursive_search(output_map, input_map, points_stored, points_visited, buffer_size, cum_count, ix+ex, iy+ey, extend_factor)
                if type(new_buffer_list) == list:
                    for buffer in new_buffer_list:
                        current_buffer_list.append(buffer)
                else:
                    current_buffer_list.append(new_buffer_list)

    return current_buffer_list