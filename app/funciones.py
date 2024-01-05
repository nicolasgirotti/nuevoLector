from flask import Flask, render_template, request, Response, jsonify, redirect
from flask_socketio import SocketIO, emit
from werkzeug.middleware.proxy_fix import ProxyFix
from queue import Queue
from pyzbar import pyzbar
from pyzbar.pyzbar import decode, ZBarSymbol
import base64, cv2
import numpy as np
from PIL import Image
import io, threading
from collections import Counter
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import requests, re
from bs4 import BeautifulSoup
from app import app, db, socketio
from app.models import lista_de_productos




def stringToImage(base64_string):
    imgdata = base64.b64decode(base64_string)
    imagen = Image.open(io.BytesIO(imgdata))
    path = 'imagen_decodificada.png'
    imagen.save(path)
    return Image.open(io.BytesIO(imgdata))

def toRGB(image):
    
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)




def procesamiento_frame(frame):
    global barcode_found
    global codigoDeBarra
    # Decodificar los datos base64 a una imagen
    
    # Convertir la imagen a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    umbral = 130
    valor_maximo = 255
    
    # Aplicar umbral binario
    _, binary = cv2.threshold(gray, umbral, valor_maximo, cv2.THRESH_BINARY | cv2.THRESH_OTSU)


    # Ajuste de filtro gaussiano
    tamaño_kernel = (5, 5)
    desviacion_x = 0
    desviacion_y = 0
    # Aplicar filtro gaussiano
    blurred = cv2.GaussianBlur(binary, tamaño_kernel, desviacion_x,desviacion_y)

    # Lógica para detectar el código de barras con OpenCV
    # Usa la biblioteca que desees para el reconocimiento del código de barras

    # Por ejemplo, si usas la biblioteca pyzbar para el reconocimiento del código de barras
    codigos = decode(blurred)

    # Procesa los códigos encontrados
    resultados = []
    for codigo in codigos:
        if codigo:
            datos = codigo.data.decode('utf-8')
            tipo = codigo.type
            resultados.append({'tipo': tipo, 'datos': datos})
            if datos:
                app.config['barcode_found'] = True
                app.config['codigoDeBarra'] = datos
                
                socketio.emit('redirect', {'url': '/codigoDeProducto'})
            break
            




def calcularCodigo(lista_codigo):
    # REQUIERE: Una lista de codigos
    # RETORNA: El codigo que mas se repite
    
    contador_codigos = Counter(lista_codigo)
    masProbable = contador_codigos.most_common(1)[0][0]
    
    return masProbable


def busquedaDeTags(respuestaDeGoogle):
    # REQUIERE: Una respuesta de html a traves de google
    # RETORNA: Los titulos de los links
    
    # Obtener el contenido HTML de la página
    html_content = respuestaDeGoogle.text

    # Parsear el contenido HTML con BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Encontrar todas las etiquetas h3 en la página
    h3_tags = soup.find_all('h3')
    
    return h3_tags



def consultaSQL(codigo_ean):
    # REQUIERE: Un codigo de producto
    # RETORNA: Los datos del producto
    producto = lista_de_productos.query.filter_by(ean=codigo_ean).first()
    return producto


# Función para extraer el tamaño
def extraer_tamaño(descripcionProducto):
    # REQUIERE: La descripcion de un producto
    # MODIFICA: Convierte en minuscula la descripcion
    # RETORNA: El tamaño del producto
    descripcion = descripcionProducto.lower()
    match = re.search(r'\b\d+\s?(?:kg|lts|saq|cc|lts|unid|uni|grm|grs|gr|g|lt|l|un|u|ml|m)\b', descripcion, re.IGNORECASE)
    return match.group() if match else ''



def tamañoUnidad(tamaño):
    # REQUIERE: Informacion del tamaño de un producto
    # RETORNA: Dimension y tamaño, si es que tiene ambas, caso contrario cadena vacia.
    try:
        dimension, unidad = tamaño.split()
        return dimension,unidad
    except:
        cadena = ''
        return tamaño, cadena



