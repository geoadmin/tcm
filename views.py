from flask import Flask, render_template
from services import get_tile_clusters

app = Flask(__name__)
app.config.from_object('config')

@app.route("/")
def index():
    #as_conn = get_autoscale_connection()
    #groups = as_conn.get_all_groups()

    #launch_config_names = [group.launch_config_name for group in groups]
    #kwargs = {'names': launch_config_names}
    #launch_configs = as_conn.get_all_launch_configurations(**kwargs)

    #elb_names = [elb for elb in group.load_balancers for group in groups]
    
    #kwargs = {'load_balancer_names': elb_names}
    #elb_conn = get_elb_connection()
    #elbs = elb_conn.get_all_load_balancers(**kwargs)

    clusters = get_tile_clusters()
    print clusters

    return render_template('index.html', clusters=clusters)
