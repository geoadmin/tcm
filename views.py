import time

from flask import Flask, render_template, request, Markup, make_response, redirect, url_for
from services import get_tile_clusters, get_images, get_master_instances, get_ec2_connection, get_cloudformation_connection, get_autoscale_connection
from boto.exception import EC2ResponseError, BotoServerError

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
    elif s in ('PENDING', 'CREATE_IN_PROGRESS'):
        return Markup(html % ('label-info', s))
    # danger
    elif s in ('STOPPED'):
        return Markup(html % ('label-danger', s))
    else:
        return Markup(html % ('label-default', s))

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
        context['launch_form'] = Markup(render_template('launch-form.html').replace('\n', ''))
        return render_template('images.html', **context)

    return render_template('loader.html', **context)


@app.route('/create-image', methods=['POST'])
def create_image():
    id = request.form['id']
    description = request.form['description']
    user = inject_user()['username']

    conn = get_ec2_connection()

    instances = conn.get_only_instances(instance_ids=[id])
    instance = instances[0]

    name = "%s_%s" % (instance.tags['Name'], time.strftime("%Y-%m-%d_%H-%M-%S"))

    try:
        ami_id = instance.create_image(name, description)
        # sleep 2 seconds to make sure that we can load the AMI
        time.sleep(2)
        ami = conn.get_image(ami_id)
        ami.add_tag('creator', user)
    except EC2ResponseError, e:
        return make_response(e.error_message, 500) 

    return "AMI %s is getting created. It can take a while to show up under images!" % ami.id

@app.route('/launch-cluster', methods=['POST'])
def launch_cluster():

    template = render_template('template.json')

    params = [
        ('InstanceType', request.form['instance-type']),
        ('ImageId', request.form['ami']),
        ('DesiredCapacity', request.form['capacity']),
    ]

    conn = get_cloudformation_connection()
    conn.create_stack("Test-Stack", template_body=template, parameters=params)

    return "Cluster successfully launched! Go to <a href='"+url_for('index')+"'>Index Page</a>"

@app.route('/edit-cluster', methods=['POST'])
def edit_cluster():
    conn = get_autoscale_connection()
    group_name = request.form['group_name']
    capacity = request.form['capacity']

    try:
        conn.set_desired_capacity(group_name, capacity)
    except BotoServerError, e:
        return make_response(e.error_message, 500)

    return "Cluster %s capacity updated to %s nodes!" % (group_name, capacity)
