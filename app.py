import datetime
import json
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, jsonify, Response, g
from flask_session import Session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required


app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

CORS(app)
Session(app)

usernameGlobal = ''
typesNames = ['Fire', 'Grass', 'Water', 'Normal', 'Bug', 'Poison', 'Electric',
                  'Fighting', 'Ground', 'Rock', 'Psychic', 'Ice', 'Dragon', 'Ghost', 'Fairy']
openedPacksData = []
con = sqlite3.connect(
    r"C:\xampp\htdocs\phpLiteAdmin\pokebum2", check_same_thread=False)
cur = con.cursor()


@app.before_request
def before_request():
    g.username = usernameGlobal


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def getBacks():
    backData = {}
    for name in typesNames:
        typeDataUnrender = cur.execute(
            f"SELECT * FROM 'backgrounds' WHERE type = '{name}'")
        typeData = typeDataUnrender.fetchall()
        for data in typeData:
                backData[f'{name}'] = data[1]
    return backData

def createTypes():
    backData = getBacks()
    cardsOwned = getOwnedCards()
    
    typesData = {}

    for name in typesNames:
        typeDataUnrender = cur.execute(
            f"SELECT * FROM 'pokemons' WHERE type = '{name}'")
        typeData = typeDataUnrender.fetchall()
        typesData[f'{name}'] = []
        for data in typeData:
            if data[2] == name:
                value = {'id': data[0], 'name': data[1],
                         'type': data[2], 'card': data[3], 'back': backData[f'{name}']}
                if value['id'] not in cardsOwned:
                    value['card'] = ''
                typesData[f'{name}'].append(value)
    return typesData

def getUserPacks():
    packsUR = cur.execute(
            "SELECT packsAmount FROM users WHERE username = ?", (usernameGlobal,))
    userPacks = packsUR.fetchall()
    return userPacks

def getOwnedCards():
    userIdUR = cur.execute("SELECT id FROM users WHERE username = ?", (usernameGlobal,))
    userId = userIdUR.fetchall()
    
    cardsOwnedUR = cur.execute("SELECT pokemonId FROM cardsFound WHERE userId = ?", (userId[0][0],))
    cardsOwnedAll = cardsOwnedUR.fetchall()
    cardsOwned = []
        
    for card in cardsOwnedAll:
        cardsOwned.append(card[0])
    return cardsOwned

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
    lastPackUnrender = cur.execute(
        "SELECT lastPack FROM users WHERE username = ?", (usernameGlobal,))
    lastPack = lastPackUnrender.fetchall()
    return render_template("index.html", data=lastPack[0][0])


@app.route("/claim", methods=["POST", "GET"])
def claim():
    if request.method == 'POST':
        userPacks = getUserPacks()
        date = datetime.datetime.now()
        date_time = date.strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("UPDATE users SET lastPack = ? WHERE username = ?",
                    (date_time, usernameGlobal))

        cur.execute("UPDATE users SET packsAmount = ? WHERE username = ?",
                    (userPacks[0][0] + 1, usernameGlobal))
        con.commit()
    return redirect("/packs")


@app.route("/login", methods=["POST", "GET"])
def login():

    # Forget any user_id
    session.clear()
    errorMessage = ''
    username = request.form.get("username")
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            errorMessage = "Must provide a username"
            return render_template("register.html", error=errorMessage)

        # Ensure password was submitted
        elif not request.form.get("password"):
            errorMessage = "Must provide a password"
            return render_template("register.html", error=errorMessage)

        # Query database for username
        rowsUnrendered = cur.execute(
            "SELECT * FROM users WHERE username = ?", (username,))
        rows = rowsUnrendered.fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], (request.form.get("password"))):
            errorMessage = "Invalid username and/or password"
            return render_template("login.html", error=errorMessage)

        # Remember which user has logged in

        session["user_id"] = rows[0][0]
        global usernameGlobal
        usernameGlobal = rows[0][1]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        passwords = [request.form.get(
            "password"), request.form.get("confirmation")]
        usernamesUnrender = cur.execute("SELECT username FROM users")
        usernames = usernamesUnrender.fetchall()
        usernamesList = []

        for user in usernames:
            u = user[0]
            usernamesList.append(u)

        errorMessage = ''
        if name == '' or name in usernamesList:
            errorMessage = "Type in an username or select one that isnt already in use"
            return render_template("register.html", error=errorMessage)

        if passwords[0] != passwords[1]:
            errorMessage = "Your passwords don't match"
            return render_template("register.html", error=errorMessage)
        elif passwords[0] == '' or passwords[1] == '':
            errorMessage = "One or both of your password fields are empty"
            return render_template("register.html", error=errorMessage)

        hash = generate_password_hash(
            passwords[0], method='pbkdf2:sha256', salt_length=8)
        cur.execute(
            f"INSERT INTO users (username, password, packsAmount) VALUES (?, ?, ?)", (name, hash, 0))
        con.commit()
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/packs", methods=["GET", "POST"])
@login_required
def packs():
    session.pop('reloaded', None)
    packsUR = cur.execute(
        "SELECT packsAmount FROM users WHERE username = ?", (usernameGlobal,))
    userPacks = packsUR.fetchall()
    lastPackUnrender = cur.execute(
        "SELECT lastPack FROM users WHERE username = ?", (usernameGlobal,))
    lastPack = lastPackUnrender.fetchall()
    return render_template("packs.html", data=lastPack[0][0], userPacks=userPacks[0][0])


@app.route("/openedPacks", methods=["GET", "POST"])
@login_required
def openedPacks():    
  
    userIdUR = cur.execute("SELECT id FROM users WHERE username = ?", (usernameGlobal,))
    userId = userIdUR.fetchall()
    
    packsUR = cur.execute(
        "SELECT packsAmount FROM users WHERE username = ?", (usernameGlobal,))
    userPacks = packsUR.fetchall()
    
    backs = getBacks()
    
    if request.method == "GET":
        if 'reloaded' in session:
            session.pop('reloaded', None)
            return redirect("/packs")
        if request.method == "POST":
            session.pop('reloaded', None)
            return redirect("/packs")

        session['reloaded'] = True
        
        typeDataUnrender = cur.execute(
                "SELECT * FROM pokemons ORDER BY RANDOM() LIMIT 5;")
        typeData = typeDataUnrender.fetchall()
        
        userPacks = getUserPacks()
        
        global openedPacksData
        openedPacksData = typeData
        
        cur.execute("UPDATE users SET packsAmount = ? WHERE username = ?",
                        (userPacks[0][0] - 1, usernameGlobal))
        con.commit()
        return render_template("openedPacks.html", pokeData=openedPacksData, backgrounds=backs)
    if request.method == "POST":
        ids = []
        for type in openedPacksData:
            ids.append(type[0])
            
        cardsOwned = getOwnedCards()
        for id in ids:
            if id in cardsOwned:
                continue
            cur.execute("INSERT INTO cardsFound (pokemonId, userId) VALUES (?, ?)", (id, userId[0][0]))
            con.commit()
        return redirect("/packs")
    
if __name__ == '__main__':
    app.run()