import pandas as pd
import numpy as np
import re
import os
from google.cloud.sql.connector import connector

creds_file = "assets/t-scholar-233105-70deda761f56.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file

def create_connection_with_db():
    conn = connector.connect("t-scholar-233105:us-central1:project1050", "pg8000", 
                            user="postgres", password="tempPassword123", db="project")
    cursor = conn.cursor()
    return conn, cursor

def fetch_entire_tables():
    conn, cur = create_connection_with_db()
    cur.execute("SELECT * FROM covid_data")
    data = pd.DataFrame(cur.fetchall(), columns=[x[0] for x in cur.description])
    cur.execute("SELECT * FROM covid_data_latest")
    data2 = pd.DataFrame(cur.fetchall(), columns=[x[0] for x in cur.description])
    conn.close()
    return data, data2

