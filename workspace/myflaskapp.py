from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    app.run(host='0.0.0.0')

@app.route('/')
def index():
    return "<span style='color:red'>I am app 1</span>"

# uwsgi --socket 127.0.0.1:7000 --wsgi-file myflaskapp.py --callable app --processes 4 --threads 2 --stats 127.0.0.1:9191es 4 --threads 2 --stats 127.0.0.1:9191