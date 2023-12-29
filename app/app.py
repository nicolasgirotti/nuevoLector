from flask import Flask, render_template, request, Response, jsonify
from flask_socketio import SocketIO, emit
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



app = Flask(__name__)
app.config['SECRET_KEY'] ='llave-secreta'
socketio = SocketIO(app, async_mode='eventlet')

#Conexion a la base de datos
#app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://nico:naiki2353@172.20.0.2/productos'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://nico:naiki2353@localhost/productos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

db = SQLAlchemy(app)

def stringToImage(base64_string):
    imgdata = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(imgdata))

def toRGB(image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)




def procesamiento_frame(frame):
    global barcode_found
    global codigoDeBarra
    # Decodificar los datos base64 a una imagen
    
    # Convertir la imagen a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Aplicar umbral binario
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Aplicar filtro gaussiano
    blurred = cv2.GaussianBlur(binary, (5, 5), 0)

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
                barcode_found = True
                codigoDeBarra = datos
            if barcode_found:
                socketio.emit('redirect', {'url': '/codigoDeProducto'})
            
        break
   

# Socket que permite transmitir el codigo capturado y redirigir para su manejo.
@socketio.on('connect')
def handle_connect():
    global barcode_found
    


class lista_de_productos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ean = db.Column(db.String(100), unique=True)
    nameComplete = db.Column(db.String(255))
    dimension = db.Column(db.String(20))
    unidad_de_peso = db.Column(db.String(20))
    precio = db.Column(db.Float)


# Variables globales
barcode_found = False
codigoDeBarra = None

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
    codigoBuscado = codigoDeBarra
    consulta = consultaSQL(codigoDeBarra)
    return render_template('codigoEAN.html', codigo=consulta, codigoBuscado=codigoBuscado)

   


# Ruta que googlea un codigo que no se encuentra en la BBDD
    
@app.route('/codigoEan/<int:numero>')
def googleCodigo(numero):
    url = f'https://www.google.com/search?q={numero}'

    # Realizar la solicitud GET a la URL
    response = requests.get(url)

    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:

        # Encontrar todas las etiquetas h3 en la página
        h3_tags = busquedaDeTags(response)

        # Seleccionar las primeras tres etiquetas h3
        selected_h3 = h3_tags[:3]

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








if __name__ == '__main__':
    socketio.run(app, debug=True)