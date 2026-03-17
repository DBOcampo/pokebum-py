import datetime
from flask import Flask, flash, redirect, render_template, request, session, jsonify, g
from flask_session import Session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "pokebum_secret")

CORS(app)
Session(app)

# Connection pool - evita el problema de max connections
db_pool = pooling.MySQLConnectionPool(
    pool_name="pokebum_pool",
    pool_size=5,
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_DATABASE")
)

def get_db():
    if "db" not in g:
        g.db = db_pool.get_connection()
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

usernameGlobal = ''
typesNames = ['Fire', 'Grass', 'Water', 'Normal', 'Bug', 'Poison', 'Electric',
              'Fighting', 'Ground', 'Rock', 'Psychic', 'Ice', 'Dragon', 'Ghost', 'Fairy']
openedPacksData = []


@app.before_request
def before_request():
    g.username = usernameGlobal


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def getBacks():
    con = get_db()
    cur = con.cursor()
    backData = {}
    for name in typesNames:
        cur.execute("SELECT * FROM backgrounds WHERE type = %s", (name,))
        typeData = cur.fetchall()
        for data in typeData:
            backData[name] = data[1]
    return backData


def createTypes():
    con = get_db()
    cur = con.cursor()
    backData = getBacks()
    cardsOwned = getOwnedCards()
    typesData = {}

    for name in typesNames:
        cur.execute("SELECT * FROM pokemons WHERE type = %s", (name,))
        typeData = cur.fetchall()
        typesData[name] = []
        for data in typeData:
            if data[2] == name:
                value = {'id': data[0], 'name': data[1],
                         'type': data[2], 'card': data[3], 'back': backData.get(name, '')}
                if value['id'] not in cardsOwned:
                    value['card'] = ''
                typesData[name].append(value)
    return typesData


def getUserPacks():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT packsAmount FROM users WHERE username = %s", (usernameGlobal,))
    userPacks = cur.fetchall()
    return userPacks


def getOwnedCards():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT id FROM users WHERE username = %s", (usernameGlobal,))
    userId = cur.fetchall()
    if not userId:
        return []
    cur.execute("SELECT pokemonId FROM cardsFound WHERE userId = %s", (userId[0][0],))
    cardsOwnedAll = cur.fetchall()
    return [card[0] for card in cardsOwnedAll]


@app.route("/")
@login_required
def mainPage():
    return render_template("mainPage.html")


@app.route('/route/to/data')
def get_data():
    Ghosts = createTypes()
    return jsonify(Ghosts)


@app.route("/store")
@login_required
def store():
    return render_template("store.html")


@app.route('/logout')
def logout():
    session.clear()
    return render_template("login.html")


@app.route("/album")
@login_required
def album():
    Ghosts = createTypes()
    return render_template("album.html", ghosts=Ghosts)


@app.route("/index")
def index():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT lastPack FROM users WHERE username = %s", (usernameGlobal,))
    lastPack = cur.fetchall()
    return render_template("index.html", data=lastPack[0][0])


@app.route("/claim", methods=["POST", "GET"])
def claim():
    if request.method == 'POST':
        con = get_db()
        cur = con.cursor()
        userPacks = getUserPacks()
        date = datetime.datetime.now()
        date_time = date.strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("UPDATE users SET lastPack = %s WHERE username = %s", (date_time, usernameGlobal))
        cur.execute("UPDATE users SET packsAmount = %s WHERE username = %s", (userPacks[0][0] + 1, usernameGlobal))
        con.commit()
    return redirect("/packs")


@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()
    errorMessage = ''
    username = request.form.get("username")

    if request.method == "POST":
        if not request.form.get("username"):
            errorMessage = "Must provide a username"
            return render_template("login.html", error=errorMessage)
        elif not request.form.get("password"):
            errorMessage = "Must provide a password"
            return render_template("login.html", error=errorMessage)

        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        rows = cur.fetchall()

        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            errorMessage = "Invalid username and/or password"
            return render_template("login.html", error=errorMessage)

        session["user_id"] = rows[0][0]
        global usernameGlobal
        usernameGlobal = rows[0][1]
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        con = get_db()
        cur = con.cursor()
        name = request.form.get("username")
        passwords = [request.form.get("password"), request.form.get("confirmation")]

        cur.execute("SELECT username FROM users")
        usernames = [user[0] for user in cur.fetchall()]

        errorMessage = ''
        if name == '' or name in usernames:
            errorMessage = "Type in a username or select one that isn't already in use"
            return render_template("register.html", error=errorMessage)
        if passwords[0] != passwords[1]:
            errorMessage = "Your passwords don't match"
            return render_template("register.html", error=errorMessage)
        elif passwords[0] == '' or passwords[1] == '':
            errorMessage = "One or both of your password fields are empty"
            return render_template("register.html", error=errorMessage)

        hash = generate_password_hash(passwords[0], method='pbkdf2:sha256', salt_length=8)
        cur.execute("INSERT INTO users (username, password, packsAmount) VALUES (%s, %s, %s)", (name, hash, 0))
        con.commit()
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/packs", methods=["GET", "POST"])
@login_required
def packs():
    session.pop('reloaded', None)
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT packsAmount FROM users WHERE username = %s", (usernameGlobal,))
    userPacks = cur.fetchall()
    cur.execute("SELECT lastPack FROM users WHERE username = %s", (usernameGlobal,))
    lastPack = cur.fetchall()
    return render_template("packs.html", data=lastPack[0][0], userPacks=userPacks[0][0])


@app.route("/openedPacks", methods=["GET", "POST"])
@login_required
def openedPacks():
    con = get_db()
    cur = con.cursor()

    cur.execute("SELECT id FROM users WHERE username = %s", (usernameGlobal,))
    userId = cur.fetchall()

    backs = getBacks()

    if request.method == "GET":
        if 'reloaded' in session:
            session.pop('reloaded', None)
            return redirect("/packs")

        session['reloaded'] = True
        cur.execute("SELECT * FROM pokemons ORDER BY RAND() LIMIT 5")
        typeData = cur.fetchall()

        userPacks = getUserPacks()

        global openedPacksData
        openedPacksData = typeData

        cur.execute("UPDATE users SET packsAmount = %s WHERE username = %s",
                    (userPacks[0][0] - 1, usernameGlobal))
        con.commit()
        return render_template("openedPacks.html", pokeData=openedPacksData, backgrounds=backs)

    if request.method == "POST":
        ids = [type[0] for type in openedPacksData]
        cardsOwned = getOwnedCards()
        for id in ids:
            if id in cardsOwned:
                continue
            cur.execute("INSERT INTO cardsFound (pokemonId, userId) VALUES (%s, %s)", (id, userId[0][0]))
        con.commit()
        return redirect("/packs")


if __name__ == '__main__':
    app.run(debug=True)