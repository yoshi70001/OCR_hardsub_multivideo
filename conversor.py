from pathlib import Path
import os
import subprocess

current = Path(Path.cwd())

pathentrada = Path(f'{current}/POR CONVERTIR/')

pathsalida = Path(f'{current}/CONVERTIDO/')
def conversor(comando):
    resultado = subprocess.run(comando, shell=True)
    # Comprobar resultado, si es diferente de 0 lanza una excepción
    resultado.check_returncode()

with os.scandir(f'{pathentrada}') as videos:
    for video in videos:
        ruta=Path(f'{current}/POR CONVERTIR/{video.name}')
        nombre=video.name.replace(".avi","")
        rutasalida=Path(f'{current}/CONVERTIDO/{nombre}.mkv')
        #rutasalida=rutasalida+".mkv"
        comando=str(f'ffmpeg -hwaccel cuda -i "{ruta}"  "{rutasalida}"')
        conversor(comando)