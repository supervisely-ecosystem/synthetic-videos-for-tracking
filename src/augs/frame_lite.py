import imgaug.augmenters as iaa

seq = iaa.Sequential([
	iaa.Sometimes(0.5, iaa.blur.MotionBlur(k=(9, 21), angle=(0, 360), direction=(-1, 1), order=1))
], random_order=False)
