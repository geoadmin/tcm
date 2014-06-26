import config, datetime, json
from boto import ec2, cloudformation
from boto.ec2 import autoscale, elb, cloudwatch
from flask import Markup

def get_ec2_connection(region_name='eu-west-1'):
    """
    Return ec2 connection to region
    """
    return ec2.connect_to_region(
        region_name,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECERET_ACCESS_KEY
    )

def get_cloudformation_connection(region_name='eu-west-1'):
    """
    Return cloudformation connection to region
    """
    return cloudformation.connect_to_region(
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

def get_cloudwatch_connection(region_name='eu-west-1'):
    """
    Return elastic loadbalancer connection to region
    """

    return cloudwatch.connect_to_region(
        region_name,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECERET_ACCESS_KEY
    )

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            encoded_object = obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            encoded_object =json.JSONEncoder.default(self, obj)
        return encoded_object

def get_elb_stats(name, metric='RequestCount', minutes=60, period=60):
    conn = get_cloudwatch_connection()
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=minutes)
    stats = conn.get_metric_statistics(period, start, end, metric, 'AWS/ELB', 'Sum', {"LoadBalancerName": name})
    return stats

def get_cpu_stats(name, metric='CPUUtilization', minutes=60, period=60):
    conn = get_cloudwatch_connection()
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=minutes)
    stats = conn.get_metric_statistics(period, start, end, metric, 'AWS/EC2', 'Average', {"AutoScalingGroupName": name})
    print stats
    return stats

def get_tile_clusters(**filter):
    ec2_conn = get_ec2_connection()
    cf_conn = get_cloudformation_connection()
    elb_conn = get_elb_connection()
    as_conn = get_autoscale_connection()

    clusters = []
    for stack in cf_conn.describe_stacks():
        if stack.stack_status not in ('ROLLBACK_COMPLETE'):
            cluster = {'stack': stack}
            for resource in stack.list_resources():
                if resource.resource_type == 'AWS::ElasticLoadBalancing::LoadBalancer':
                    cluster['elb'] = elb_conn.get_all_load_balancers(load_balancer_names=[resource.physical_resource_id])[0]
                elif resource.resource_type == 'AWS::AutoScaling::LaunchConfiguration':
                    kwargs = {'names': [resource.physical_resource_id]}
                    cluster['launch_config'] = as_conn.get_all_launch_configurations(**kwargs)[0]
                elif  resource.resource_type == 'AWS::AutoScaling::AutoScalingGroup':
                    cluster['group'] = as_conn.get_all_groups(names=[resource.physical_resource_id])[0]

            instance_ids = [i.instance_id for i in cluster['group'].instances]
            cluster['instances'] = ec2_conn.get_only_instances(instance_ids=instance_ids)

            cluster['elb_stats'] = Markup(json.dumps(get_elb_stats(cluster['elb'].name), cls=DateTimeEncoder))
            cluster['cpu_stats'] = Markup(json.dumps(get_cpu_stats(cluster['group'].name), cls=DateTimeEncoder))


            clusters.append(cluster)
        
    return clusters

def get_images():
    conn = get_ec2_connection()
    images = conn.get_all_images(owners=['self'])
    return images

def get_master_instances():
    conn = get_ec2_connection()
    filters = {'tag:tcm': 'master'}
    return conn.get_only_instances(filters=filters)


