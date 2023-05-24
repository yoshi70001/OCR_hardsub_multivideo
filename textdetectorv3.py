import onnxruntime as rt
from pathlib import Path

import datetime
import cv2
import os
from re import sub
import numpy as np
from concurrent.futures import ThreadPoolExecutor


excutor = ThreadPoolExecutor(max_workers=2)


sess= rt.InferenceSession('9-5-23.onnx')
input_name = sess.get_inputs()[0].name
label_name = sess.get_outputs()[0].name


#boxes
sess2= rt.InferenceSession('RCNN_600k3_10k.onnx')
input_name2 = sess2.get_inputs()[0].name
label_name2 = sess2.get_outputs()[0].name




def filtradoNombre(nombre):
    x = sub(r"\.avi$", "", nombre)
    x = sub(r"\.mp4$", "", x)
    x = sub(r"\.mkv$", "", x)
    return x


def times(contador, fps):
    td = datetime.timedelta(seconds=((contador)/fps))
    ms = td.microseconds // 1000
    m, s = divmod(td.seconds, 60)
    h, m = divmod(m, 60)
    return '{:02d}_{:02d}_{:02d}_{:03d}'.format(h, m, s, ms)


def guardarImagen(videofile,temp,aux,temp_img):
    cv2.imwrite(filtradoNombre(videofile.name) +"/"+temp+"__"+aux+".jpeg", temp_img)

def imgExtractor(videofile):
    video = cv2.VideoCapture(str(videofile.path))
    image_dir = Path(f'{Path(Path.cwd())}/'+filtradoNombre(videofile.name))
    if not image_dir.exists():
        os.mkdir(filtradoNombre(videofile.name))
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    print(fps)
    counter = 1
    step = 0
    aux = ""
    temp_img = [1]
    mask_temp = []
    tempVal=0
    while counter <= total_frames:
        _, img = video.read()
        
        if counter % int(fps/6) == 0:
            img = img[int(img.shape[0]/1.3):, :, :]
            imagen2 = img.copy()
            #imagen3 = img.copy()
            img = cv2.resize(img, (256, 64), interpolation=cv2.INTER_AREA)
            img2 = img
            x = img.astype(np.float32)
            x = np.expand_dims(x, axis=0)
            images = np.vstack([x])
            val = sess.run([label_name],{input_name:images})
            val = np.array(val[0][0],dtype=np.int8)
            if val[0] != 1:
                if step > 0:
                    temp = aux
                    aux = times(counter-1, fps)
                    
                    #print(temp+"__"+aux)
                    excutor.submit(guardarImagen,videofile,temp,aux,temp_img)
                    imagen2 = []
                    step = 0
                    
            else:
                
                if step == 0:
                    aux = times(counter-1, fps)
                    temp_img = imagen2
                    step += 1
                else:
                    img2 = img2.astype(np.float32)
                    img2 = np.expand_dims(img2, axis=0)
                    img2 = np.vstack([img2])
                    val2 = sess2.run([label_name2],{input_name2:img2})
                    _,val2=cv2.threshold(val2[0][0]*255,20,255,cv2.THRESH_BINARY)
                    val2=np.reshape(val2,(64,256,-1))
                    val2=val2.astype(np.uint8)
                    #val2=cv2.dilate(val2,np.ones((3,3)),iterations=3)
                    #cv2.imshow("test2",val2)
                    if len(mask_temp)==0:
                        mask_temp=val2
                    res=cv2.absdiff(mask_temp,val2)
                    res = res.astype(np.uint8)
                    percentage = (np.count_nonzero(res) * 100)/ res.size
                    #print(percentage)
                    if  percentage>10 :
                        #print(percentage)
                        temp = aux
                        aux = times(counter-1, fps)                       
                        #print(temp+"__"+aux)
                        excutor.submit(guardarImagen,videofile,temp,aux,temp_img)
                        imagen2 = []
                        step = 0                    
                    cv2.imshow("diff",cv2.hconcat([mask_temp,val2,res]))
                    mask_temp=val2
                    
            cv2.imshow("test",img)
            cv2.waitKey(1)
        counter += 1
    # excutor.shutdown(wait=True)