import config
from boto import ec2
from boto.ec2 import autoscale, elb

def get_ec2_connection(region_name='eu-west-1'):
    """
    Return ec2 connection to region
    """
    return ec2.connect_to_region(
        region_name,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECERET_ACCESS_KEY
    )


def get_autoscale_connection(region_name='eu-west-1'):
    """
    Return autoscaling connection to region
    """
    
    return autoscale.connect_to_region(
        region_name,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECERET_ACCESS_KEY
    )


def get_elb_connection(region_name='eu-west-1'):
    """
    Return elastic loadbalancer connection to region
    """
    
    return elb.connect_to_region(
        region_name,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECERET_ACCESS_KEY
    )

def get_tile_clusters():
    as_conn = get_autoscale_connection()

    clusters = []

    for group in as_conn.get_all_groups():
        cluster = {'group': group}
        kwargs = {'names': [group.launch_config_name]}
        launch_configs = as_conn.get_all_launch_configurations(**kwargs)
        cluster['launch_config'] = launch_configs[0]

        elb_conn = get_elb_connection()
        kwargs = {'load_balancer_names': [elb for elb in group.load_balancers]}
        cluster['elbs'] = elb_conn.get_all_load_balancers(**kwargs)

        clusters.append(cluster)
        
    return clusters
