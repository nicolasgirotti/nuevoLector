var constraints = {
    video: {
        facingMode: 'environment' ,
        width: { ideal: 640 },
        height: { ideal: 480 }
    }
};

navigator.mediaDevices.getUserMedia(constraints)
    .then(function(stream) {
        var video = document.getElementById('video');
        video.srcObject = stream;
        video.play();
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: video,
            },
            decoder: {
                readers: ["ean_reader"]
            }
        }, function(err) {
            if (err) {
                console.log(err);
                return;
            }
            console.log("QuaggaJS initialization finished");

            Quagga.start();
            Quagga.onDetected(function(data) {
                console.log("Código de barras detectado:", data.codeResult.code);

                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');
                canvas.width = 640;
                canvas.height = 480;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                var imageDataURL = canvas.toDataURL('image/png');

                fetch('/recibir_frame', {
                    method: 'POST',
                    body: JSON.stringify({ image_data: imageDataURL }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    console.log('Frame enviado al servidor');
                })
                .catch(error => {
                    console.error('Error al enviar el frame:', error);
                });
            });
        });
    })
    .catch(function(err) {
        console.log("Error al acceder a la cámara: " + err);
    });