import logging
from applicationinsights.flask.ext import AppInsights
from flasgger import Swagger
from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
swagger = Swagger()
appinsights = AppInsights()
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    app.config['APPINSIGHTS_INSTRUMENTATIONKEY'] = os.environ['APPINSIGHTS_INSTRUMENTATIONKEY']
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    appinsights.init_app(app)
    swagger.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    
    return app

import os
from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    send_from_directory,
    url_for,
    session
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app,db,login_manager,bcrypt,swagger,appinsights,logger
from models import User
from forms import login_form,register_form
import requests

#картинки про котів
api_key = 'live_nh2nBNg7o0ezAaPFStcGG8LWXhJSSnDdezIO6YnqDlu4DxKSDjwyXY0hgnOLOe4k'
def get_random_cat():
    response = requests.get(f'https://api.thecatapi.com/v1/images/search?api_key={api_key}')
    cat_data = response.json()
    return cat_data[0]['url']

#факти про котів
def get_random_cat_fact():
    response = requests.get(f'https://catfact.ninja/fact')
    cat_data = response.json()
    return cat_data['fact']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=120)

@app.route("/", methods=("GET", "POST"), strict_slashes=False)
@app.route("/home", methods=("GET", "POST"), strict_slashes=False)
def home():
    return render_template("home.html",title="Home")

@app.route("/cats", methods=("GET", "POST"), strict_slashes=False)
def cats():
    random_cat_url = get_random_cat()
    random_cat_fact = get_random_cat_fact()
    return render_template("cats.html",title="Cats", random_cat_url=random_cat_url, random_cat_fact=random_cat_fact)

@app.route("/api_cats_fact")
def api_cats_fact():
    """
    A sample endpoint that returns a fact about cat.
    ---
    responses:
      200:
        description: A string indicating a fact about cat.
    """
    random_cat_fact = get_random_cat_fact()
    return random_cat_fact
    
@app.route("/api_cats_picture")
def api_cats_picture():
    """
    A sample endpoint that returns a url of cat.
    ---
    responses:
      200:
        description: A string indicating a url of cat.
    """
    random_cat_url = get_random_cat()
    return random_cat_url

@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    logger.debug('Request for login page received')
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )



# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    logger.debug('Request for register page received')
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            
            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )
    
            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/hello') #/apidocs
def hello():
    """
    A sample endpoint that returns a greeting.
    ---
    responses:
      200:
        description: A string indicating a greeting.
    """
    app.logger.info('Hello, World!')
    logger.debug('Entering hello string')
    return 'Hello, world!'


@app.route("/about/", methods=("GET", "POST"), strict_slashes=False)
def about():
    logger.debug('Request for about page received')
    return render_template('about.html')

@app.route("/profile/", methods=("GET", "POST"), strict_slashes=False)
def profile():
    logger.debug('Request for about profile received')
    return render_template('profile.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/health')
def health():
    """
    A sample endpoint that returns info about health.
    ---
    responses:
      200:
        description: A string indicating that health is ok.
    """
    return "OK"


if __name__ == "__main__":
    app.run(host='0.0.0.0')
