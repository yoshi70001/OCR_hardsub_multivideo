from pathlib import Path
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import pytesseract
import cv2
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
import os
from tqdm import tqdm
import httplib2
from shutil import rmtree,move
import io
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

excutor = ThreadPoolExecutor(max_workers=16)

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
# Code is based on https://tanaikech.github.io/2017/05/02/ocr-using-google-drive-api/
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Drive API Python Quickstart'
current_directory = Path(Path.cwd())

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_path = os.path.join("./", 'token.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def extractor_Google(nombre):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    # imgfile = 'image.jpeg'  # Image with texts (png, jpg, bmp, gif, pdf)
    # txtfile = 'text.txt'  # Text file outputted by OCR

    images_dir = Path(f'{current_directory}/{nombre.replace(".mp4","")}')
    raw_texts_dir = Path(f'{current_directory}/{nombre.replace(".mp4","")}/raw_texts')
    texts_dir = Path(f'{current_directory}/{nombre.replace(".mp4","")}/texts')
    srt_file = open(Path(f'{current_directory}/Subtitles/{nombre.replace(".mp4","")}.srt'), 'a', encoding='utf-8')
    line = 1

    # check directory if exists
    if not images_dir.exists():
        images_dir.mkdir()
        print('Images folder is empty.')
        exit()

    if not raw_texts_dir.exists():
        raw_texts_dir.mkdir()
    else:
        rmtree("raw_texts")
        raw_texts_dir.mkdir()
    
    if not texts_dir.exists():
        texts_dir.mkdir()
    else:
        rmtree("texts")
        texts_dir.mkdir()

    images = Path(images_dir).rglob('*.jpeg')
    for image in tqdm(images):

        # Get data
        imgfile = str(image.absolute())
        imgname = str(image.name)
        raw_txtfile = f'{current_directory}/{nombre.replace(".mp4","")}/raw_texts/{imgname[:-5]}.txt'
        txtfile = f'{current_directory}/{nombre.replace(".mp4","")}/texts/{imgname[:-5]}.txt'

        mime = 'application/vnd.google-apps.document'
        conforme=True
        while conforme :
            try:
                res = service.files().create(
                    body={
                        'name': imgname,
                        'mimeType': mime
                    },
                    media_body=MediaFileUpload(imgfile, mimetype=mime, resumable=True)
                ).execute()
                break
            except:
                print('error al subir imagen')
        while conforme :        
            try:
                downloader = MediaIoBaseDownload(
                    io.FileIO(raw_txtfile, 'wb'),
                    service.files().export_media(fileId=res['id'], mimeType="text/plain")
                )
                done = False
                break
            except:
                print('error al descargar archivo')

        while done is False:
            status, done = downloader.next_chunk()

        service.files().delete(fileId=res['id']).execute()

        # Create clean text file
        raw_text_file = open(raw_txtfile, 'r', encoding='utf-8')
        text_content = raw_text_file.read()
        raw_text_file.close()
        text_content = text_content.split('\n')
        text_content = ''.join(text_content[2:])
        text_file = open(txtfile, 'w', encoding='utf-8')
        text_file.write(text_content)
        text_file.close()

        start_hour = imgname.split('_')[0][:2]
        start_min = imgname.split('_')[1][:2]
        start_sec = imgname.split('_')[2][:2]
        start_micro = imgname.split('_')[3][:3]

        end_hour = imgname.split('__')[1].split('_')[0][:2]
        end_min = imgname.split('__')[1].split('_')[1][:2]
        end_sec = imgname.split('__')[1].split('_')[2][:2]
        end_micro = imgname.split('__')[1].split('_')[3][:3]

        # Format start time
        start_time = f'{start_hour}:{start_min}:{start_sec},{start_micro}'

        # Format end time
        end_time = f'{end_hour}:{end_min}:{end_sec},{end_micro}'
        # Append the line to srt file
        srt_file.writelines([
            f'{line}\n',
            f'{start_time} --> {end_time}\n',
            f'{text_content}\n\n',
            ''
        ])

        line += 1

        #print(f"{imgname} Done.")

    srt_file.close()


# def extractor_tesseract(nombre):
#     filtro=True
#     current = Path(Path.cwd())

#     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

#     # if current.exists("subti"):   
#     #     os.remove("subtitulo.srt")
#     srt_file = open(Path(f'{current}/Subtitles/{nombre}.srt'), 'a', encoding='utf-8')
#     line=1
#     with os.scandir(f'D:\Programas de subtitulos\Release_x64\RGBImages') as imagenes:
#         for image in imagenes :
#             img = cv2.imread(image.path)
            
#             # ret,thresh1 = cv2.threshold(img,250,255,cv2.THRESH_BINARY)
#             #cv2.imshow("prueba",img)
#             #ret,thresh2 = cv2.threshold(img,250,255,cv2.THRESH_BINARY_INV)
#             if filtro:
#                 frame=cv2.cvtColor(img,cv2.COLOR_RGB2XYZ)
#                 b,g,r=cv2.split(frame)
#                 rev,thresh1=cv2.threshold(b,235,255,cv2.THRESH_BINARY_INV)
#                 rev,thresh2=cv2.threshold(g,235,255,cv2.THRESH_BINARY_INV)
#                 rev,thresh3=cv2.threshold(r,235,255,cv2.THRESH_BINARY_INV)
#                 uwu=thresh1+thresh2+thresh3
#             else:
#                 ret,uwu = cv2.threshold(img,245,255,cv2.THRESH_BINARY_INV)
#             cv2.imshow("filtrado",uwu)
            
#             imgname=str(image.name)
#             text=pytesseract.image_to_string(uwu,lang="spa")
#             print(text)
#             start_hour = imgname.split('_')[0][:2]
#             start_min = imgname.split('_')[1][:2]
#             start_sec = imgname.split('_')[2][:2]
#             start_micro = imgname.split('_')[3][:3]

#             end_hour = imgname.split('__')[1].split('_')[0][:2]
#             end_min = imgname.split('__')[1].split('_')[1][:2]
#             end_sec = imgname.split('__')[1].split('_')[2][:2]
#             end_micro = imgname.split('__')[1].split('_')[3][:3]

#             # Format start time
#             start_time = f'{start_hour}:{start_min}:{start_sec},{start_micro}'

#             # Format end time
#             end_time = f'{end_hour}:{end_min}:{end_sec},{end_micro}'
#             # Append the line to srt file
#             srt_file.writelines([
#                 f'{line}\n',
#                 f'{start_time} --> {end_time}\n',
#                 f'{text}\n\n',
#                 ''
#             ])

#             line += 1
#             cv2.waitKey(5)
#         # print(f"{imgname} Done.")
#     srt_file.close()     

def comando(comand):
    resultado=subprocess.run(comand,shell=True)
    # resultado.check_returncode()

def mover(nom):
    
    os.mkdir(nom.replace(".mp4", ""))
    #cambiar por la ruta de RGBImages de su Videosubfinder
    #ademas añadir VideoSubfinder a el path
    folder=os.scandir(f'D:\Programas de subtitulos\Release_x64\RGBImages')
    
    for bitmap in folder:
        rutaimagen=Path(f"{current_directory}/{nom.replace('.mp4', '')}/{bitmap.name}")
        move(bitmap.path,rutaimagen )



gaaaa=os.scandir(f'{current_directory}\Videos')
print("Iniciando proceso")
for nani in gaaaa:
    print("Extrayendo imagenes de :"+str(nani.name))
    cd=f'VideoSubFinderWXW -c -r -i "{nani.path}" -ovffmpeg -uc -te 0.3 -be 0.0 -le 0.0 -re 1.0'
    comando(cd)
    print("---------Moviendo imagenes-----------")
    mover(nani.name)
    print("OCR de :"+str(nani.name))

    #extractor_tesseract(nani.name)
    #extractor_Google(nani.name)
    excutor.submit(extractor_Google,nani.name)
    print("Completado :"+str(nani.name))
