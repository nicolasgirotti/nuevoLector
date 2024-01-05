from flask import Flask, render_template, request, Response, jsonify, redirect, url_for, flash
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
from app import app, socketio
from app.funciones import stringToImage, toRGB, procesamiento_frame, consultaSQL, busquedaDeTags, extraer_tamaño,tamañoUnidad
from app.models import lista_de_productos




# Socket que permite transmitir el codigo capturado y redirigir para su manejo.
@socketio.on('connect')
def handle_connect():
    global barcode_found


@app.route('/')
def capturar():
    return render_template('index.html')


@app.route('/recibir_frame', methods=['POST'])
def recibir_frame():
    data = request.get_json()
    image_data = data['image_data'].split(',')[1]  # Elimina la parte 'data:image/png;base64,' del string
    imagen = stringToImage(image_data)
    img_rgb = toRGB(imagen)
    resultados = procesamiento_frame(img_rgb)
    
    return jsonify(resultados)





# Ruta para manejar el codigo obtenido
@app.route('/codigoDeProducto')
def codigoDeProducto():
    codigoBuscado = app.config['codigoDeBarra']
    consulta = consultaSQL(codigoBuscado)
    if consulta:
        print(f'ESTE ES EL CODIGO BUSCADO -> {codigoBuscado}')
        return render_template('codigoEAN.html', codigo=consulta, codigoBuscado=codigoBuscado)
    else:
        flash('Este producto no esta en la base de datos', 'warning')
        return redirect(url_for('googleCodigo', numero=codigoBuscado))
   


# Ruta que googlea un codigo que no se encuentra en la BBDD
    
@app.route('/codigoEan/<int:numero>')
def googleCodigo(numero):
    
    print(f'ESTE ES EL NUMERO DE CODIGO -------------> {numero}')
    url = f'https://www.google.com/search?q={numero}'

    # Realizar la solicitud GET a la URL
    response = requests.get(url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:

        # Encontrar todas las etiquetas h3 en la página
        h3_tags = busquedaDeTags(response)

        # Seleccionar las primeras tres etiquetas h3
        selected_h3 = h3_tags[:3]
        print(f' ESTOS SON LOS TAGS ENCONTRADOS   {selected_h3}')

        # Obtener el texto de las etiquetas h3 seleccionadas
        h3_text = [tag.get_text() for tag in selected_h3]
        
        # Obtiene todas las palabras en las descripciones
        palabras = [re.findall(r'\b\w+\b', descripcion) for descripcion in h3_text]

        # Encuentra palabras comunes en las descripciones
        palabras_unidas = [word.lower() for sublist in palabras for word in sublist]
        frecuencias = Counter(palabras_unidas)
        
        palabras_comunes = {word for word, count in frecuencias.items() if count >= 2}
        
        # Obtiene el tamaño común
        tamaño_comun = extraer_tamaño(' '.join(h3_text))
        
        dimension, unidad = tamañoUnidad(tamaño_comun)
        print(tamaño_comun)
        # Crea la descripción final
        descripcion_final = ' '.join(palabras_comunes)
        descripcion_final_sin_tamaño = descripcion_final.replace(dimension, '')

        print(f"Esta es la descripcion final {descripcion_final_sin_tamaño}")
        
        
        codigo = numero
        
        # Devolver los datos como JSON
        #return jsonify({'descriptions': h3_text}), 200
        return render_template('productoWeb.html', codigo=codigo, dimension=dimension, unidad=unidad, descripcion=descripcion_final_sin_tamaño)

    
    return jsonify({'message': 'Failed to fetch data'}), 500
