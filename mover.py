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


def _move(path):
  dst = _get_move_path(path)
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

def _get_move_path(path):
  guess = guess_file_info(path, info = ['filename'])
  t = guess['type']
  return os.path.join(PATHS[t], _path_suffix(path, guess))

def _path_suffix(path, guess):
  t = guess['type']
  return {
    'movie':_movie_path_suffix,
    'episode':_episode_path_suffix,
  }[t](path, guess)

def _episode_path_suffix(path, guess):
  name = os.path.basename(path)
  tld = guess['series']
  sld = 'Season %s ' % guess['season']
  return os.path.join(tld, sld, name)

def _movie_path_suffix(path, guess):
  title, container = guess['title'], guess['container']
  return '%s.%s' % (title, container)

class FileEventMover(FileSystemEventHandler):
  def on_created(self, evt):
    if not any(evt.src_path.endswith(ext) for ext in VALID_EXT):
      return

    try:
      return _move(evt.src_path)
    except Exception as e:
      print repr(e)
      raise

  def on_moved(self, evt):
    if not any(evt.dest_path.endswith(ext) for ext in VALID_EXT):
      return
    try:
      return _move(evt.dest_path)
    except Exception as e:
      print repr(e)
      raise


if __name__ == "__main__":
  try:
    path = sys.argv[1]
  except IndexError:
    path = ''
  path = os.path.abspath(path)

  for f in os.listdir(path):
    if any(f.endswith(ext) for ext in VALID_EXT):
      _move(f)

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
