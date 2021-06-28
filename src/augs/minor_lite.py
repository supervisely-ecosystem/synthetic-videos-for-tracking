import imgaug.augmenters as iaa

seq = iaa.Sequential([
	iaa.geometric.Rotate(rotate=(-16, 16), order=1, cval=0, mode='constant', fit_output=True),
	iaa.color.AddToBrightness(add=(-8, 8), to_colorspace='YCrCb', from_colorspace='RGB'),
	iaa.color.AddToHue(value=(-8, 8))
], random_order=False)
