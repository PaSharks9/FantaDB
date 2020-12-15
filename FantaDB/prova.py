import pyodbc
import sqlalchemy as sal
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
import pandas as pd
from flask import render_template, request, redirect, url_for, Flask
# from FantaDB import app
import random


app = Flask(__name__)

engine = sal.create_engine('mssql+pyodbc://MSI/FantaDB?trusted_Connection=yes&driver=SQL+Server+Native+Client+11.0')
# meta = MetaData()
# print(engine.table_names())

# fantaAllenatori= Table(
#    'FantaAllenatori', meta,
#    Column('id', Integer, primary_key=True),
#    Column('Email', String),
#    Column('Username', String),
#    )
# meta.create_all(engine)

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == "GET":
        return render_template('prova.html')
    else:
        IdAllenatore = random.randint(0,10)
        tables = engine.table_names()
        
        for el in tables: 
            with engine.connect() as connection:
                with connection.begin():  # connection.begin ritorna un oggetto Transaction
                    connection.execute("insert into FantaAllenatori values (IdAllenatore, 'lucapasqua9@gmail.com', 'BFCBulagna')")
                    connection.execute(el.insert(), {'id': IdAllenatore , 'Email': 'lucapasqua9@gmail.com', 'Username': 'BFCBulagna'})
            print("FantaAllenatori non trovati")
        return render_template('prova.html')


if __name__ == "__main__":
    app.run(debug=False)