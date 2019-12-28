from flask import Flask, render_template, request, session, redirect, url_for
from models import db, User, Place, Products, Categories
from forms import SignupForm, LoginForm, AddressForm, SearchForm
from logging.handlers import RotatingFileHandler
import urllib.request
import geocoder
import configparser
import logging
import json


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///var/store.db'
db.init_app(app)

app.secret_key = app.config['SECRET_KEY']

@app.route("/")
def index():
    this_route = url_for('.index')
    app.logger.info("Logging a test message from {}".format(this_route))
    return render_template("index.html")

@app.route("/about")
def about():
    this_route = url_for('.about')
    app.logger.info("Logging a test message from {}".format(this_route))
    return render_template("about.html")

@app.route("/contact")
def contact():
    this_route = url_for('.contact')
    app.logger.info("Logging a test message from {}".format(this_route))
    return render_template("contact.html")

@app.route("/map", methods=["GET", "POST"])
def map():
    this_route = url_for('.map')
    if 'email' not in session:
        app.logger.info("Logging a test message from {}".format(this_route))
        return redirect(url_for('login'))

    form = AddressForm()

    places = []
    ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    g = geocoder.ip(ip)
    my_coordinates = (g.lat, g.lng)

    if request.method == 'POST':
        if form.validate() == False:
            app.logger.info("Logging a test message from {}".format(this_route))
            return render_template('map.html', form=form)
        else:
            # get the address
            address = form.address.data
            # query for places around it
            p = Place()
            my_coordinates = p.address_to_latlng(address)
            places = p.query(address)
            app.logger.info("Logging a test message from {}".format(this_route))
            # return those results
            return render_template('map.html', form=form, my_coordinates=my_coordinates, places=places)

    elif request.method == 'GET':
        app.logger.info("Logging a test message from {}".format(this_route))
        return render_template("map.html", form=form, my_coordinates=my_coordinates, places=places)

    app.logger.info("Logging a test message from {}".format(this_route))
    return render_template("map.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    this_route = url_for('.signup')
    if 'email' in session:
        app.logger.info("Logging a test message from {}".format(this_route))
        return redirect(url_for('home'))

    form = SignupForm()

    if request.method == "POST":
        if form.validate() == False:
            app.logger.info("Logging a test message from {}".format(this_route))
            return render_template('signup.html', form=form)
        else:
            newuser = User(form.first_name.data, form.last_name.data, form.email.data, form.password.data)
            db.session.add(newuser)
            db.session.commit()

            session['email'] = newuser.email
            app.logger.info("Logging a test message from {}".format(this_route))
            return redirect(url_for('home'))

    elif request.method == "GET":
        app.logger.info("Logging a test message from {}".format(this_route))
        return render_template('signup.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    this_route = url_for('.login')
    if 'email'in session:
        app.logger.info("Logging a test message from {}".format(this_route))
        return redirect(url_for('home'))

    form = LoginForm()

    if request.method == "POST":
        if form.validate() == False:
            app.logger.info("Logging a test message from {}".format(this_route))
            return render_template("login.html", form=form)
        else:
            email = form.email.data
            password = form.password.data

            user = User.query.filter_by(email=email).first()
            if user is not None and user.check_password(password):
                session['email'] = form.email.data
                app.logger.info("Logging a test message from {}".format(this_route))
                return redirect(url_for('home'))
            else:
                app.logger.info("Logging a test message from {}".format(this_route))
                return redirect(url_for('login'))

    elif request.method == 'GET':
        app.logger.info("Logging a test message from {}".format(this_route))
        return render_template('login.html', form=form)

@app.route("/logout")
def logout():
    this_route = url_for('.logout')
    session.pop('email', None)
    app.logger.info("Logging a test message from {}".format(this_route))
    return redirect(url_for('index'))

@app.route("/home/", methods=["GET", "POST"])
def home():
    this_route = url_for('.home')
    if 'email' not in session:
        app.logger.info("Logging a test message from {}".format(this_route))
        return redirect(url_for('login'))

    form = SearchForm()

    c = Categories()
    categories = c.return_categories()

    p = Products()
    #c = Categories()

    category = request.args.get('category')
    if category != None:
        #products = p.search_query("", )
        count = 0
        for cat in categories:
            for each in cat:
                if count == 0:
                    if category == each['category']:
                        print("CAT: ", each)
                else:
                    if category == each['subcat']:
                        products = p.search_query("", each['sub_id'])

                        app.logger.info("Logging a test message from {}".format(this_route))
                        return render_template('home.html', form=form, products=products, categories=categories)

                count += 1
            count = 0



    if request.method == "POST":
        if form.validate() == False:
            app.logger.info("Logging a test message from {}".format(this_route))
            return render_template("home.html", form=form, categories=categories)
        else:
            query = form.query.data

            cat_id = request.form.get("categories")

            products = p.search_query(query, cat_id)
            #categories = c.return_categories()

            app.logger.info("Logging a test message from {}".format(this_route))
            return render_template('home.html', form=form, products=products, categories=categories)

    elif request.method == 'GET':
        app.logger.info("Logging a test message from {}".format(this_route))
        return render_template('home.html', form=form, categories=categories)



@app.errorhandler(404)
def page_not_found(error):
    return "You are lost, Traveller.", 404

def init(app):
    config = configparser.ConfigParser()
    try:
        config_location = "etc/defaults.cfg"
        config.read(config_location)

        app.config['DEBUG'] = config.get("config", "debug")
        app.config['SECRET_KEY'] = config.get("config", "secret_key")
        app.config['LOG_FILE'] = config.get("logging", "name")
        app.config['LOG_LOCATION'] = config.get("logging", "location")
        app.config['LOG_LEVEL'] = config.get("logging", "level")
    except:
        print("Could not read configs from: ", config_location)

def logs(app):
	log_pathname = app.config['LOG_LOCATION'] + app.config['LOG_FILE']
	file_handler = RotatingFileHandler(log_pathname, maxBytes=1024 * 1024 * 10, backupCount=1024)
	file_handler.setLevel( app.config['LOG_LEVEL'] )
	formatter = logging.Formatter("%(levelname)s | %(asctime)s | %(module)s | %(funcName)s | %(message)s")
	file_handler.setFormatter(formatter)
	app.logger.setLevel( app.config['LOG_LEVEL'] )
	app.logger.addHandler(file_handler)

if __name__ == "__main__":
    init(app)
    logs(app)
    app.run(debug=app.config['DEBUG'])
