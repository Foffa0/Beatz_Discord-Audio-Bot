
class Song():

    def __init__(self, origin, host, url, title=None, duration=None, thumbnail=None):
        self.origin = origin
        self.host = host
        self.title = title
        self.url = url
        self.duration = duration
        self.thumbnail = thumbnail