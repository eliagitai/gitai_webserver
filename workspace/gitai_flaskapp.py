from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    app.run(host='0.0.0.0')

@app.route('/')
def index():
    return "<span style='color:red'>I am a Python Flask app</span>"

#  uwsgi --socket gitai_site.sock --wsgi-file gitai_flaskapp.py --callable app --processes 4 --threads 2 --chmod-socket=666 --stats :9000