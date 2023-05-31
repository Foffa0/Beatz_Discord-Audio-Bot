from collections import deque
import random
from config import config

class Playlist:
    """Stores the songs to be played and already played and offers basic operation on the queues"""

    def __init__(self):
        # Stores the songs in queue and the ones already played
        self.playque = deque()
        self.playhistory = deque()

        self.loop = False

    def __len__(self):
        return len(self.playque)

    def add(self, track):
        self.playque.append(track)

    def next(self):

        if self.loop == True:
            self.playque.appendleft(self.playhistory[-1])

        if len(self.playque) == 1:
            return None

        if len(self.playhistory) > config.MAX_HISTORY_LENGTH:
            self.playhistory.popleft()
        self.playhistory.append(self.playque[0])
        self.playque.popleft()
        return self.playque[0]

    def prev(self):

        # if current_song is None:
        #     self.playque.appendleft(self.playhistory[-1])
        #     return self.playque[0]
        if len(self.playhistory) < 1:
            return None
        #ind = self.playhistory.index(current_song)
        self.playque.appendleft(self.playhistory.pop())
        #if current_song != None:
        #self.playque.insert(0, self.playque[0])
        return self.playque[0]

    def shuffle(self):
        random.shuffle(self.playque)

    def move(self, oldindex: int, newindex: int):
        temp = self.playque[oldindex]
        del self.playque[oldindex]
        self.playque.insert(newindex, temp)

    def clear(self):
        self.playque.clear()
        self.playhistory.clear()