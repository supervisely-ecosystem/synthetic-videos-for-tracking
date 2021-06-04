import supervisely_lib as sly  # Supervisely Python SDK
from PIL import Image
import numpy
from matplotlib import cm
import cv2

# Open existing project on disk.

# {'lemon': []}

project = sly.Project('./objects/lemons_annotated', sly.OpenMode.READ)
# Locate and load image labeling data.
item_paths = project.datasets.get('ds1').get_item_paths('IMG_0748.jpeg')
ann = sly.Annotation.load_json_file(item_paths.ann_path, project.meta)


# from matplotlib.pyplot import imread
#
# heart = imread(item_paths.ann_path, cv2.IMREAD_GRAYSCALE)
# _, mask = cv2.threshold(heart, thresh=180, maxval=255, type=cv2.THRESH_BINARY)


# Go over the labeled objects and print out basic properties.
# for label in ann.labels:
#     print('Found label object: ' + label.obj_class.name)
#     print('   geometry type: ' + label.geometry.geometry_name())
#     print('   object area: ' + str(label.geometry.area))

#
# label_0 = ann.labels[0]
#
# figure = sly.Bitmap(label_0.geometry.data)
# print(item_paths)
#
# img = Image.open(item_paths.img_path)
# img_arr = numpy.array(img)
#
# new_img = sly.imaging.image.crop(img_arr, )
#
#

# im = Image.fromarray(new_img)
# im.show()

import numpy as np
from matplotlib import pyplot as plt


img = sly.image.read(item_paths.img_path)

ann_render = np.zeros(ann.img_size + (3,), dtype=np.uint8)

ann.draw(ann_render)

# binary_image = Image.fromarray(ann_render).convert('LA')
# img_arr = numpy.array(binary_image)


gray_image = cv2.cvtColor(ann_render, cv2.COLOR_BGR2GRAY)

_, mask = cv2.threshold(gray_image, thresh=1, maxval=255, type=cv2.THRESH_BINARY)


print(mask.shape)
temple_x, temple_y, _ = img.shape
heart_x, heart_y = mask.shape
#
x_heart = min(temple_x, heart_x)
x_half_heart = mask.shape[0]//2

heart_mask = mask[x_half_heart-x_heart//2 : x_half_heart+x_heart//2+1, :temple_y]

temple_width_half = img.shape[1]//2
temple_to_mask = img[:, temple_width_half-x_half_heart:temple_width_half+x_half_heart]

masked = cv2.bitwise_and(temple_to_mask, temple_to_mask, mask=heart_mask)
plt.imshow(masked)
plt.show()
