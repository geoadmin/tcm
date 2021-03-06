import config
import datetime
import json
from boto import ec2, cloudformation
from boto.ec2 import autoscale, elb, cloudwatch
from flask import Markup
from boto.exception import BotoServerError


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            encoded_object = obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            encoded_object =json.JSONEncoder.default(self, obj)
        return encoded_object


def get_aws_connection(service, region_name='eu-west-1'):

    credentials = {
        'aws_access_key_id': config.AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': config.AWS_SECERET_ACCESS_KEY
    }

    if service == 'ec2':
        return ec2.connect_to_region(region_name, **credentials)
    elif service == 'cloudformation':
        return cloudformation.connect_to_region(region_name, **credentials)
    elif service == 'autoscale':
        return autoscale.connect_to_region(region_name, **credentials)
    elif service == 'elb':
        return elb.connect_to_region(region_name, **credentials)
    elif service == 'cloudwatch':
        return cloudwatch.connect_to_region(region_name, **credentials)
    else:
        raise Exception("Unkown service '%s'" % service)


def describe_clusters(stack_name_or_id=None):

    cf = get_aws_connection('cloudformation')
    elb = get_aws_connection('elb')
    autoscale = get_aws_connection('autoscale')

    # get a list of active stacks
    stacks = []
    try:
        for stack in cf.describe_stacks(stack_name_or_id=stack_name_or_id):
            if stack.stack_status not in ('ROLLBACK_COMPLETE') and stack.stack_name.startswith('tcm-'):
                stacks.append(stack)
    except BotoServerError, e:
        # log
        return None

    clusters = []
    for stack in stacks:
            cluster = {'stack': stack}
            for resource in stack.list_resources():
                if resource.resource_type == 'AWS::ElasticLoadBalancing::LoadBalancer':
                    cluster['elb'] = elb.get_all_load_balancers(load_balancer_names=[resource.physical_resource_id])[0]

                elif resource.resource_type == 'AWS::AutoScaling::LaunchConfiguration':
                    kwargs = {'names': [resource.physical_resource_id]}
                    cluster['launch_config'] = autoscale.get_all_launch_configurations(**kwargs)[0]
                elif  resource.resource_type == 'AWS::AutoScaling::AutoScalingGroup':
                    cluster['group'] = autoscale.get_all_groups(names=[resource.physical_resource_id])[0]
                else:
                    raise Exception("Unkonw resource type '%s'" % resource.resource_type)

            clusters.append(cluster)

    # sort list by stack creation time
    clusters.sort(key=lambda x: x['stack'].creation_time, reverse=True)

    return clusters


def get_autoscaling_group(group_name):
    autoscale = get_aws_connection('autoscale')
    groups = autoscale.get_all_groups(names=[group_name])
    if len(groups) == 1:
        return groups[0]
    else:
        raise Exception('%i autoscaling groups found for name %s' % (len(groups), group_name))


def get_cluster_instances(group_name):
    ec2 = get_aws_connection('ec2')

    group = get_autoscaling_group(group_name)
    instance_ids = [i.instance_id for i in group.instances]

    if len(instance_ids) > 0:
        return ec2.get_only_instances(instance_ids=instance_ids)
    else:
        return []



def get_stats(period, start_time, end_time, metric_name, namespace, statistics, dimensions):
    cw = get_aws_connection('cloudwatch')
    data = cw.get_metric_statistics(period, start_time, end_time, metric_name, namespace, statistics, dimensions)
    stats = json.dumps(data, cls=DateTimeEncoder)
    return Markup(stats)


def get_images():
    ec2 = get_aws_connection('ec2')
    filters = {'tag:tcm': 'image'}
    images = ec2.get_all_images(owners=['self'], filters=filters)
    return images


def get_master_instances():
    ec2 = get_aws_connection('ec2')
    filters = {'tag:tcm': 'master'}
    return ec2.get_only_instances(filters=filters)

