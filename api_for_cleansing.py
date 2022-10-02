from cgitb import text
from msilib.schema import tables
from flask import Flask, request, jsonify
import re
import sqlite3

app = Flask(__name__)

conn = sqlite3.connect("db_challenge.db", check_same_thread=False)
mycur = conn.cursor()

def create_table():
    mycur.execute("CREATE TABLE IF NOT EXISTS cleaning_text(raw_text varchar(50), clean_text varchar(50))")

def remove_punct(text):
    # Remove angka termasuk angka yang berada dalam string
    # Remove non ASCII chars
    text = re.sub(r'[^\x00-\x7f]', r'', text)
    text = re.sub(r'(\\u[0-9A-Fa-f]+)', r'', text)
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    # text = re.sub(r'\\u\w\w\w\w', '', text)
    # Remove simbol, angka dan karakter aneh
    text = re.sub(r"[.,:;+!\-_<^/=?\"'\(\)\d\*]", "", text)
    return text

@app.route("/remove_punct/v1", methods=['POST'])
def remove_punct_posts():
    text = request.get_json()
    non_punct = remove_punct(text['text'])

    data = [(text['text']), non_punct]
    mycur.executemany("INSERT INTO cleaning_text(raw_text, clean_text) VALUES(?,?)", [data])
    conn.commit()
    return jsonify({"clean_result":non_punct})

if __name__ == "__main__":
    app.run(port=1234, debug=True)