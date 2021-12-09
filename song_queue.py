
class Song():
    def __init__(self, id, title, url, playUrl, duration, player=None):
        self.id=id
        self.title=title
        self.url=url
        self.playUrl = playUrl
        self.duration=duration
        self.player=player

class SongQueue():
    def __init__(self):
        self.queue_list = []

    async def add_to_queue(self, file, url, playUrl, duration, player=None):
        self.queue_list.append(Song(len(self.queue_list), file, url, playUrl, duration, player))

    async def remove_from_queue(self, id):
        for song in self.queue_list:
            if id == song.id:
                self.queue_list.remove(song)
        # if os.path.exists(f"./AudioFiles/{file}"):
        #     os.remove(f"./AudioFiles/{file}")
    
    async def get_queue(self):
        return self.queue_list

    async def clear_queue(self):
        self.queue_list = []
