from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
from re import sub
from shutil import rmtree
from subprocess import  CalledProcessError, run
from textdetectorv4 import imgExtractor
from decouple import config



PYTHONPATH=config('PYTHONPATH')

inUse=False
def filtradoNombre(nombre):
    x = sub(r"\.avi$", "", nombre)
    x = sub(r"\.mp4$", "", x)
    x = sub(r"\.mkv$", "", x)
    x = sub(r"\.ts$", "", x)
    x = sub(r"\.rmvb", "", x)
    x = x.strip()
    return x


def comando(comand,workDirectory,nameDirectory,excutor3):
    try:
        excutor3.submit(updateQueue,comand,workDirectory)
    except CalledProcessError as err:
        print('ERROR:', err)

def updateQueue(comand,workDirectory):
    run(comand,cwd=workDirectory)
    rmtree(workDirectory)


def main():
    queueText = Path(f'{Path(Path.cwd())}/queue.json')
    if queueText.exists():
        os.remove('queue.json')
    excutor2 = ThreadPoolExecutor(max_workers=4)
    excutor3 = ThreadPoolExecutor(max_workers=1)
    current_directory = Path(Path.cwd())
    videos_path= Path(f'{current_directory}/Videos')
    if not videos_path.exists():
        os.mkdir('Videos')
    for video in os.scandir('Videos'):
        try:
            images_dir = Path(
                f'{current_directory}/{filtradoNombre(video.name)}')
            if not images_dir.exists():
                print("\nExtrayendo imagenes de :"+str(video.name))
                imgExtractor(video, excutor2)
                #'cd "'+video.path+'"; python "' + str(current_directory)+'/ocrGoogle.py"'
            comando(f'{PYTHONPATH} "{current_directory}\\ocrGoogle.py"',str(current_directory)+'\\'+filtradoNombre(video.name),filtradoNombre(video.name),excutor3)
        except Exception as ex:
            print(ex)
    excutor2.shutdown(wait=True)
    excutor3.shutdown(wait=True)


if __name__ == "__main__":
    main()
