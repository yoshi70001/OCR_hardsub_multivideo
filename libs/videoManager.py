import os
from libs.imgExtractor import  imageExtractor

def videoManager():
    for file in os.scandir('videos'):
        print(file.name)
        imageExtractor(file.path,file.name)