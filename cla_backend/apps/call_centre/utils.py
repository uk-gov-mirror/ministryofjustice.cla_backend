class NoDefaultProvided(object):
    pass

def getattrd(obj, name, default=NoDefaultProvided):
    """
    Same as getattr(), but allows double dash notation lookup
    Discussed in:
    http://stackoverflow.com/questions/11975781
    """

    try:
        return reduce(getattr, name.split("__"), obj)
    except AttributeError, e:
        if default != NoDefaultProvided:
            return default
        raise


def _transform_patch_line(item):
    lookup = {
        'replace': 'Changed',
        'add': 'Added',
        'remove': 'Removed'
    }

    return {
        'action': lookup[item['op']],
        'thing': item['path'].lstrip('/').replace('/','.'),
        'value': item['value']
    }

def format_patch(patch):
    lines = []
    for change in patch:
        change = _transform_patch_line(change)
        lines.append("{action} {thing} to {value}".format(**change))
    return '\n'.join(lines)


