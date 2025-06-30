
from flask import Flask, render_template, request, redirect, url_for, session
import bcrypt
import datetime

app = Flask(__name__)
app.secret_key = 'ursao_seguro_123'

# Usuários de exemplo (substituir depois por banco de dados)
usuarios = {
    '123': {
        'senha': bcrypt.hashpw('senha123'.encode('utf-8'), bcrypt.gensalt()),
        'nome': 'João da Silva',
        'meta': 2000,
        'pontos': 1800,
        'estoque': 250
    },
    '456': {
        'senha': bcrypt.hashpw('senha456'.encode('utf-8'), bcrypt.gensalt()),
        'nome': 'Maria Oliveira',
        'meta': 1500,
        'pontos': 1600,
        'estoque': 100
    }
}

def registrar_acesso(matricula, ip):
    agora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("acessos.log", "a") as f:
        f.write(f"{agora} - Matrícula {matricula} acessou do IP {ip}\n")

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        matricula = request.form["matricula"]
        senha = request.form["senha"]
        if matricula in usuarios and bcrypt.checkpw(senha.encode('utf-8'), usuarios[matricula]["senha"]):
            session["matricula"] = matricula
            ip = request.remote_addr
            registrar_acesso(matricula, ip)
            return redirect(url_for("painel"))
        else:
            return render_template("login.html", erro="Matrícula ou senha inválida.")
    return render_template("login.html")

@app.route("/painel")
def painel():
    if "matricula" not in session:
        return redirect(url_for("login"))
    matricula = session["matricula"]
    dados = usuarios[matricula]
    return render_template("painel.html", nome=dados["nome"], meta=dados["meta"],
                           pontos=dados["pontos"], estoque=dados["estoque"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
