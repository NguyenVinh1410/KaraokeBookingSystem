from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key-demo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abc123@localhost/bookingdb?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)