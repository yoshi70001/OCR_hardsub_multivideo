from time import time
from tensorflow.keras.preprocessing import image
import tensorflow as tf
import cv2
import os
import numpy as np
from pathlib import Path
import shutil

def borrador(dir_path):
    current_directory = Path(Path.cwd())
    dir_text=Path(f'{current_directory}/texto')
    dir_no_text=Path(f'{current_directory}/no_texto')
    if not dir_text.exists():
        dir_text.mkdir()
    if not dir_no_text.exists():
        dir_no_text.mkdir()
    model=tf.keras.models.load_model("./modelo_text.h5")

    for i in os.listdir(dir_path):
        img = image.load_img(dir_path+"//"+i,target_size=(50,360))
        # plt.imshow(img)
        # plt.show()
        imagen=cv2.imread(dir_path+"/"+i)
        x=image.img_to_array(img)
        x=np.expand_dims(x,axis=0)
        images = np.vstack([x])
        val=model.predict(images)
        if val==0:
            # print("0")
            # cv2.putText(imagen,"No texto",(50,25),cv2.FONT_HERSHEY_SIMPLEX,1.2,(0,255,0),2)
            os.remove(dir_path+"/"+i)
            # os.rename(dir_path+"/"+i,"no_texto"+"/"+str(time())+i)
        # else:
            # print("1")
            # cv2.putText(imagen,"Texto",(50,25),cv2.FONT_HERSHEY_SIMPLEX,1.2,(0,255,0),2)
            # os.rename(dir_path+"/"+i,"texto"+"/"+i)
            # shutil.copyfile(dir_path+"/"+i,"texto"+"/"+str(time())+i)
        