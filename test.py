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



print()


# Go over the labeled objects and print out basic properties.
# for label in ann.labels:
#     print('Found label object: ' + label.obj_class.name)
#     print('   geometry type: ' + label.geometry.geometry_name())
#     print('   object area: ' + str(label.geometry.area))

#
new_img = Image.open(item_paths.img_path)
img_arr = numpy.array(new_img)
curr_label = ann.labels[0]

curr_geometry = curr_label.geometry

curr_x = curr_geometry.origin.row
curr_y = curr_geometry.origin.col

print(f'workin now with {curr_label.obj_class.name}')

new_img = sly.imaging.image.crop(img_arr,
                                 sly.Rectangle(curr_x, curr_y,
                                               curr_x + len(curr_geometry.data),
                                               curr_y + len(curr_geometry.data[0])))

im = Image.fromarray(new_img)
im.show()
