from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from time_fix import rotate_hr, convert_hr, rotate_time, rotate_day

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:Buildit@localhost:3306/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y33kolV00d00'


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    body = db.Column(db.Text)
    date = db.Column(db.DateTime)
    utc_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, title, body, owner, utc_date=None, date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if utc_date is None:
            utc_date = datetime.utcnow()
        self.utc_date = utc_date
        if date is None:
            # change day maybe
            day = rotate_day(utc_date)
            # change time definitely
            hr = utc_date.hour
            hr = rotate_hr(hr)
            hr = convert_hr(hr)
        self.date = datetime(utc_date.year, utc_date.month, day, hr, utc_date.minute, utc_date.second)

    def __repr__(self):
        return '<Post %r>' % self.title

    def get_date(self):
        return '{0}.{1}.{2}'.format(
                            str(self.date.month), 
                            str(self.date.day), 
                            str(self.date.year))
    
    def get_time(self):
        return rotate_time(self.utc_date)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    posts = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password


"""
# doesn't work
@app.before_request
def require_login():
    #allowed_routes = ['login','register','blog']
    not_allowed_routes = ['newpost']
    if request.endpoint in not_allowed_routes and 'email' not in session:
        return redirect('/login')

@app.before_request
def require_logout():
    allowed_routes = ['blog','entry','newpost','logout'] #?? / ??
    not_allowed_routes = ['login','register']
    if request.endpoint in not_allowed_routes and 'email' in session:
        return redirect('/')
"""


def log_status():
    if 'email' in session: # is logged in, need option to logout
        return 'logout'
        #flash('logout','log')
    else:   # is logged out, need option to login
        return 'login'
        #flash('login','log')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST': # sb trying to log in
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first() # retrieve from database
        if user and user.password == password: # log them in
            session['email'] = email
            flash('Logged in', 'success')
            return redirect('/blog')
        else: # why did login fail?
            # enter categories through flash fn!! for user's next request
            flash('User password incorrect, or user does not exist (cue existential crisis)', 'error')
    flash('register','log')
    return render_template('login.html', title='Login')


def is_password_valid(password):
    if len(password) < 3 or len(password) > 20:
        return 'Invalid length'
    elif ' ' in password:
        return 'No whitespace in password'
    else:
        return ''
        

def do_passwords_match(password, verify_password):

    # if empty or lengths don't match
    if not verify_password or len(password) != len(verify_password):
        return 'Passwords don\'t match'
    
    # if password invalid
    elif is_password_valid(password):
        # want verify_password to give same error warning as password
        return is_password_valid(password)

    elif ' ' in verify_password:
        return 'No whitespace in password'

    for i in range(len(password)):
        if password[i] != verify_password[i]:
            return 'Passwords don\'t match'
    return ''


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify_password']

        # TODO validate data
        password_error = is_password_valid(password)
        if password_error:
            flash(password_error, 'error')
        else: #if password ok, check verify-password
            verify_error = do_passwords_match(password, verify)
            if verify_error:
                flash(verify_error, 'error')
        if password_error or verify_error:
            return render_template('register.html',
                                    title='Register',
                                    email=email,
                                    password='',
                                    verify='')

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/blog')
        else:
            flash('Duplicate user','error')
            return render_template('register.html', title='Register')

    flash('login','log')
    return render_template('register.html', title='Register')


@app.route('/logout')
def logout():
    if log_status()=='logout':
        del session['email']
    return redirect('/blog')


def is_valid(field):
    if field.strip() == '':
        return 'Left a field blank'
    return ''


@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    if request.method == 'POST':
        post_title = request.form['post_title']
        post_body = request.form['post_body']
        title_err = is_valid(post_title)
        body_err = is_valid(post_body)
        
        # if at least one field is empty
        if body_err:
            flash('Body is blank', 'error')
        if title_err:
            flash('Title is blank', 'error')
        if title_err or body_err:
            posts = Blog.query.all()
            flash(log_status(),'log')
            return render_template('newpost.html', title='Add a Blog Post',
                                    post_title = post_title,
                                    post_body = post_body,
                                    posts = posts)
                                    
        # success - neither field is empty
        elif not title_err and not body_err:
            if log_status() == 'login': # an email IS NOT in the session
                owner_name = User.query.filter_by(id=1).first()
            else:
                owner_name = User.query.filter_by(email=session['email']).first()
            new = Blog(post_title, post_body, owner_name)
            db.session.add(new)
            db.session.commit()
            flash('Added post!', 'success')

            posts = Blog.query.all()
            post_id = Blog.query.filter_by(title=post_title).first().id
            return redirect('/blog?id={0}'.format(post_id))
    
    flash(log_status(),'log')
    return render_template('newpost.html', title='Add a Blog Post')


def sort(posts):

    # will hold attr 'date' of post obj, of datetime objs
    # in correct order by date
    order_posts = [] 
    for post in posts:
        # sort by post.date
        order_posts += [post.date]
    order_posts = sorted(order_posts, reverse=True)
    #order_posts.sort() 

    # will return original list of posts in correct order by date
    list_posts = []
    for date in order_posts:
        new = Blog.query.filter_by(date=date).first()
        list_posts += [new]
    return list_posts


@app.route('/blog', methods=['POST', 'GET'])
def index():
    flash(log_status(),'log')
        
    if request.args.get('id'):
        post_id = request.args.get('id')
        post = Blog.query.filter_by(id=post_id).first()
        post_title = post.title
        return render_template('entry.html', title=post_title, post=post)

    if request.method == 'POST':
        post_title = request.form['post_title']
        post_body = request.form['post_body']
        owner_name = User.query.filter_by(email=session['email']).first()
        a_new_post = Blog(post_title, post_body, owner_name)
        db.session.add(a_new_post)
        db.session.commit()

    posts = Blog.query.all()
    posts = sort(posts)
    return render_template('blog.html', title='Home', posts=posts)


@app.route('/', methods=['GET', 'POST'])
def watch_it():
    return redirect('/blog')


if __name__ == "__main__":
    app.run()