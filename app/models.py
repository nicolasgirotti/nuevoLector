from app import db



class lista_de_productos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ean = db.Column(db.String(100), unique=True)
    nameComplete = db.Column(db.String(255))
    dimension = db.Column(db.String(20))
    unidad_de_peso = db.Column(db.String(20))
    precio = db.Column(db.Float)
