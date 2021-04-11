from typing import Sized
from flask import Flask, render_template, redirect, url_for, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
import os, subprocess
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/test.db'
db = SQLAlchemy(app)

def init():
    db.create_all()

app.secret_key = b"random bytes representing flask secret key"
# OAuth2 must make use of HTTPS in production environment.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"      # !! Only in development environment.

app.config["DISCORD_CLIENT_ID"] = 830237179980152843    # Discord client ID.
app.config["DISCORD_CLIENT_SECRET"] = "3zlxShOIz-fyYsL4WitzO8K_1Z7Fde1k"                # Discord client secret.
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"                 # URL to your callback endpoint.

CORS(app)

discord = DiscordOAuth2Session(app)


@app.route("/login/")
def login():
    return discord.create_session()

@app.route("/callback/")
def callback():
    discord.callback()
    return redirect(url_for(".admin"))


@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for("login"))

class Mirror(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    href = db.Column(db.String(120), unique=True, nullable=False)
    size = db.Column(db.String(120), unique=False, nullable=False)
    synctime = db.Column(db.String(120), unique=False, nullable=False)
    path = db.Column(db.String(120), unique=False, nullable=False)

    def __repr__(self):
        return '<Mirror Name %r>' % self.name

@app.route('/')
def index():
    Mirrors = Mirror.query.all()
    return render_template('mirrorlist.html', cards=Mirrors)


@app.route('/admin', methods=["GET", "POST"])
@requires_authorization
def admin():
    user = discord.fetch_user()
    if user.id != 484040243818004491:
        abort(418)

    if request.method == "GET":
        Mirrors = Mirror.query.all()
        return render_template('admin.html', user=user, mirrors=Mirrors, updatedSize=request.args.get('updatedSize'))

    if request.method == "POST":
        mirrorEntry = Mirror(name=request.form['name'], href=request.form['href'], size=request.form['size'], synctime=request.form['synctime'], path=request.form['path'])
        db.session.add(mirrorEntry)
        db.session.commit()
        Mirrors = Mirror.query.all()
        return render_template('admin.html', user=user, mirrors=Mirrors)

@app.route('/admin/updateSize', methods=["GET", "POST"])
@requires_authorization
def updateSize():
    Mirrors = Mirror.query.all()
    for mirror in Mirrors:
        size = getSize(mirror.path)
        mirror = Mirror.query.filter_by(name=mirror.name).first()
        mirror.size = size
        db.session.commit()
    
    return redirect(url_for('admin', updatedSize=True))

def getSize(path):
    size = subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8')
    return size

if __name__ == '__main__':
    init()
    app.run(debug=True)

