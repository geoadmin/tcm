from flask import Flask, render_template, request
from services import get_tile_clusters, get_images, get_master_instances

app = Flask(__name__)
app.config.from_object('config')

@app.context_processor
def inject_user():
    username = request.headers.get('REMOTE_USER')
    if username is None:
        username = "Anyonmous"

    return dict(username=username)

@app.route('/')
def index():
    context = { 'title': 'Index' }
    if request.is_xhr:
        context['clusters'] = get_tile_clusters()
        return render_template('index.html', **context)

    return render_template('loader.html', **context)

@app.route('/images')
def images():
    context = { 'title': 'Images' }
    if request.is_xhr:
        context['images'] = get_images()
        context['instances'] = get_master_instances()
        return render_template('images.html', **context)

    return render_template('loader.html', **context)

