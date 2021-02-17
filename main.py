import importlib.machinery
import classes as cls
import matplotlib.pyplot as plt
import pickle
import help_funcs
import numpy as np
import input_funcs

#Init layer
layer_filename = 'NN_layers/ResNet101'
layer_number = [3]
layer_spec = importlib.machinery.SourceFileLoader('%s' % (layer_filename),
                                                  '%s.py' % (layer_filename)).load_module()
layers = [cls.Layer.extract_layer_info(layer_spec.layer_info[layer_number])
          for layer_number in layer_number]
if len(layer_number) > 1:
    raise Exception("Multiple layers asked, not yet implemented")
layer = layers[0]

#Init map
# f = open('map', 'rb')
# map = pickle.load(f)
# f.close

plt.imshow(map, cmap='Greys',  interpolation='nearest')
plt.show()

# TODO: import zigzag solution

help_funcs.max_pixelwise_unrolling(layers)
