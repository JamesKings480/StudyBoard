from flask import Flask
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


@app.route('/')
def index():
    return '<h1>Studyboard</h1><p>App is running.</p>'


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)