import imgaug.augmenters as iaa



def get_transforms(augs_dict):
    return augs_dict['Base'], augs_dict['Minor'], augs_dict['Frame']

#
# def get_transforms(i):
#     div = 0.02 * i  # magic formula for correct transforms
#
#     general_transform = iaa.Sequential([
#         iaa.Sometimes(0.3, iaa.Resize((1 - div * 2, 1 + div * 2), interpolation='cubic')),
#         # iaa.Rot90((1, 4), keep_size=False),
#         # iaa.Rotate(rotate=(-5 - i * 5, 5 + i * 5), fit_output=True)
#     ])
#
#     minor_transform = iaa.Sequential([
#         # iaa.Affine(rotate=(-5 - i, 5 + i)),
#         iaa.Resize((1 - div * 1.2, 1 + div * 1.2)),
#         # iaa.Rotate(rotate=(-45 - i * 5, 45 + i * 5), fit_output=True),
#         iaa.Rotate(rotate=(-10, 10), fit_output=True),
#         # iaa.Fliplr(p=0.5),
#         # iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
#         iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
#         # iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 1.5)),
#         iaa.MotionBlur(k=(10, int(20 + i * 1.5)))
#         # iaa.ElasticTransformation(alpha=90, sigma=9),
#     ])
#
#     frame_transform = iaa.Sometimes(0.3, iaa.Sequential([
#         iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
#         iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
#         # iaa.Rotate(rotate=(-4, 4), fit_output=True),
#         iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 2)),
#         iaa.MotionBlur(k=(10, int(20 + i * 1.5)))
#         # iaa.ElasticTransformation(alpha=90, sigma=9),
#     ]))
#
#     return general_transform, minor_transform, frame_transform

