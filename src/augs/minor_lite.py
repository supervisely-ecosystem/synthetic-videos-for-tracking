import imgaug.augmenters as iaa

seq = iaa.Sequential([
	iaa.geometric.Rotate(rotate=(-15, 15), fit_output=True),
	iaa.color.AddToBrightness(add=(-8, 8), to_colorspace='YCrCb', from_colorspace='RGB'),
	iaa.color.AddToHue(value=(-8, 8))
], random_order=False)
