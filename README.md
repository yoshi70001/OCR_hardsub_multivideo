# OCR_hardsub_multivideo
Script para realizar ocr a videos de manera multiple
-----------------------------------------------
Usa VideoSubfinder https://sourceforge.net/projects/videosubfinder/ como extractor de imagenes(secuencial) y
google docs como motor de OCR(paralelo)
Se uso https://github.com/Abu3safeer/image-ocr-google-docs-srt como base y se modifico para poder ser usado en paralelo ya que el proyecto original solo permite ejecutar 1 proceso a la vez, y tiene no tiene control de errores para la subida de imagenes lo cual puede causar que el proceso se detenga a la mitad.

Configuracion
----------------------------------------------
Para hacer uso de este script sera necesario el archivo credentials que nos da google al crear un proyecto en su plataforma googlecloud https://console.cloud.google.com/, ya que en este archivo se encontraran los datos necesarios para poder hacer uso de drive y convertir las imagenes a texto.
- El archivo credential.json debe ir junto a subfinder.py.
- Se debe añadir la ruta del VideoSubFinder al path del sistema, ya que haremos uso del mismo mediante linea de comandos
- Por ultimo sera necesario modificar la linea 238 folder=os.scandir(f'D:\Programas de subtitulos\Release_x64\RGBImages') cambiando la ruta por la de su carpeta RBGImages que sera generada al ejecutar por primera vez el VideoSubFinder.
