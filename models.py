from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class WindInfo(db.Model):
    __tablename__ = 'wind_info'

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False)
    wind_value = db.Column(db.String(100), nullable=False)

    def __init__(self, table_name, wind_value):
        self.table_name = table_name
        self.wind_value = wind_value

    def __repr__(self):
        return f'<WindInfo {self.table_name!r}>'

class TableLog(db.Model):
    __tablename__ = 'table_log'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String, nullable=False)
    heat_no = db.Column(db.String, nullable=False)
    insert_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TableLog {self.table_name} {self.insert_time}>"
    
# class TableEvent(db.Model):
#         __table_args__ = {'extend_existing': True}

#         id = db.Column(db.Integer, primary_key=True)
#         position = db.Column(db.Integer)
#         bib_no = db.Column(db.Integer)
#         first_name = db.Column(db.String)
#         last_name = db.Column(db.String)
#         team = db.Column(db.String)
#         time = db.Column(db.String)

#         def __init__(self, event_name, class_name):
#             self.__tablename__ = event_name.replace(" ", "_") #TODO Check for spaces in titles
#             self.class_name = class_name

#         def __repr__(self):
#             return f"<{self.class_name} {self.first_name} {self.last_name}>"