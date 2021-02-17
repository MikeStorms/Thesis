import classes as cls

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