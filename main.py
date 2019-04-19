from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from time_fix import rotate_hr, convert_hr, rotate_time, rotate_day

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:sGvjgunWZs2FYae@localhost:3306/blogz'
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
            # might need to change day 
            day = rotate_day(utc_date)
            # change time 
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
    username = db.Column(db.String(120))
    password = db.Column(db.String(120))
    posts = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.before_request
def require_login():
    allowed_routes = ['login','list_blogs','index','register']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


def log_status():
    if 'username' in session:   # if username in session --> user is logged in
        return 'logout'         # need option to logout
    else:                       # is logged out, therefore
        return 'login'          # need option to login


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST': # user trying to log in
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first() # retrieve from database
        if user and user.password == password:  # log them in
            session['username'] = username      # remember user
            flash('Logged in', 'success')
            return redirect('/newpost')
        else:   # why did login fail?
            if not user:
                flash('This username does not exist', 'error')
            elif user.password != password:
                flash('Incorrect password', 'error')
    flash('register','log')
    return render_template('login.html', title='Login')


def is_valid(field):
    if len(field) < 3 or len(field) > 20:
        return 'Invalid length for ' # calling function inserts the approp. field
    elif ' ' in field:
        return 'No whitespace allowed in '
    else:
        return ''
        

def do_passwords_match(password, verify_password):

    # if empty or lengths don't match
    if not verify_password or len(password) != len(verify_password):
        return 'Passwords don\'t match'
    
    # if password invalid
    elif is_valid(password):
        # want verify_password to give same error warning as password
        return is_valid(password)

    elif ' ' in verify_password:
        return 'No whitespace in password'

    for i in range(len(password)):
        if password[i] != verify_password[i]:
            return 'Passwords don\'t match'
    return ''


# /signup
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify_password']

        username_error = is_valid(username)
        password_error = is_valid(password)
        if username_error:
            flash(username_error + 'username', 'error')
            username = ''
        if password_error:
            flash(password_error + 'password', 'error')
        elif not password_error: #if password ok, check verify-password
            verify_error = do_passwords_match(password, verify)
            if verify_error:
                flash(verify_error, 'error')
        if username_error or password_error or verify_error:
            flash('login','log')
            return render_template('register.html',
                                    title='Register',
                                    username=username,
                                    password='',
                                    verify='')

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            flash('Username taken','error')
            return render_template('register.html', title='Register')

    flash('login','log')
    return render_template('register.html', title='Register')


@app.route('/logout')
def logout():
    if log_status()=='logout':
        del session['username']
    return redirect('/blog')


def is_not_empty(field):
    if field.strip() == '':
        return 'Left a field blank'
    return ''


@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        post_title = request.form['post_title']
        post_body = request.form['post_body']
        title_err = is_not_empty(post_title)
        body_err = is_not_empty(post_body)
        
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
            owner = User.query.filter_by(username=session['username']).first()
            new = Blog(post_title, post_body, owner)
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
def list_blogs():
    flash(log_status(),'log')

    # click on single entry
    if request.args.get('id'):
        post_id = request.args.get('id')
        post = Blog.query.filter_by(id=post_id).first()
        return render_template('entry.html', title='a blog', post=post)

    # click on username from home page, 
    # display only blogs by one user
    if request.args.get('user'):
        user_id = request.args.get('user')
        user = User.query.filter_by(id=user_id).first()
        posts = Blog.query.filter_by(owner_id=user_id).all()
        posts = sort(posts)
        return render_template('blog.html', title='Blogs by {0}'.format(user.username), posts=posts)

    posts = Blog.query.all()
    posts = sort(posts)
    return render_template('blog.html', title='All Blogs', posts=posts)


@app.route('/')
def index():
    flash(log_status(),'log')
    users = User.query.all()
    return render_template('index.html', title='Home', users=users)



if __name__ == "__main__":
    app.run()