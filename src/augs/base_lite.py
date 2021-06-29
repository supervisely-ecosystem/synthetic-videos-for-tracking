import imgaug.augmenters as iaa

seq = iaa.Sequential([
	iaa.geometric.ScaleX(scale=(0.5, 1.5), order=1, cval=0, mode='constant', fit_output=True),
	iaa.geometric.ScaleY(scale=(0.5, 1.5), order=1, cval=0, mode='constant', fit_output=True),
	iaa.geometric.Rotate(rotate=(-180, 180), order=1, cval=0, mode='constant', fit_output=True)
], random_order=False)
