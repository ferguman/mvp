from config.config import camera_subscribers

def make_subscriber(dict):

    module = __import__('python.camera_subscribers.{}'.format(dict['sub']), fromlist=[dict['sub']])

    class_ = getattr(module, dict['sub'])

    return class_(**dict['args'])

def get_camera_subscribers(camera_subscribers):

    subs = []
    for s in camera_subscribers:
        subs.append(make_subscriber(s))

    return subs
