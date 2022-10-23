from flask import Flask, request, jsonify
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from
import re
import sqlite3
from unidecode import unidecode
import pandas as pd

app = Flask(__name__)
app.json_encoder = LazyJSONEncoder

swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API for Cleansing Text'),
    'version': LazyString(lambda: '1'),
    'description': LazyString(lambda: 'cleansing text'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config)

conn = sqlite3.connect("db_challenge.db", check_same_thread=False)
mycur = conn.cursor()
mycur.execute("DROP TABLE IF EXISTS cleanData")
mycur.execute("DROP TABLE IF EXISTS rawData")
mycur.execute("CREATE TABLE IF NOT EXISTS cleaning_text(raw_text varchar(50), clean_text varchar(50))")

def remove_punct(text):
    return re.sub(r"[^\w\d\s]", "", text)

def replace_ascii(text):
    return unidecode(text)

def replace_ascii2(text):
    return re.sub(r"\\x[A-Za-z0-9./]", "", unidecode(text))

def remove_newline(text):
    return re.sub('\n', '', text)

@app.route("/", methods=['GET'])
def main():
    return 'Homepage'

@swag_from("swagger_config.yml", methods=['POST'])
@app.route("/remove_punct/v1", methods=['POST'])
def remove_punct_posts():
    text = request.get_json()
    non_punct = remove_newline(text['text'])
    non_punct = replace_ascii(non_punct)
    non_punct = replace_ascii2(non_punct)
    non_punct = remove_punct(non_punct)

    data = [(text['text']), non_punct]
    mycur.executemany("INSERT INTO cleaning_text(raw_text, clean_text) VALUES(?,?)", [data])
    conn.commit()
    return jsonify({"clean_result":non_punct})

@swag_from("swagger_config_file.yml", methods=['POST'])
@app.route("/remove_punct_file", methods=['POST'])
def upload_file():
    file_input = request.files['file']
    df = pd.read_csv(file_input, encoding="ISO-8859-1", sep=",")
    mycur.execute("CREATE TABLE IF NOT EXISTS rawData(rawText varchar(255))")
    mycur.execute("CREATE TABLE IF NOT EXISTS cleanData(cleanText varchar(255))")
    df['Tweet'].to_sql('rawData', con=conn, if_exists='replace',index_label='id')
    for index, row in df.iterrows():
        text = row['Tweet']
        clean_text = replace_ascii(text)
        clean_text = replace_ascii2(clean_text)
        clean_text = remove_newline(clean_text)
        clean_text = remove_punct(clean_text)
        mycur.execute("INSERT INTO cleanData(cleanText) VALUES(?)", [clean_text])
        conn.commit()
        print(clean_text)
    resp = jsonify({'message' : 'File successfully uploaded'})
    resp.status_code = 201
    return resp

if __name__ == "__main__":
    app.run(port=1234, debug=True)