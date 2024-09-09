import cv2
import numpy as np
from libs.imgOcr import ocrImg
model = cv2.dnn.readNetFromONNX('models/model.onnx')
model.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
model.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)

def imageExtractor(videoPath,videoName):
    cap = cv2.VideoCapture(videoPath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frameCounter = 1
    while cap.isOpened():
        existFrame, frame = cap.read()
        if not existFrame:
            break
        if frameCounter % int(fps/7)==0:
            resizedFrame = cv2.resize(frame,(224,224),interpolation=cv2.INTER_AREA)
            blobResizedFrame=cv2.dnn.blobFromImage(resizedFrame)/255
            model.setInput(blobResizedFrame)
            inferedFrame = model.forward()[0]*255
            inferedFrame = np.transpose(inferedFrame,(1,2,0))
            _,inferedFrame= cv2.threshold(inferedFrame,30,255,cv2.THRESH_BINARY)
            inferedFrameEroded = cv2.erode(inferedFrame,np.ones((5,10)),iterations=2)
            inferedFrameEroded= np.uint8(inferedFrameEroded)
            inferedFrameEroded = cv2.bitwise_not(inferedFrameEroded)
            contours, hierarchy=cv2.findContours(inferedFrameEroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x,y,w,h = cv2.boundingRect(contour)
                if h>7 and y >112:
                    area = cv2.contourArea(contour)
                    if 240< area<112*224:
                        cv2.rectangle(resizedFrame,(x,y),(x+w,y+h),(0,255,0),1)
            # cv2.imwrite(f'frames/{frameCounter}.jpeg',frame)
            # print(ocrImg(f'frames/{frameCounter}.jpeg'))
            # print(resizedFrame.shape)
            # print(inferedFrame.shape)
            # break
            cv2.imshow('test3',inferedFrameEroded)
            cv2.imshow('test2',inferedFrame)
            cv2.imshow('test',resizedFrame)
            cv2.waitKey(1)
        frameCounter+=1
    cap.release()