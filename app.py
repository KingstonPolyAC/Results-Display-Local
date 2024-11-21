
import os
import subprocess
import json
from flask import Flask, g, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_socketio import SocketIO, emit
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData,inspect, Table
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
import threading
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from db_funcs import read_lif_lff_files,insert_data_from_excel_to_db
from models import db,WindInfo, TableLog
from export_funcs import export_fieldcards_to_pdf, export_evt_to_pdf

from queue import Queue
import sqlite3
import time

import waitress
import pythoncom

app = Flask(__name__)

pythoncom.CoInitialize() #Initialize COM Library

socketio = SocketIO(app)

app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'
bootstrap = Bootstrap5(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scoreboard.db'
#Set Secret Key
app.config['SECRET_KEY'] = 'secret-key'
app.config['SSE_QUEUE'] = Queue()

#Initialize db with Flask App                                                                                                                              
db.init_app(app)

# Define the custom filter
def is_digit(value):
    return str(value).isdigit()

# Register the custom filter with Jinja
app.jinja_env.filters['is_digit'] = is_digit

DATABASE = os.path.join(os.getcwd(), "instance", "scoreboard.db") #'instance/scoreboard.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        try:
            # Check if 'wind_info' table exists, create if it doesn't
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS wind_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name VARCHAR(100) NOT NULL,
                wind_value VARCHAR(100) NOT NULL
            );
            """)

            # Check if 'table_log' table exists, create if it doesn't
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name VARCHAR(100) NOT NULL,
                heat_no VARCHAR(100) NOT NULL,
                insert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Commit the changes
            db.commit()
            print("Database setup complete")

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            db.rollback()
        
        finally:
            # Close the connection
            cursor.close()

def get_last_two_tables():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT table_name, heat_no FROM table_log
        ORDER BY insert_time DESC
    ''')
    logs = cursor.fetchall()
    #print("Logs", logs)
    lff_table = None
    lif_table = None
    lff_heat_no = None
    lif_heat_no = None

    # Define the list of keywords to search for
    keywords = ["Javelin", "Discus", "Shot", "Jump", "Pole", "Hammer", "Throw"]

        # Fetch wind info data
    wind_info_dict = {}
    wind_info_query = 'SELECT table_name, wind_value FROM wind_info'
    for row in db.execute(wind_info_query):
        #print(row)
        wind_info_dict[row[0]] = row[1]
        
        
    # Get the last table that has any keyword
    for table_name, heat_no in logs:
        if any(word in table_name.split('_') for word in keywords):
            lff_table = table_name
            lff_heat_no = heat_no
            break

    # Get the last table that does not have any keyword
    for table_name, heat_no in logs:
        if not any(word in table_name.split('_') for word in keywords):
            lif_table = table_name
            lif_heat_no = heat_no
            break

    lif_wind_value = wind_info_dict.get(lif_table, "N/A")

    # Print the results
    print(f"LFF Table: {lff_table}, Heat No: {lff_heat_no}")
    print(f"LIF Table: {lif_table}, Heat No: {lif_heat_no}")

    return [(lff_table, lff_heat_no, "field", "N/A"), (lif_table, lif_heat_no, "track", lif_wind_value)]


def query_last_two_tables():
    tables_data = {}
    last_tables = get_last_two_tables()
    db = get_db()
    cursor = db.cursor()
    
    print(last_tables)
    
    for table in last_tables:
        if table[0] is None:
            continue
        
        cursor.execute(f'SELECT * FROM "{table[0]}"')
        rows = cursor.fetchall()
        #cursor.execute(f'PRAGMA table_info("{table_name}")')
        #columns = [info[1] for info in cursor.fetchall()]
        tables_data[table[0].replace("_", " ")] = {
            #'columns': columns,
            'event_type': table[2],
            'heat_no': table[1],
            'wind_value': table[3],
            'rows': rows,
            
        }
    return tables_data
    
JSON_FILE_PATH = 'meeting_info.json' 
meeting_info = {
    'name': '',
    'track_path': '',
    'field_path': '',
    'workbook_path': ''
}
watcher = None
 
def drop_all_tables():
    # engine = db.engine
    # engine.begin()
    # #Drop all tables
    # inspector = inspect(engine)
    # for table_name in inspector.get_table_names():
    #     print(db.metadata.tables)
    #     table = db.metadata.tables[table_name]
    #     db.session.execute(table.drop(bind=engine))
        
    #     db.session.commit()
    print("Deleting previous tables")
    # metadata = MetaData()
    # metadata.reflect(db.engine)
    #db.metadata = metadata
    #Drop all tables from metadata
    # metadata.drop_all(db.engine)
    # db.metadata.clear()
    # Identify the 'wind_info' and 'table_log' table
    # wind_info_table = Table('wind_info', metadata, autoload_with=db.engine)
    # table_log_table = Table('table_log', metadata, autoload_with=db.engine)

    # # Drop all tables except 'wind_info' and table_log
    # tables_to_drop = [table for table in metadata.sorted_tables if table.name != 'wind_info' and table.name != 'table_log']
    # metadata.drop_all(bind=db.engine, tables=tables_to_drop)

    # # Clear the metadata (optional, but keeps the state clean)
    # metadata.clear()

    # # Create a new session
    # Session = sessionmaker(bind=db.engine)
    # session = Session()

    # try:
    #     # Delete all rows from 'wind_info' table within a transaction
    #     session.execute(wind_info_table.delete())
    #     session.execute(table_log_table.delete())
    #     session.commit()
    # except Exception as e:
    #     # Rollback in case of error
    #     session.rollback()
    #     print(f"An error occurred: {e}")
    # finally:
    #     # Close the session
    #     print("Finished Deleting Tables")
    #     session.close()
    #     time.sleep(0.5)
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        try:
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Drop all tables except 'wind_info' and 'table_log'
            for table in tables:
                table_name = table[0]
                if table_name not in ['wind_info', 'table_log']:
                    quoted_table_name = f'"{table_name}"'
                    cursor.execute(f'DROP TABLE IF EXISTS {quoted_table_name};')
            
            # Delete all rows from 'wind_info' and 'table_log' tables
            cursor.execute("DELETE FROM wind_info;")
            cursor.execute("DELETE FROM table_log;")
            
            # Commit the changes
            db.commit()
            print("Finished Deleting Tables")
    
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            db.rollback()
        
        finally:
            # Close the connection
            cursor.close()
            db.close()
            time.sleep(0.5)
            
        init_db()
        
def read_meeting_info():
    global meeting_info
    """Read the meeting information from the JSON file."""
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r') as file:
            meeting_info = json.load(file)
    else:
        meeting_info = {"name": "", "track_path": "", "field_path": "", "workbook_path": ""}

def write_meeting_info(data):
    """Write the meeting information to the JSON file."""
    with open(JSON_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)

def clear_meeting_info():
    """Clear the meeting information in the JSON file."""
    data = {"name": "", "track_path": "", "field_path": "", "workbook_path": ""}
    write_meeting_info(data)
    
class Watcher:
    def __init__(self, directories_to_watch,workbook_path):
        self.observer = Observer()
        self.directories_to_watch = directories_to_watch
        self.workbook_path = workbook_path
        self.event_handler = Handler()

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
            if directory is not None and os.path.exists(str(directory)):
                self.observer.schedule(self.event_handler, directory, recursive=False)
        
        # Also watch the directory of the specific Excel file
        if directory is not None and os.path.exists(str(self.workbook_path)): 
            self.observer.schedule(self.event_handler, os.path.dirname(self.workbook_path), recursive=False)
            
        self.observer.start()

    def stop_observer(self):
        self.observer.stop()
        self.observer.join()

    def update_directories(self, new_directories, workbook_path):
        self.stop_observer()
        self.directories_to_watch = new_directories
        self.workbook_path = workbook_path
        self.observer = Observer()
        self.start_observer()

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    
class Handler(FileSystemEventHandler):
        
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type in ('modified', 'created', 'moved', 'deleted'):
            # print(f"Received {event.event_type} event - {event.src_path}")
            # if event.src_path.endswith('.lif'):
            #     last_inserted_file_lif = event.src_path
            # elif event.src_path.endswith('.lff'):
            #     last_inserted_file_lff = event.src_path
            
            
            #print(f"Received {event.event_type} event - {event.src_path}")
            # Check if the modified file is the specific Excel file
            if event.src_path.endswith('.xlsm') or event.src_path.endswith('.xlsx'):
                print(f"Excel macro book modified: {event.src_path}")
                with app.app_context():
                    insert_data_from_excel_to_db(meeting_info)
                    socketio.emit('file_changed', {'event': event.event_type, 'path': event.src_path})
                    
            elif event.src_path.endswith('.lff') or event.src_path.endswith('.lif'):
                with app.app_context():
                    read_meeting_info()
                    read_lif_lff_files(db, meeting_info)
                    #socketio.emit('message', last_inserted_file_lif if last_inserted_file_lif else last_inserted_file_lff, namespace='/stream')
                    socketio.emit('file_changed', {'event': event.event_type, 'path': event.src_path})
                    
@app.route('/', methods=['GET', 'POST'])
def index():    
    global watcher, db, meeting_info
    if request.method == 'POST':
        if 'submit' in request.form:
            meeting_info['name'] = request.form.get('meeting_name')
            meeting_info['track_path'] = request.form.get('track_path')
            meeting_info['field_path'] = request.form.get('field_path')
            meeting_info['workbook_path'] = request.form.get('workbook_path')
            
            meeting_info["workbook_path_check"] = request.form.get('workbook_path_check') == 'on'
            meeting_info["track_path_check"] = request.form.get('track_path_check') == 'on'
            meeting_info["field_path_check"] = request.form.get('field_path_check') == 'on'

            

            clear_meeting_info()
            write_meeting_info(meeting_info)
            
            #return redirect(url_for('index'))

            with app.app_context():
                db.create_all()
                drop_all_tables()
                message = read_lif_lff_files(db, meeting_info)
                excel_message = insert_data_from_excel_to_db(meeting_info)

            if message == "Success" and (excel_message == "Success" or excel_message == "Workbook path ignored"):
                print("Meeting Info: ", meeting_info)
                if watcher:
                    watcher.update_directories((meeting_info['track_path'], meeting_info['field_path']),meeting_info["workbook_path"])
                else:
                    watcher = Watcher((meeting_info['track_path'], meeting_info['field_path']),meeting_info["workbook_path"])
                    watcher_thread = threading.Thread(target=watcher.run)
                    watcher_thread.daemon = True
                    watcher_thread.start()
                    
                return redirect(url_for('dashboard'))
            else:
                flash(message, 'danger')
                flash(excel_message, 'danger')
                
                return redirect(url_for('index'))
            
        elif 'reset' in request.form:
            meeting_info['name'] = ''
            meeting_info['track_path'] = ''
            meeting_info['field_path'] = ''
            meeting_info['workbook_path'] = ''
            
            print(request.form)
        
        elif 'excel_submit' in request.form:
            subprocess.run(['dist/excel_file_dialog.exe'])
            
        return redirect(url_for('index'))
    
    #Ensure that the workbook path is saved to the list
    read_meeting_info()
    #clear_meeting_info()
    return render_template('index.html', meeting_info=meeting_info)

@app.route('/latest_tables')
def last_tables():
    
    tables_data = query_last_two_tables()

    print(tables_data)
    return render_template('latest_tables.html', tables=tables_data)

@app.route('/single_event/<event_type>')
def get_latest_table(event_type):
    #event_type = request.args.get('type')
    tables_data = query_last_two_tables()
    print(tables_data)
    if event_type == 'field':
        return render_template('single_file.html', event_type=event_type, table_name=list(tables_data.keys())[0], table_data=list(tables_data.values())[0])
    elif event_type == 'track':
        if len(list(tables_data.keys())) > 1: #* check if the returned tables include both track and event tables (length 2) or track only (len 1)
            return render_template('single_file.html', event_type=event_type ,table_name=list(tables_data.keys())[1], table_data=list(tables_data.values())[1])
        else:
            return render_template('single_file.html', event_type=event_type ,table_name=list(tables_data.keys())[0], table_data=list(tables_data.values())[0])

# @app.route('/dashboard')
# def dashboard():
#     #global db
#     with app.app_context():
#         track_events = []
#         field_events = []
#         tables = db.metadata.tables.keys()
#         wind_info_dict = {wi.table_name: wi.wind_value for wi in db.session.query(WindInfo).all()}

#         for table_name in tables:
#             if table_name == 'wind_info':
#                 continue

#             # table_class = db.Model.query_class(table_name)
#             # if table_class is None:
#             #     continue
#             table = db.metadata.tables[table_name]
#             event_name = ' '.join(table_name.split('_'))
#             results = db.session.query(table).all()
#             #print(results)
#             wind_value = wind_info_dict.get(table_name, "N/A")
#             event = {
#                 'name': event_name,
#                 'results': results,
#                 'wind_value': wind_value
#             }
#             pattern = re.compile(r'\b(Discus|Shot|Jump|Pole|Hammer|Throw|Javelin)\b', re.IGNORECASE)
#             if bool(pattern.search(event_name)): # ?Means it is a field table
#                 field_events.append(event)
#             else:
#                 track_events.append(event)
                
#     return render_template('dashboard.html', track_events=track_events,field_events=field_events, meeting_name=meeting_info['name'])
@app.route('/dashboard')
def dashboard():
    return render_dashboard_view(all=True)

@app.route('/dashboard/track')
def dashboard_track():
    return render_dashboard_view(track_only=True)

@app.route('/dashboard/field')
def dashboard_field():
    return render_dashboard_view(field_only=True)

# def render_dashboard_view(track_only=False, field_only=False):
#     with app.app_context():
#         track_events = []
#         field_events = []
#         tables = db.metadata.tables.keys()
#         wind_info_dict = {wi.table_name: wi.wind_value for wi in db.session.query(WindInfo).all()}

#         def split_table(results, max_rows=7):
#             """Split the table rows into multiple tables if they exceed max_rows."""
#             return [results[i:i + max_rows] for i in range(0, len(results), max_rows)]

#         # for table_name in tables:
#         #     if table_name == 'wind_info':
#         #         continue
#         #     table = db.metadata.tables[table_name]
#         #     event_name = ' '.join(table_name.split('_'))
#         #     results = db.session.query(table).all()
#         #     wind_value = wind_info_dict.get(table_name, "N/A")
#         #     event = {
#         #         'name': event_name,
#         #         'tables': split_table(results),# if len(results) > 10 else results,
#         #         'wind_value': wind_value
#         #     }
#         #     pattern = re.compile(r'\b(Discus|Shot|Jump|Pole|Hammer|Throw|Javelin)\b', re.IGNORECASE)
#         #     if bool(pattern.search(event_name)):  # Field event
#         #         field_events.append(event)
#         #     else:  # Track event
#         #         track_events.append(event)
        
#         for table_name in tables:
#             if table_name == 'wind_info' or table_name ==  "table_log":
#                 continue
#             table = db.metadata.tables[table_name]
#             event_name = ' '.join(table_name.split('_'))
#             results = db.session.query(table).all()
#             wind_value = wind_info_dict.get(table_name, "N/A")
#             split_tables = split_table(results)
#             for index, split_table_results in enumerate(split_tables):
#                 event = {
#                     'name': f"{event_name} (Part {index + 1})",
#                     'results': split_table_results,
#                     'wind_value': wind_value
#                 }
#                 pattern = re.compile(r'\b(Discus|Shot|Jump|Pole|Hammer|Throw|Javelin)\b', re.IGNORECASE)
#                 if bool(pattern.search(event_name)):  # Field event
#                     field_events.append(event)
#                 else:  # Track event
#                     track_events.append(event)
                
#         print(track_events, field_events)
#         return render_template('dashboard.html', track_events=track_events if not field_only else [], field_events=field_events if not track_only else [], meeting_name=meeting_info['name'])

def render_dashboard_view(track_only=False, field_only=False, all=False):
    read_meeting_info()
    
    track_events = []
    field_events = []

    db = get_db()
    
    # Get team names and points from match results table
    team_results = []
    try:
        team_results = db.cursor().execute("SELECT * FROM match_results").fetchall()
    except sqlite3.OperationalError as e:
        print("Excel Match Scoreboard table was not found and has been ignored.")
    print(team_results)

    def split_table(results, max_rows=16): #! Change here if the tables don't fit the viewport
        """Split the table rows into multiple tables if they exceed max_rows."""
        return [results[i:i + max_rows] for i in range(0, len(results), max_rows)]
    
    def check_name_columns_empty(rows, f_name_col, l_name_col):
        for row in rows:
            # Check if the column index is valid for the current row
            if f_name_col >= len(row) or l_name_col >= len(row):
                return False
            # Check if the cell in the specified column is not empty
            if row[f_name_col] + row[l_name_col] != "":
                return False
        return True
    # Fetch wind info data
    wind_info_dict = {}
    wind_info_query = 'SELECT table_name, wind_value FROM wind_info'
    for row in db.execute(wind_info_query):
        #print(row)
        wind_info_dict[row[0]] = row[1]

    # Get all table names
    tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
    tables = [row[0] for row in db.execute(tables_query) if row[0] not in ['wind_info', 'table_log', 'match_results']]

    for table_name in tables:
        event_name = ' '.join(table_name.split('_'))
        
        # Fetch table data
        table_query = f'SELECT * FROM "{table_name}"'
        results = [row for row in db.execute(table_query)]
        #print(results)
        wind_value = wind_info_dict.get(table_name, "N/A")
        split_tables = split_table(results)
        for index, split_table_results in enumerate(split_tables):
            event = {
                #'name': f"{event_name} (Part {index + 1})",
                'name': event_name,
                'results': split_table_results,
                'wind_value': wind_value
            }
            pattern = re.compile(r'\b(Discus|Shot|Long Jump|Triple Jump|High Jump|Pole|Hammer|Throw|Javelin)\b', re.IGNORECASE)
            match = pattern.search(event_name)
            if match:  # Field event
                #* Check if the matched word was "Jump"
                matched_event_name = match.group(1).lower()
                if matched_event_name == 'long jump' or matched_event_name == "triple jump":
                    event['is_jump'] = True
                    
                event['names_empty'] = check_name_columns_empty(event["results"],5,4)
                field_events.append(event)
            else:  # Track event
                event['names_empty'] = check_name_columns_empty(event["results"],4,3)
                track_events.append(event)

    #print(track_events, field_events)
    if all:
        return render_template('dashboard.html', track_events=track_events, field_events=field_events , meeting_name=meeting_info['name'], team_results=team_results,meeting_info=meeting_info)
    else:
        return render_template('dashboard.html', track_events=track_events if not field_only else [], field_events=field_events if not track_only else [], meeting_name=meeting_info['name'],team_results=team_results, meeting_info=meeting_info)

@app.route('/get_events')
def get_events():
    read_meeting_info()
    
    events = []
    for filename in os.listdir(meeting_info['field_path']):
        if filename.endswith('.lff'):  # Assuming the files are .txt
            with open(os.path.join(meeting_info['field_path'], filename), 'r') as file:
                event_name_parts = file.readline().strip().split(',')
                event_name = event_name_parts[0] + ' ' + event_name_parts[3]
                events.append({'filename': filename, 'event_name': event_name})
    return jsonify(events)

@app.route('/events_page', methods=['POST', 'GET'])
def export_lffs():
    read_meeting_info()
    
    if request.method == 'POST':
        selected_files = request.json.get('selected_files', [])
        meeting_name = request.json.get('meeting_name', meeting_info['name'])
        venue_name = request.json.get('venue_name', meeting_info['name'])
        
        btn_name = request.json.get('button_name')
        
        try:
            html_files = []
            if btn_name == "from_lffs_btn":
                html_files = export_fieldcards_to_pdf(meeting_name, venue_name,meeting_info["field_path"],selected_files,None)
            elif btn_name == "from_evt_btn":
                html_files = export_evt_to_pdf(meeting_name, venue_name, meeting_info["field_path"])
            #print(html_files)
            # flash(f"Files processed successfully {selected_files}", 'info')
            # return redirect(url_for('export_lffs'))
            return jsonify({"message": "Files processed successfully", "html_files": [f'/static/generated_files/{os.path.basename(path)}' for path in html_files]})
        except Exception as e:
            print(e)
            return jsonify({"message": f"Error processing files: {str(e)}"}), 500
    else:
        return render_template('export_lffs.html',meeting_info=meeting_info)

@app.route('/excel_path')
def get_excel_path():
    subprocess.run(['dist/excel_file_dialog.exe'])
    return redirect(url_for('index'))

@app.route('/refresh_tables')
def refresh_tables():
    read_meeting_info()
    
    message = read_lif_lff_files(db, meeting_info)
    insert_data_from_excel_to_db(meeting_info)
    
    flash(f"Message: {message}")
    return redirect(url_for('dashboard'))
    
    

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            message = app.config['SSE_QUEUE'].get()
            yield f'data: {message}\n\n'
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    #app.run(debug=True)
    #waitress.serve(app, host="0.0.0.0", port=5000, threads=1000)
    #clear_meeting_info() #Optional to remove any paths saved in the json file after the app was terminated
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
