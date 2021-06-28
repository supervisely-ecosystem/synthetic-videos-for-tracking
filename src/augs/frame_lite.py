import imgaug.augmenters as iaa

seq = iaa.Sequential([
	iaa.Sometimes(0.6, iaa.imgcorruptlike.GaussianNoise(severity=(1, 3)))
], random_order=False)
