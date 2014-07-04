import time, datetime, config

from flask import Flask, render_template, request, Markup, make_response, redirect, url_for, jsonify
from services import describe_clusters, get_cluster_instances, get_stats, get_images, get_master_instances, \
    get_aws_connection
from filters import highlight_with_label
from boto.exception import EC2ResponseError, BotoServerError

app = Flask(__name__)
app.config.from_object('config')

@app.route('/')
def index():
    context = { 'title': 'Index' }
    if request.is_xhr:
        context['clusters'] = describe_clusters()
        return render_template('index.html', **context)

    return render_template('loader.html', **context)


@app.route('/ajax-cluster-details', methods=['POST'])
def ajax_cluster_details():
    stack_name = request.form['stack_name']

    clusters = describe_clusters(stack_name)
    if clusters and len(clusters) > 0:
        cluster = clusters[0]

    instanceInfos = cluster['elb'].get_instance_health()
    elbInService = sum(i.state == 'InService' for i in instanceInfos)

    context = {
        'cluster': cluster,
        'elbInService': elbInService,
        'instanceCount': len(instanceInfos),
    }

    return render_template('ajax_cluster_details.html', **context)


@app.route('/ajax-cluster-instances', methods=['POST'])
def ajax_cluster_instances():
    group_name = request.form['group_name']
    instances = get_cluster_instances(group_name)
    return render_template('ajax_cluster_instances.html', instances=instances)


@app.route('/ajax-elb-stats', methods=['POST'])
def ajax_elb_stats():
    elb_name = request.form['elb_name']
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(minutes=60)
    stats = get_stats(60, start_time, end_time, 'RequestCount', 'AWS/ELB', 'Sum', {"LoadBalancerName": elb_name})
    return stats


@app.route('/ajax-cpu-stats', methods=['POST'])
def ajax_cpu_stats():
    group_name = request.form['group_name']
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(minutes=60)
    stats = get_stats(60, start_time, end_time, 'CPUUtilization', 'AWS/EC2', 'Average', {"AutoScalingGroupName": group_name})
    return stats


@app.route('/images')
def images():
    return render_template('images.html')

@app.route('/ajax-image-list', methods=['GET'])
def ajax_image_list():
    images = get_images()
    return render_template('ajax_image_list.html', images=images)

@app.route('/ajax-master-instances', methods=['GET'])
def ajax_master_instances():
    instances = get_master_instances()
    return render_template('ajax_master_instances.html', instances=instances)

@app.route('/create-image', methods=['POST'])
def create_image():
    id = request.form['id']
    description = request.form['description']
    user = inject_user()['username']

    conn = get_aws_connection('ec2')

    instances = conn.get_only_instances(instance_ids=[id])
    instance = instances[0]

    name = "%s_%s" % (instance.tags['Name'], time.strftime("%Y-%m-%d_%H-%M-%S"))

    try:
        ami_id = instance.create_image(name, description)
        # sleep 2 seconds to make sure that we can load the AMI
        time.sleep(2)
        ami = conn.get_image(ami_id)
        ami.add_tag('creator', user)
        ami.add_tag('tcm', 'image')
    except EC2ResponseError, e:
        return make_response(e.error_message, 500)

    return "AMI %s is getting created. It can take a while to show up under images!" % ami.id


@app.route('/delete-image', methods=['POST'])
def delete_image():
    image_id = request.form['image-id']
    ec2 = get_aws_connection('ec2')
    try:
        ec2.deregister_image(image_id, delete_snapshot=True)
        return "Image successfully deleted!"
    except BotoServerError, e:
        return make_response(e.error_message, 500)


@app.route('/edit-cluster', methods=['POST'])
def edit_cluster():
    conn = get_aws_connection('autoscale')
    group_name = request.form['group_name']
    capacity = request.form['capacity']

    try:
        conn.set_desired_capacity(group_name, capacity)
    except BotoServerError, e:
        return make_response(e.error_message, 500)

    return "Cluster %s capacity updated to %s nodes!" % (group_name, capacity)

@app.route('/delete-cluster', methods=['POST'])
def delete_cluster():
    stack_id = request.form['stack-id']
    cf = get_aws_connection('cloudformation')
    try:
        cf.delete_stack(stack_id)
        return "Cluster successfully deleted!"
    except BotoServerError, e:
        return make_response(e.error_message, 500)

@app.route('/launch-form', methods=['POST'])
def launch_form():
    ami = request.form['image-id']
    return render_template('launch-form.html', ami=ami)

@app.route('/launch-cluster', methods=['POST'])
def launch_cluster():

    template = render_template('template.json')

    # Prefix stackname
    stackName = "tcm-%s" % request.form['name']

    params = [
        ('InstanceType', request.form['instance-type']),
        ('ImageId', request.form['ami']),
        ('DesiredCapacity', request.form['capacity']),
        ('AZs', config.AWS_AVAILABILITY_ZONE),
        ('Subnets', config.AWS_SUBNET),
        ('SecurityGroups', config.AWS_SECURITY_GROUPS),
    ]

    try:
        cf = get_aws_connection('cloudformation')
        cf.create_stack(stackName, template_body=template, parameters=params)
    except BotoServerError, e:
        return make_response(e.error_message, 500)

    return "Cluster '%s' successfully launched! Go to <a href='%s'>Index Page</a>" % (stackName, url_for('index'))


# Register custom template filters
app.jinja_env.filters['highlight_with_label'] = highlight_with_label

# Register
@app.context_processor
def inject_user():
    username = request.headers.get(config.USER_HEADER)
    if username is None:
        username = "Anyonmous"

    return dict(username=username)
