from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from db_funcs import read_lif_lff_files

class Watcher:
    def __init__(self, app, database,directories_to_watch):
        self.observer = Observer()
        self.directories_to_watch = directories_to_watch
        self.event_handler = Handler()#app, database, directories_to_watch[0], directories_to_watch[1])

    def run(self):
        self.start_observer()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.stop_observer()
        self.observer.join()

    def start_observer(self):
        for directory in self.directories_to_watch:
            self.observer.schedule(self.event_handler, directory, recursive=False)
        self.observer.start()

    def stop_observer(self):
        self.observer.stop()
        self.observer.join()

    def update_directories(self, new_directories):
        self.stop_observer()
        self.directories_to_watch = new_directories
        self.observer = Observer()
        self.start_observer()

class Handler(FileSystemEventHandler):
    def __init__(self, app, database, lff_dir, lif_dir):
        self.app = app
        self.database = database
        self.lff_dir = lff_dir
        self.lif_dir = lif_dir
        
    @staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            return None
        elif event.event_type == 'modified':
            print(f"Received modified event - {event.src_path}")
            print(event)
            
            with self.app.app_context():
                read_lif_lff_files(self.database, self.lif_dir, self.lff_dir)
        elif event.event_type == 'created':
            print(f"Received created event - {event.src_path}")
            print(event)
            
            with self.app.app_context():
                read_lif_lff_files(self.database, self.lif_dir, self.lff_dir)
        elif event.event_type == 'moved':
            print(f"Received moved event - {event.src_path} to {event.dest_path}")
            print(event)
            
            with self.app.app_context():
                read_lif_lff_files(self.database, self.lif_dir, self.lff_dir)
