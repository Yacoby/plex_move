import sys
import time
import os
import shutil
import errno

from guessit import guess_file_info
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

VALID_EXT = ['mp4', 'avi', 'mkv']

BASE_PATH = '/media/bea8e41e-979a-4576-af23-768972299af6/flat/downloaded'

PATHS = {
    'movie': os.path.join(BASE_PATH, 'films'),
    'episode': os.path.join(BASE_PATH, 'tv'),
}

class FileEventMover(FileSystemEventHandler):
    def on_created(self, evt):
        print 'create'
        if not any(evt.src_path.endswith(ext) for ext in VALID_EXT):
            print 'nope'
            return
        return self._move(evt.src_path)

    def on_moved(self, evt):
        if not any(evt.dest_path.endswith(ext) for ext in VALID_EXT):
            return
        return self._move(evt.dest_path)

    def _move(self, path):
        dst = self._get_move_path(path)
        try:
            dir_path = os.path.dirname(dst)
            os.makedirs(dir_path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
                pass
            else:
                raise

        if not os.path.exists(dst):
            shutil.copyfile(path, dst)

    def _get_move_path(self, path):
        guess = guess_file_info(path, info = ['filename'])
        t = guess['type']
        return os.path.join(PATHS[t], self._path_suffix(guess))

    def _path_suffix(self, guess):
        t = guess['type']
        return {
            'movie':self._movie_path_suffix,
            'episode':self._episode_path_suffix,
        }[t](guess)

    def _episode_path_suffix(self, guess):
        title, container = guess['title'], guess['container']
        season, episode = guess['season'], guess['episodeNumber']
        name = '%s S%dE%d.%s' % (title, season, episode, container)
        tld = guess['series']
        sld = 'Season %s ' % guess['season']
        return os.path.join(tld, sld, name)

    def _movie_path_suffix(self, guess):
        name, container = guess['name'], guess['container']
        return '%s.%s' % (name, container)


if __name__ == "__main__":
    try:
        path = sys.argv[1]
    except IndexError:
        path = ''

    event_handler = FileEventMover()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()