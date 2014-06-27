from flask import Markup

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