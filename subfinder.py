import json

from pathlib import Path
from os import path, scandir,remove
from subprocess import run, CalledProcessError
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import false, true
from tqdm import tqdm
from httplib2 import Http
from shutil import rmtree,move
import io
from re import sub
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaFileUpload, MediaIoBaseDownload


NHILOS=1
RUTASUBFINDER="VideoSubFinderWXW"
CIVSF="-c -r "
MOTOR="-ovocv"
USECUDA=""
CVSF="-te 0.3 -be 0.0 -le 0.0 -re 1.0"
REMOVEFILES=true

# cargamos la configuracion
text_configure = Path(f'{Path(Path.cwd())}/config.json')



if not text_configure.exists():
    configuration=open('./config.json', 'w', encoding='utf-8')
    configuration.write('{"nthreads": 4,"removeFiles":true,"ruteVideoSubfinder.exe":"VideoSubFinderWXW","configInitVideoSubFinder":"-c -r ","searchMotor":"-ovocv", "useCuda":false,"cutVideoSubFinder":"-te 0.3 -be 0.0 -le 0.0 -re 1.0"}')
    configuration.close()
configuration=open('./config.json', 'r', encoding='utf-8')
configurationGeneral=configuration.read()
configurationGeneral=json.loads(configurationGeneral)
configuration.close()

for config in configurationGeneral:
    if config =="nthreads":
        NHILOS=int(configurationGeneral[config])
    if config == "removeFiles":
        if configurationGeneral[config]=="true":
            REMOVEFILES=true
        else:
            REMOVEFILES=false
    if config == "ruteVideoSubfinder.exe":
        RUTASUBFINDER=configurationGeneral[config]
    if config == "configInitVideoSubFinder":
        CIVSF=configurationGeneral[config]
    if config == "searchMotor":
        MOTOR=configurationGeneral[config]
    if config == "useCuda":
        USECUDA=configurationGeneral[config]
    if config == "cutVideoSubFinder":
        CVSF=configurationGeneral[config]


excutor = ThreadPoolExecutor(max_workers=NHILOS)#el numero de hilos de su procesador menos 1

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
def filtradoNombre(nombre):
    x=sub(r"\.avi$","",nombre)
    x=sub(r"\.mp4$","",x)
    x=sub(r"\.mkv$","",x) 
    return x

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_path = path.join("./", 'token.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Guardando credenciales en ' + credential_path)
    return credentials


def extractor_Google(nombre):
    try:
        credentials = get_credentials()
        http = credentials.authorize(Http())
        service = discovery.build('drive', 'v3', http=http)

        # imgfile = 'image.jpeg'  # Image with texts (png, jpg, bmp, gif, pdf)
        # txtfile = 'text.txt'  # Text file outputted by OCR
        
        nombre=filtradoNombre(nombre)
       
        images_dir = Path(f'{current_directory}/{nombre}')
        raw_texts_dir = Path(f'{current_directory}/{nombre}/raw_texts')
        texts_dir = Path(f'{current_directory}/{nombre}/texts')
        srt_file = open(Path(f'{current_directory}/Subtitles/{nombre}.srt'), 'a', encoding='utf-8')
        line = 1

        # check directory if exists
        if not images_dir.exists():
            images_dir.mkdir()
            print('Images folder is empty.')
            exit()

        if not raw_texts_dir.exists():
            raw_texts_dir.mkdir()
        else:
            # rmtree(raw_texts_dir)
            # raw_texts_dir.mkdir()
            pass
        
        if not texts_dir.exists():
            texts_dir.mkdir()
        else:
            # rmtree(texts_dir)
            # texts_dir.mkdir()
            pass 

        images = Path(images_dir).rglob('*.jpeg')
        for image in tqdm(images,desc=nombre):

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
                    print('\nerror al subir imagen')
            while conforme :        
                try:
                    downloader = MediaIoBaseDownload(
                        io.FileIO(raw_txtfile, 'wb'),
                        service.files().export_media(fileId=res['id'], mimeType="text/plain")
                    )
                    done = False
                    break
                except:
                    print('\nerror al descargar archivo')

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
            # borramos la imagen
            if REMOVEFILES==true :
                remove(image.absolute())
            # remove(txtfile)
            #print(f"{imgname} Done.")
        srt_file.close()
        # verificamos que se hizo el ocr de todas las imagenes 
        # imagenes_images = Path(images_dir).rglob('*.jpeg')
        # textos_images=Path(texts_dir).rglob('*.text')
        # nro_imagenes=0;
        # nro_textos=0;
        # for imagen in imagenes_images:
        #     nro_imagenes+=1
        # for texto in textos_images:
        #     nro_textos+=1
        # if not nro_imagenes==nro_textos:
        #     extractor_Google(nombre)
        
        return images_dir
    except OSError as err:
        print("OS error: {0}".format(err))
        extractor_Google(nombre)
    except ValueError:
        print("Could not convert data to an integer.")
        extractor_Google(nombre)
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        extractor_Google(nombre)



def comando(comand):
    
    try:
        resultado=run(comand,shell=False)
    except CalledProcessError as err:
        print('ERROR:', err)
    else:
        print('Codigo', resultado.returncode)
        
    

def mover(nom):
    x=sub(r"\.avi$","",nom)
    x=sub(r"\.mp4$","",x)
    x=sub(r"\.mkv$","",x)    
    nombreimagen=x
    nombreimagen=Path(f'{current_directory}/{nombreimagen}')
    # print(nombreimagen)
    if not nombreimagen.exists():
        nombreimagen.mkdir()
    else:
        rmtree(nombreimagen)
        nombreimagen.mkdir()
    #cambiar por la ruta de RGBImages de su Videosubfinder
    #ademas añadir VideoSubfinder a el path
    folder=scandir(f'D:\Programas de subtitulos\Release_x64\RGBImages')
    
    for bitmap in folder:
        
        rutaimagen=Path(f"{nombreimagen}/{bitmap.name}")
        move(bitmap.path,rutaimagen )

# verifcamos si existen las carpetas necesarias
videos_dir = Path(f'{current_directory}/Videos')
if not videos_dir.exists():
        videos_dir.mkdir()

Subtitles_dir = Path(f'{current_directory}/Subtitles')

if not Subtitles_dir.exists():
        Subtitles_dir.mkdir()



videos=scandir(f'{current_directory}\Videos')
print("Iniciando proceso")

procesos=[]

for video in videos:
    try:
        images_dir = Path(f'{current_directory}/{filtradoNombre(video.name)}')
        if not images_dir.exists():
            print("\nExtrayendo imagenes de :"+str(video.name))
            # cd=f'VideoSubFinderWXW -c -r -i "{video.path}" -ovffmpeg -uc -te 0.3 -be 0.0 -le 0.0 -re 1.0' #usar si tiene instalado ffmpeg y tiene activo cuda (solo para gpu nvidia)
            # cd=f'VideoSubFinderWXW -c -r -i "{video.path}" -ovocv -te 0.3 -be 0.0 -le 0.0 -re 1.0'  #todos los demas casos 
            # print(f'{RUTASUBFINDER} {CIVSF} -i "{video.path}" {MOTOR} {CVSF}')
            cd=f'{RUTASUBFINDER} {CIVSF} -i "{video.path}" {MOTOR} {CVSF}'  #todos los demas casos 
            comando(cd)
            print("\n---------Moviendo imagenes-----------")
            mover(video.name)
        result=excutor.submit(extractor_Google,video.name)
        procesos.append(result)
        
    except Exception as ex:
        print(ex)
excutor.shutdown(wait=true)
if REMOVEFILES :
    print("Removiendo archivos")
    for proceso in procesos :
        print(proceso.result())
        rmtree(proceso.result())


