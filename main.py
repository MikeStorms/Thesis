import importlib.machinery
import classes as cls
import matplotlib.pyplot as plt
import pickle
import conv1
import numpy as np

#Init layer
layer_filename = 'NN_layers/ResNet34'
layer_number = [3]
layer_spec = importlib.machinery.SourceFileLoader('%s' % (layer_filename),
                                                  '%s.py' % (layer_filename)).load_module()
layers = [cls.Layer.extract_layer_info(layer_spec.layer_info[layer_number])
          for layer_number in layer_number]
if len(layer_number) > 1:
    raise Exception("Multiple layers asked, not yet implemented")
layer = layers[0]

#Init map
f = open('map', 'rb')
map = pickle.load(f)
f.close

plt.imshow(map, cmap='Greys',  interpolation='nearest')
plt.show()

# TODO: import zigzag solution

#implementation of 1x1 pointwise convolutions
if layer.FX == 1 & layer.FY == 1:
    # Do 1x1 convolution of current layer
    # Do this for regular, + spatially sparse, + line buffered, + depth first
elif layer.FX == 3 & layer.FY == 3:
    # Do 3x3 convolution of current layer
    # Do this for regular, + spatially sparse, + line buffered, + depth first

# Note:
# Does this need