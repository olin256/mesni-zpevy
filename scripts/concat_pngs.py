from PIL import Image
import glob
import os
import numpy as np

skip = 90
margin_threshold = 5

def fill_f(*args, **kwargs):
    return 255*np.ones(*args, **kwargs)

for fn1 in glob.iglob("../png/*-1.png"):
    fn2 = fn1.replace("-1.png", "-2.png")

    num = fn1[-9:-6]

    imgs = [np.array(Image.open(fn).convert("L")) for fn in [fn1, fn2]]
    right_margins = []

    for img in imgs:
        sum = np.sum(1-img/255, axis=0)
        i = len(sum)-1
        while sum[i] < margin_threshold:
            i -= 1
        right_margins.append(len(sum)-i)

    target_right_margin = max(right_margins)
    for i in range(2):
        right_margin = right_margins[i]
        if right_margin < target_right_margin:
            imgs[i] = np.concatenate([imgs[i], fill_f((imgs[i].shape[0], target_right_margin-right_margin), dtype=np.uint8)], axis=1)

    target_width = max(img.shape[1] for img in imgs)
    for i in range(2):
        width = imgs[i].shape[1]
        if width < target_width:
            imgs[i] = np.concatenate([fill_f((imgs[i].shape[0], target_width-width), dtype=np.uint8), imgs[i]], axis=1)


    out_img = np.concatenate([imgs[0], fill_f((skip, target_width), dtype=np.uint8), imgs[1]], axis=0)

    out_img_obj = Image.fromarray(out_img.astype(np.uint8))

    out_img_obj.save("../png_concat/"+num+".png")