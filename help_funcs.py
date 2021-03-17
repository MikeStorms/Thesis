import classes as cls
from copy import deepcopy
import pickle
import bsgutils
import itertools


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
        self.linewise_edges = []

    def isolate_layer(self, layer_index):
        self.average_factors = self.average_factors[layer_index]
        self.edge_maps = self.edge_maps[layer_index]
        self.map_list = self.map_list[layer_index]
        self.serial_load_map = self.serial_load_map[layer_index]

    def load(self, path):
        for index in self.map_list:
            self.map_list[index].load(path + "_%d" % (index))

    def load_extend(self, layer_info):
        self.map_list_input = spatial_map_extension(self.map_list, layer_info)

    def load_linewise_edges(self, layer_info, layer_indices):
        # linewise_edges only used for the simulations in linewise_operation
        self.linewise_edges = linewise_edges_approx(self.map_list, layer_info)
        [average_factors, edge_maps, serial_load_map] = get_average_factors(self.map_list, self.map_list_input, self.linewise_edges, layer_info)
        self.average_factors = average_factors
        self.edge_maps = edge_maps
        self.serial_load_map = serial_load_map


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
    '''
    Switches the specification to a pixelwise specification
    :param layers:
    :return:
    '''
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
    '''
    Converges the layer_info into pixelwise layer info
    :param layer_info:
    :param spatial_map:
    :return:
    '''
    pixelwise_layer_info = {}
    for layer_index, layer in layer_info.items():
        assert layer['B'] == 1, "Error: B is not 1 in layer %i" %(layer_index)
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
    spatial_map.load_linewise_edges(layer_info, layer_indices)
    buffer = 200
    # [average_factor, average_factor_edges] = linewise_operation(spatial_map.map_list_input[3].map, spatial_map.map_list[3].map, buffer, 1, spatial_map.linewise_edges[3].map)
    return spatial_map


def spatial_map_extension(spatial_map_list,layer_info):
    '''
    ONLY IS USED FOR THE SIMULATION OF THE VISUALISATION,
    Inputs are SpatialMaps, not arrays
    
    Makes a new variable, which is the spatial map, but with all of the input data that is necessary to operate.
    This is done by extending the current map's boundary with a certain thickness, which is derived from the kernel size
    '''
    spatial_map_list_extended = deepcopy(spatial_map_list)
    spatial_map_list_extended = extend_spatial_map(spatial_map_list_extended, layer_info)
    spatial_map_reference = deepcopy(spatial_map_list_extended)
    for layer in spatial_map_reference.keys():
        map = spatial_map_reference[layer].map
        if map == []:
            continue
        extend_factor = int((layer_info[layer]['FX'] - 1) / 2)
        for iy in range(spatial_map_reference[layer].size[1]):
            for ix in range(spatial_map_reference[layer].size[0]):
                if spatial_map_list_extended[layer].map[iy][ix] == 0:
                    if has_neighbour(map, extend_factor, ix, iy, spatial_map_reference[layer].size):
                        spatial_map_list_extended[layer].map[iy][ix] = 1
        # f = open('map_1', 'wb')
        # pickle.dump(spatial_map_list_extended[layer].map, f, 2)
        # f.close
        # f = open('map_2', 'wb')
        # pickle.dump(spatial_map_reference[layer].map, f, 2)
        # f.close
    return spatial_map_list_extended


def map_extension(input_map, extend_kernel_x, extend_kernel_y, max_kernel_x, max_kernel_y):
    input_map_copy = deepcopy(input_map)
    input_map_extended = extend_map(input_map_copy, max_kernel_x, max_kernel_y)
    if (extend_kernel_x == 1) & (extend_kernel_y == 1):
        return input_map_extended
    input_map_reference = deepcopy(input_map_extended)
    extend_factor_x = int((extend_kernel_x - 1) / 2)
    extend_factor_y = int((extend_kernel_y - 1) / 2)
    for iy in range(len(input_map_reference)):
        for ix in range(len(input_map_reference[0])):
            if input_map_reference[iy][ix] == 1:
                for ey in range(-extend_factor_y, extend_factor_y + 1):
                    for ex in range(-extend_factor_x, extend_factor_x + 1):
                        input_map_extended[iy+ey][ix+ex] = 1
    return input_map_extended


def extend_spatial_map(map_list,layer_info):
    '''
    ONLY USED FOR SIMULATION
    Input is a SpatialMap, not a list

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


def extend_map(map, max_kernel_x, max_kernel_y):
    extend_factor_x = int((max_kernel_x - 1)/2)
    extend_factor_y = int((max_kernel_y - 1) / 2)
    [size_x, size_y] = [sum(x) for x in zip([len(map), len(map[0])], [2*extend_factor_x, 2*extend_factor_y])]
    for ie in range(extend_factor_x):
        for iy in range(len(map)):
            map[iy].insert(0, 0)
            map[iy].append(0)
    for ie in range(extend_factor_y):
        map.insert(0, size_x*[0])
        map.append(size_x * [0])
    return map


def linewise_edges_approx(spatial_map_list, layer_info):
    '''
    Outputs a map with all the pixels that can be thaught of as edges, meaning that they would require more BW than usual
    to load do to not having a data dependency
    :param spatial_map_list:
    :param layer_info:
    :return:
    '''
    linewise_edge_layers = deepcopy(spatial_map_list)
    for layer in spatial_map_list.keys():
        assert layer_info[layer]['FX'] == layer_info[layer]['FY'], "Assymetrical kernel in layer %d" % (layer)
        if layer_info[layer]['FX'] == 1:
            linewise_edge_layers[layer].map = []
            linewise_edge_layers[layer].percentage = 0
            continue
        map = spatial_map_list[layer].map
        layer_linewise_edge = [[0 for i in range(len(map[0]))] for j in range(len(map))]
        for iy in range(len(map)):
            for ix in range(len(map[0])):
                if map[iy][ix] == 1:
                    second_point_poss = layer_info[layer]['FX']
                    if ix > len(map) - layer_info[layer]['FX']:
                        second_point_poss = len(map) - ix
                    if map[iy][ix-1] == 0 or iy == 0:
                        layer_linewise_edge[iy][ix] = 1
                    else:
                        second_point_good = 0
                        for ex in range(second_point_poss):
                            if map[iy-1][ix+ex] == 1:
                                second_point_good = 1
                        if not(second_point_good):
                            layer_linewise_edge[iy][ix] = 1
        linewise_edge_layers[layer].map = layer_linewise_edge

        # f = open('map_edges', 'wb')p
        # pickle.dump(layer_linewise_edge, f, 2)
        # f.close
    return linewise_edge_layers


def linewise_edges_map(spatial_map, FX, FY):
    x_check = 1
    y_check = FX
    layer_linewise_edge = [[0 for i in range(len(spatial_map[0]))] for j in range(len(spatial_map))]
    if (FX == 1) & (FY == 1):
        return []
    if FX == 1:
        x_check = 0
        y_check = 1
    if FY == 1:
        y_check = 0
    for iy in range(len(spatial_map)):
        for ix in range(len(spatial_map[0])):
            if spatial_map[iy][ix] == 1:
                x_valid = 0
                y_valid = 0
                if x_check:
                    if spatial_map[iy][ix - 1] == 1:
                        x_valid = 1
                else:
                    x_valid = 1
                if y_check != 0:
                    if (y_check > 1) & (ix > len(spatial_map[0]) - FX):
                        y_check_adjusted = len(spatial_map[0]) - ix
                    else:
                        y_check_adjusted = y_check
                    for ex in range(y_check_adjusted):
                        if spatial_map[iy - 1][ix + ex] == 1:
                            y_valid = 1
                else:
                    y_valid = 1
                if not(x_valid & y_valid):
                    layer_linewise_edge[iy][ix] = 1

    return layer_linewise_edge


def linewise_edged_extended(linewise_edges, layer_info, layer_indices):
    edges_map = SpatialMapList(layer_indices, layer_info)
    for layer in layer_indices:
        edges_map.map_list[layer] = linewise_edges[layer]
    edges_extended = spatial_map_extension(edges_map.map_list, layer_info)
    return edges_extended


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
    '''
    tries to find the optimal buffer path to maximally utilize the input data reuse by recursively searching
    for all the different paths and choosing the one that where we can operate the maximal number of points from
    output_map, while storing all the necessary input data inside buffer_size
    Buffer_size is in elements, not bits
    '''
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
    '''
    :param output_map:
    :param input_map:
    :param points_stored:
    :param points_visited:
    :param buffer_size:
    :param cum_count:
    :param ix:
    :param iy:
    :param extend_factor:
    :return:

    recursively searches for the best path from point [ix,iy] by starting the same search in all neighbouring points
    that can still fit inside the buffer
    '''
    if sum([sum(x) for x in points_stored]) != cum_count:
        print('fault')
    #init
    prev_cum_count = deepcopy(cum_count)
    prev_points_stored = deepcopy(points_stored)
    prev_points_visited = deepcopy(points_visited)

    current_cum_count = deepcopy(cum_count)
    current_points_stored = deepcopy(points_stored)
    current_points_visited = deepcopy(points_visited)

    # fill in
    current_points_visited[iy][ix] = 1

    lowerbound_x = -extend_factor
    upperbound_x = extend_factor + 1
    lowerbound_y = -extend_factor
    upperbound_y = extend_factor + 1

    for ex in range(lowerbound_x, upperbound_x):
        for ey in range(lowerbound_y, upperbound_y):
            if current_points_stored[iy+extend_factor+ey][ix+extend_factor+ex] == 0:
                current_cum_count += 1
                current_points_stored[iy+extend_factor+ey][ix+extend_factor+ex] = 1

    if cum_count == 198:
        print('stop')
    # evaluate
    if current_cum_count > buffer_size:
        return InputBufferConfig(prev_points_visited, prev_points_stored, sum([sum(x) for x in prev_points_stored]))
    # search for next point
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
                new_buffer_list = recursive_search(output_map, input_map, current_points_stored, current_points_visited, buffer_size, current_cum_count, ix+ex, iy+ey, extend_factor)
                if type(new_buffer_list) == list:
                    for buffer in new_buffer_list:
                        current_buffer_list.append(buffer)
                else:
                    current_buffer_list.append(new_buffer_list)

    return current_buffer_list


def lengthen_dict(dict, extension_coeff):
    for ex in range(extension_coeff):
        dict[len(dict) + ex + 1] = 0


def linewise_operation(input_map, output_map, buffer_size, extend_factor, edge_map):
    current_buffer_map = [[0 for i in range(len(input_map[0]))] for j in range(len(input_map))]
    current_buffer_size = 0
    cycles = [[0 for i in range(len(output_map[0]))] for j in range(len(output_map))]
    buffer_map = [[0 for i in range(len(output_map[0]))] for j in range(len(output_map))]
    edge_cycles = []
    buffer_index = 1
    buffer_elements_deterministic = {}
    buffer_elements_deterministic[1] = 0
    lowerbound_x = -extend_factor
    upperbound_x = extend_factor + 1
    lowerbound_y = -extend_factor
    upperbound_y = extend_factor + 1

    for iy in range(len(output_map)):
        for ix in range(len(output_map[0])):
            if output_map[iy][ix] == 1:
                cycles_per_pixel = 0
                buffer_increase = 0
                for ex in range(lowerbound_x, upperbound_x):
                    for ey in range(lowerbound_y, upperbound_y):
                        if current_buffer_map[iy + extend_factor + ey][ix + extend_factor + ex] == 0:
                            current_buffer_map[iy + extend_factor + ey][ix + extend_factor + ex] = 1
                            buffer_increase += 1
                            cycles_per_pixel += 1
                if (current_buffer_size + buffer_increase) > buffer_size:
                    buffer_index += 1
                    buffer_elements_deterministic[buffer_index] = 0
                    current_buffer_size = buffer_increase
                else:
                    current_buffer_size += buffer_increase
                cycles[iy][ix] = cycles_per_pixel
                buffer_map[iy][ix] = buffer_index
                buffer_elements_deterministic[buffer_index] += 1
                if edge_map[iy][ix] == 1:
                    edge_cycles.append(cycles_per_pixel)
    buffer_map_deterministic = deepcopy(buffer_map)
    # f = open('map_deterministic', 'wb')
    # pickle.dump(buffer_map_deterministic, f, 2)
    # f.close

    # Stochastic part
    current_buffer_size = 0
    buffer_map = [[0 for i in range(len(output_map[0]))] for j in range(len(output_map))]
    buffer_index = 1
    buffer_elements_stochastic = {}
    buffer_elements_stochastic[1] = 0
    average_factor = sum([sum(x) for x in input_map])/sum([sum(x) for x in output_map])
    for iy in range(len(output_map)):
        for ix in range(len(output_map[0])):
            if output_map[iy][ix] == 1:
                if (current_buffer_size + average_factor) > buffer_size:
                    buffer_index += 1
                    buffer_elements_stochastic[buffer_index] = 0
                    current_buffer_size = average_factor
                else:
                    current_buffer_size += average_factor
                buffer_map[iy][ix] = buffer_index
                buffer_elements_stochastic[buffer_index] += 1


    buffer_map_stochastic = deepcopy(buffer_map)
    # f = open('map_stochastic', 'wb')
    # pickle.dump(buffer_map_stochastic, f, 2)
    # f.close

    # Stochastic with edges
    current_buffer_size = 0
    buffer_map = [[0 for i in range(len(output_map[0]))] for j in range(len(output_map))]
    buffer_index = 1
    buffer_elements_stochastic_edges = {}
    buffer_elements_stochastic_edges[1] = 0
    total_data = sum([sum(x) for x in input_map])
    total_pixels = sum([sum(x) for x in output_map])
    number_edge_cases = sum([sum(x) for x in edge_map])
    average_factor_edge = (total_data - (total_pixels - number_edge_cases)) / number_edge_cases
    for iy in range(len(output_map)):
        for ix in range(len(output_map[0])):
            if output_map[iy][ix] == 1:
                if edge_map[iy][ix] == 1:
                    average_factor = average_factor_edge
                else:
                    average_factor = 1
                if (current_buffer_size + average_factor) > buffer_size:
                    buffer_index += 1
                    buffer_elements_stochastic_edges[buffer_index] = 0
                    current_buffer_size = average_factor
                else:
                    current_buffer_size += average_factor
                buffer_map[iy][ix] = buffer_index
                buffer_elements_stochastic_edges[buffer_index] += 1

    buffer_map_stochastic_edge = deepcopy(buffer_map)
    # f = open('map_stochastic_edges', 'wb')
    # pickle.dump(buffer_map_stochastic_edge, f, 2)
    # f.close

    # equalize the buffer sizes for further comparison
    lengths = [len(buffer_elements_deterministic), len(buffer_elements_stochastic), len(buffer_elements_stochastic_edges)]
    extension_buffer = [max(lengths) - x for x in lengths]
    lengthen_dict(buffer_elements_deterministic, extension_buffer[0])
    lengthen_dict(buffer_elements_stochastic, extension_buffer[1])
    lengthen_dict(buffer_elements_stochastic_edges, extension_buffer[2])

    difference_stochastic = [buffer_elements_deterministic[x] - buffer_elements_stochastic[x] for x in buffer_elements_deterministic.keys()]
    difference_stochastic_edges = [buffer_elements_deterministic[x] - buffer_elements_stochastic_edges[x] for x in buffer_elements_deterministic.keys()]
    MSE_stochastic = sum([x ** 2 for x in difference_stochastic])/len(difference_stochastic)
    MSE_stochastic_edges = sum([x ** 2 for x in difference_stochastic_edges])/len(difference_stochastic_edges)
    return [average_factor, average_factor_edge]


def average_factor_edges(input_map, output_map, edge_map):
    if edge_map == []:
        return 1
    total_data = sum([sum(x) for x in input_map])
    total_pixels = sum([sum(x) for x in output_map])
    number_edge_cases = sum([sum(x) for x in edge_map])
    average_factor = (total_data - (total_pixels - number_edge_cases)) / number_edge_cases
    return average_factor


def get_combinations(list1, list2):
    '''
    makes all popssible combinations with the restrain that the elements need to come from the respective list
    :param list1:
    :param list2:
    :return:
    '''
    comb = []
    for i in list1:
        for j in list2:
            comb.append([i, j])
    return comb


def get_average_factors(map_list, map_list_input, linewise_edges, layer_info):
    average_factors = {}
    edge_maps = {}
    serial_load_map = {}
    for layer in map_list.keys():
        max_FX = layer_info[layer]['FX']
        max_FY = layer_info[layer]['FY']
        FX_pf = bsgutils.prime_factors(max_FX)
        FY_pf = bsgutils.prime_factors(max_FY)
        FX_pf.insert(0, 1)
        FY_pf.insert(0, 1)
        kernel_comb = get_combinations(FX_pf, FY_pf)

        average_factors[layer] = {}
        edge_maps[layer] = {}
        serial_load_map[layer] = {}
        for comb in kernel_comb:
            extension_x = max_FX - (comb[0] - 1)
            extension_y = max_FY - (comb[1] - 1)
            output_data_map = map_extension(map_list[layer].map, extension_x, extension_y, max_FX, max_FY)
            edge_map = linewise_edges_map(output_data_map, comb[0], comb[1])
            factor = average_factor_edges(map_list_input[layer].map, output_data_map, edge_map)
            serial_load_map[layer][str(comb)] = get_serial_load_map(output_data_map, edge_map, factor)
            average_factors[layer][str(comb)] = factor
            edge_maps[layer][str(comb)] = edge_map
    return [average_factors, edge_maps, serial_load_map]


def get_serial_load_map(map, edge_map, average_factor):
    if average_factor == 1:
        return sum([sum(x) for x in map])*[1]
    serial_load_map = []
    for iy in range(len(map)):
        for ix in range(len(map[0])):
            if map[iy][ix] == 1:
                if edge_map[iy][ix] == 1:
                    serial_load_map.append(average_factor)
                else:
                    serial_load_map.append(1)
    return serial_load_map


def calc_input_data_pixelwise_data_reuse(fx, fy, c, spatial_map, pixelwise_temporal_unrolling, pixelwise_spatial_unrolling):
    kernel = [fx, fy]
    serial_load_map = spatial_map.serial_load_map[str(kernel)]
    total_unrolling = pixelwise_temporal_unrolling * pixelwise_spatial_unrolling
    # if (total_unrolling > 10) & (total_unrolling < 100):
    #     print('B')
    split_up_load_map = [serial_load_map[i * total_unrolling:(i + 1) * total_unrolling] for i in range((len(serial_load_map) + total_unrolling - 1) // total_unrolling )]
    sum_load_map = [sum(x) for x in split_up_load_map]
    max_size_I = max(sum_load_map) * c
    return max_size_I