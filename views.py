from flask import Flask, render_template, request, Markup
from services import get_tile_clusters, get_images, get_master_instances

app = Flask(__name__)
app.config.from_object('config')

@app.context_processor
def inject_user():
    username = request.headers.get('REMOTE_USER')
    if username is None:
        username = "Anyonmous"

    return dict(username=username)

@app.template_filter('highlight_with_label')
def highlight_with_label(s):
    """
    http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html
    """
    html = '<span class="label %s">%s</span>'
    s = s.upper()

    # success
    if s in ('RUNNING', 'AVAILABLE', 'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'):
        return Markup(html % ('label-success', s))
    # info
    elif s in ('PENDING'):
        return Markup(html % ('label-info', s))
    # danger
    elif s in ('STOPPED'):
        return Markup(html % ('label-danger', s))
    else:
        return Markup(html % ('label-default', s))
        

    return s[::-1]

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

