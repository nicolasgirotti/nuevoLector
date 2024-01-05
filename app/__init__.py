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



app = Flask(__name__)
app.config['SECRET_KEY'] ='llave-secreta'
app.config['barcode_found'] = False
app.config['codigoDeBarra'] = None

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Redirección de HTTP a HTTPS
class HTTPSMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ.get('HTTP_X_FORWARDED_PROTO') == 'http':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
        return self.app(environ, start_response)

app.wsgi_app = HTTPSMiddleware(app.wsgi_app)

socketio = SocketIO(app, async_mode='eventlet')

#Conexion a la base de datos
#app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://nico:naiki2353@172.20.0.2/productos'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://nicolas:naiki2353@localhost/productos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

db = SQLAlchemy(app)





from app import routes
