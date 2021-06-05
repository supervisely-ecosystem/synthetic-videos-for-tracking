import cv2
import numpy


def add_object_to_background(background, overlay, x, y):

    background_width = background.shape[1]
    background_height = background.shape[0]

    if x >= background_width or y >= background_height:
        return background

    h, w = overlay.shape[0], overlay.shape[1]

    if x + w > background_width:
        w = background_width - x
        overlay = overlay[:, :w]

    if y + h > background_height:
        h = background_height - y
        overlay = overlay[:h]

    if overlay.shape[2] < 4:
        overlay = numpy.concatenate(
            [
                overlay,
                numpy.ones((overlay.shape[0], overlay.shape[1], 1), dtype = overlay.dtype) * 255
            ],
            axis=2,
        )

    overlay_image = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0

    background[y:y+h, x:x+w] = (1.0 - mask) * background[y:y+h, x:x+w] + mask * overlay_image
    cv2.imwrite('combined2.png', background)

    return background


def generate_frames():
    ###
    frames = []
    for counter in range(0, 500, 5):
        frames.append(add_object_to_background(self.backgrounds[0].copy(), self.objects[1].image, counter, counter))

    pass


def write_frames_to_file():
    ###
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_shape = (self.backgrounds[0].shape[1], self.backgrounds[0].shape[0])

    # print(self.backgrounds[0].shape[:2])
    video = cv2.VideoWriter('test2.mp4', fourcc, 60, video_shape)

    for frame in tqdm(frames):
        video.write(frame)

    video.release()

