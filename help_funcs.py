import classes as cls
from copy import deepcopy

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

def pixelwise_layer_transform(layer_info):
    pixelwise_layer_info = {}
    for layer_index, layer in layer_info.items():
        pixelwise_layer_info[layer_index] = {'B': 1, 'K': 1, 'C': 1, 'OY': 1, 'OX': 1, 'FY': 1, 'FX': 1, 'SY': 1, 'SX': 1,
                                          'SFY': 1, 'SFX': 1, 'PY': 0, 'PX': 0}
        pixelwise_layer_info[layer_index]['B'] = layer['B'] * layer['OY'] * layer['OX']
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