from time import time
from tensorflow.keras.preprocessing import image
import tensorflow as tf
import cv2
import os
import numpy as np
from pathlib import Path



def borrador(dir_path):
    # current_directory = Path(dir_path)
    # dir_text = Path(f'{current_directory}/texto')
    # dir_no_text = Path(f'{current_directory}/no_texto')
    # if not dir_text.exists():
    #     dir_text.mkdir()
    # if not dir_no_text.exists():
    #     dir_no_text.mkdir()
    model = tf.keras.models.load_model("./Segmentation_lite.h5",compile=False)

    for i in os.listdir(dir_path):
        img = image.load_img(dir_path+"//"+i, target_size=(128, 512))
        # plt.imshow(img)
        # plt.show()
        imagen = cv2.imread(dir_path+"//"+i)
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        images = np.vstack([x])
        images = images/255
        segmentado = model.predict(images)
        _, img = cv2.threshold(segmentado[0]*255, 180, 255, cv2.THRESH_BINARY)

        img = np.reshape(img, (128, 512, -1))
        img = img.astype(np.uint8)
        img = cv2.erode(img, np.ones((5, 15)), iterations=2)
        contours, _ = cv2.findContours(
            img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        flag = True
        for c in contours:
            area = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)
            # if area > 150 and area<35000 and h>25 and h<70 and x<360 and x+w>360:
            # if area > 15000  and area<65536:
            if area > 612 and area < 41718:
                flag = False


        if flag == True:
            os.remove(dir_path+"\\"+i)
# borrador(f"D:\\Programas de subtitulos\\Release_x64\\RGBImages")