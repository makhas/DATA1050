import pandas as pd
import numpy as np
import re
import os
from cryptography.fernet import Fernet
from google.cloud.sql.connector import connector

def decrypt(filename, key):
    f = Fernet(key)
    with open(filename, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = f.decrypt(encrypted_data)
    with open("GAC.json", "wb") as file:
        file.write(decrypted_data)

def create_connection_with_db():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "GAC.json"
    HOST = "t-scholar-233105:us-central1:project1050"
    DB_USER = "postgres"
    PORT = "pg8000"
    DB_PASS = "tempPassword123"
    DB_NAME = "project"
    conn = connector.connect(HOST, PORT, 
                            user=DB_USER, password=DB_PASS, db=DB_NAME)
    cursor = conn.cursor()
    return conn, cursor

def fetch_entire_tables():
    KEY = os.getenv("KEY")
    decrypt("gacc", KEY)
    conn, cur = create_connection_with_db()
    cur.execute("SELECT * FROM covid_data")
    data = pd.DataFrame(cur.fetchall(), columns=[x[0] for x in cur.description])
    cur.execute("SELECT * FROM covid_data_latest")
    data2 = pd.DataFrame(cur.fetchall(), columns=[x[0] for x in cur.description])
    conn.close()
    os.remove("GAC.json")
    return data, data2

def fetch_data_from_website():
    url = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
    df = pd.read_csv(url)
    df['location'] = df['location'].apply(lambda x: x.replace("'", "")) # Handling Cote d'Ivoire -> breaks the insert query
    url = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.csv"
    df2 = pd.read_csv(url)
    df2['location'] = df2['location'].apply(lambda x: x.replace("'", "")) # Handling Cote d'Ivoire -> breaks the insert query
    return df, df2

def fetch_entire_tables_old():
    data, data2 = fetch_data_from_website()
    return data, data2
