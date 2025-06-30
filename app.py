
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Sistema de Produtividade online com sucesso via Render!"
