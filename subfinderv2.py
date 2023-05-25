import json
from time import time,sleep
from pathlib import Path
import threading
from os import path, scandir, remove
from subprocess import run, CalledProcessError
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from httplib2 import Http
from shutil import rmtree, move
import io
from re import sub
from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from textdetectorv3 import imgExtractor
import re


NHILOS = 8
RUTASUBFINDER = "VideoSubFinderWXW"
RUTARGBIMAGE = ""
CIVSF = "-c -r "
MOTOR = "-ovocv"
USECUDA = ""
CVSF = "-te 0.3 -be 0.0 -le 0.0 -re 1.0"
REMOVEFILES = True
THREADS = 16

# cargamos la configuracion
text_configure = Path(f'{Path(Path.cwd())}/config.json')

# os.environ["CUDA_VISIBLE_DEVICES"]="-1"

if not text_configure.exists():
    configuration = open('./config.json', 'w', encoding='utf-8')
    configuration.write('{"nthreads": 4,"removeFiles":true,"ruteVideoSubfinder.exe":"VideoSubFinderWXW","ruteVideoSubfinderRGBImages":"","configInitVideoSubFinder":"-c -r ","searchMotor":"-ovocv", "useCuda":false,"cutVideoSubFinder":"-te 0.3 -be 0.0 -le 0.0 -re 1.0"}')
    configuration.close()
configuration = open('./config.json', 'r', encoding='utf-8')
configurationGeneral = configuration.read()
configurationGeneral = json.loads(str(configurationGeneral))
configuration.close()

for config in configurationGeneral:
    print("config : "+config + " -- Value : " +
          str(configurationGeneral[config]))
    if config == "nthreads":
        NHILOS = int(configurationGeneral[config])
    if config == "removeFiles":
        if configurationGeneral[config]:
            REMOVEFILES = True
        else:
            REMOVEFILES = False
        # print(type(configurationGeneral[config]))
        # print(REMOVEFILES)
    if config == "ruteVideoSubfinder.exe":
        RUTASUBFINDER = configurationGeneral[config]
    if config == "ruteVideoSubfinderRGBImages":
        RUTARGBIMAGE=configurationGeneral[config]
    if config == "configInitVideoSubFinder":
        CIVSF = configurationGeneral[config]
    if config == "searchMotor":
        MOTOR = configurationGeneral[config]
    if config == "useCuda":
        if configurationGeneral[config]:
            USECUDA = True
        else:
            USECUDA = False
    if config == "cutVideoSubFinder":
        CVSF = configurationGeneral[config]


# el numero de hilos de su procesador menos 1
excutor = ThreadPoolExecutor(max_workers=NHILOS)

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
list_list={}

def filtradoNombre(nombre):
    x = sub(r"\.avi$", "", nombre)
    x = sub(r"\.mp4$", "", x)
    x = sub(r"\.mkv$", "", x)
    x = sub(r"\.ts$", "", x)
    x = sub(r"\.rmvb", "", x)
    x = x.strip()
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

def reemplazar(test_str=''):
    regex = r"[^A-Za-zÑñÁáÉéÍíÓóÚúÜü?! ,.;:¡¿]"
    subst = ""

    # You can manually specify the number of replacements by changing the 4th argument
    result = re.sub(regex, subst, test_str, 0)
    return result

def extractor_Google(nombre):
    try:

        credentials = get_credentials()
        http = credentials.authorize(Http())
        service = discovery.build('drive', 'v3', http=http)

        # imgfile = 'image.jpeg'  # Image with texts (png, jpg, bmp, gif, pdf)
        # txtfile = 'text.txt'  # Text file outputted by OCR
        
        nombre = filtradoNombre(nombre)

        list_list[nombre]={}

        images_dir = Path(f'{current_directory}/{nombre}')
        raw_texts_dir = Path(f'{current_directory}/{nombre}/raw_texts')
        texts_dir = Path(f'{current_directory}/{nombre}/texts')
        srt_file = open(
            Path(f'{current_directory}/Subtitles/{nombre}.srt'), 'a', encoding='utf-8')
        line = 1


        images2 = []
        threads = []
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
        for image in images:
            images2.append(image)

        for image in tqdm(images2, desc=nombre):
            t = threading.Thread(target=ocr_image, args=[image, line, credentials, current_directory,nombre])
            line += 1
            while len(threads) > THREADS:

                for thread in range(len(threads), 0, -1):
                    thread = thread - 1
                    if not threads[thread].is_alive():
                        threads.pop(thread)
            t.start()
            # sleep(0.25)
            threads.append(t)
            if image == images2[-1]:
                for thread in threads:
                    thread.join()

        for i in sorted(list_list[nombre]):
            srt_file.writelines(list_list[nombre][i])
        srt_file.close()


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



def ocr_image(image, line, credentials, current_directory,nombre):
    tries = 0
    while True:
        try:
            http = credentials.authorize(Http())
            service = discovery.build('drive', 'v3', http=http)
            # Get data
            imgfile = str(image.absolute())
            imgname = str(image.name)
            raw_txtfile = f'{current_directory}/{nombre}/raw_texts/{imgname[:-5]}.txt'
            txtfile = f'{current_directory}/{nombre}/texts/{imgname[:-5]}.txt'
        
            mime = 'application/vnd.google-apps.document'
            conforme = True
            while conforme:
                try:
                    res = service.files().create(
                            body={
                                'name': imgname,
                                'mimeType': mime
                            },
                            media_body=MediaFileUpload(
                                imgfile, mimetype=mime, resumable=True)
                        ).execute()
                    break
                except:
                    # sleep(2)
                    print('\nerror al subir imagen')
            while conforme:
                try:
                    downloader = MediaIoBaseDownload(
                        io.FileIO(raw_txtfile, 'wb'),
                        service.files().export_media(
                            fileId=res['id'], mimeType="text/plain")
                    )
                    done = False
                    break
                except:
                    # sleep(2)
                    print('\nerror al descargar archivo')
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            try:
                service.files().delete(fileId=res['id']).execute()
            except:
                sleep(1)
                try:
                    service.files().delete(fileId=res['id']).execute()
                except:
                    sleep(5)
                    try:
                        service.files().delete(fileId=res['id']).execute()
                    except:
                        raise
        
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
            list_list[nombre][line] = [
                f'{line}\n',
                f'{start_time} --> {end_time}\n',
                f'{reemplazar(text_content)}\n\n',
                ''
            ]
        
            # print(f"{imgname} Done.")
            # borramos la imagen
            if REMOVEFILES == True:
                remove(image.absolute())
            # sleep(2)
            
            break
        except:
            tries +=1
            if tries > 5:
                raise
            continue



def comando(comand):

    try:
        resultado = run(comand, shell=False)
    except CalledProcessError as err:
        print('ERROR:', err)
    # else:
        # print('Codigo', resultado.returncode)


def mover(nom):
    x = sub(r"\.avi$", "", nom)
    x = sub(r"\.mp4$", "", x)
    x = sub(r"\.mkv$", "", x)
    x = sub(r"\.ts$", "", x)
    x = sub(r"\.rmvb", "", x)
    x = x.strip()
    nombreimagen = x
    nombreimagen = Path(f'{current_directory}/{nombreimagen}')
    # print(nombreimagen)
    if not nombreimagen.exists():
        nombreimagen.mkdir()
    else:
        rmtree(nombreimagen)
        nombreimagen.mkdir()
    # cambiar por la ruta de RGBImages de su Videosubfinder
    # ademas añadir VideoSubfinder a el path
    folder = scandir(RUTARGBIMAGE)
    # print("Moviendo Imaganes")
    for bitmap in folder:

        rutaimagen = Path(f"{nombreimagen}/{bitmap.name}")
        move(bitmap.path, rutaimagen)


# verifcamos si existen las carpetas necesarias
videos_dir = Path(f'{current_directory}/Videos')
if not videos_dir.exists():
    videos_dir.mkdir()

Subtitles_dir = Path(f'{current_directory}/Subtitles')

if not Subtitles_dir.exists():
    Subtitles_dir.mkdir()


videos = scandir(f'{current_directory}/Videos')
print("Iniciando proceso")

procesos = []

for video in videos:
    try:
        images_dir = Path(f'{current_directory}/{filtradoNombre(video.name)}')
        if not images_dir.exists():
            print("\nExtrayendo imagenes de :"+str(video.name))
            imgExtractor(video)
            # print("\n---------Moviendo imagenes-----------")
            #mover(video.name)

        result = excutor.submit(extractor_Google, video.name)
        procesos.append(result)

    except Exception as ex:
        print(ex)
excutor.shutdown(wait=True)
if REMOVEFILES:
    print("Removiendo archivos")
    for proceso in procesos:
        print(proceso.result())
        rmtree(proceso.result())
