from flask import Flask, request, current_app, redirect, url_for, \
    render_template, make_response, flash
from simulation import prepare_pixels, create_video, \
    prepare_frames, validate_image_errors, \
    validate_image_warnings, cleanup, rows
import datetime
import os
from PIL import Image

app = Flask(__name__)

app.secret_key = b'R\xdb8g\xcc\x9d\xf7\x8e\xc9\x89P(W\xf6]\xf2'


@app.route('/', methods=['GET', 'POST', 'HEAD'])
def upload_pic_file():
    if request.method == 'HEAD':
        return '', 200
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        dt = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        cleanup()
        try:
            input_img_file = request.files['file']
        except KeyError:
            flash(u'☝️ You did not select any image. Select one to create a \
            simulation.', 'warning')
            return render_template('index.html')
        style = request.form['radios']
        if style == "LightOnPhoto":
            light = []
            for i in range(12):
                column = "col{}".format(i+1)
                light.append(request.form[column])
            styleLight = list("".join(light))
            for i in range(len(styleLight)):
                if styleLight[i] == '#':
                    styleLight[i] = '-'
            styleLight = "".join(styleLight)
            print(styleLight)
            style = styleLight
        try:
            image = Image.open(input_img_file)
        except OSError:
            flash(u'☝️ File you selected is not an image.', 'warning')
            return render_template('index.html')
        validation_error = validate_image_errors(image)
        if validation_error:
            flash(validation_error)
            return render_template('index.html')
        image = image.convert("1")
        image, converted, resized = validate_image_warnings(image, dt)
        vid_file_name = "Video{}_{}_{}".format(converted, style, dt)
        try:
            pixelList = prepare_pixels(image)
            frameList = prepare_frames(pixelList, vid_file_name, rows)
            create_video(vid_file_name, frameList)
            return redirect(url_for('result', name=vid_file_name))
        except Exception as e:
            flash(f'An error occurred during processing: {str(e)}', 'error')
            return render_template('index.html')


@app.route('/<name>', methods=['GET'])
def result(name):
    converted = False
    resized = False
    saved_image_name = "None"
    saved_image = False
    if "Converted" in name:
        converted = True
    if "Resized" in name:
        resized = True
    if resized or converted:
        for root, dirs, files in os.walk("./static/"):
            for file in files:
                if file.startswith("Image"):
                    saved_image_name = file
                    print(saved_image_name)
                    saved_image = True

    resp = make_response(render_template('result.html', name=name,
                                         converted=converted, resized=resized,
                                         saved_image_name=saved_image_name,
                                         saved_image=saved_image))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return resp


@app.route('/guidelines', methods=['GET'])
def guidelines():
    return current_app.send_static_file('guidelines.html')
