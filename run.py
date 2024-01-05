from app import app,socketio




if __name__ == '__main__':
    # Verifica la compatibilidad con WebSocket
    socketio.run(app, debug=True,host='localhost', port=5000)