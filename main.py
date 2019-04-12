from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    pub_date = db.Column(db.DateTime)
    
    def __init__(self, title, body, pub_date=None):
        self.title = title
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date

    def __repr__(self):
        return '<Post %r>' % self.title

    def get_date(self):
        return '{0}.{1}.{2}'.format(
                            str(self.pub_date.month), 
                            str(self.pub_date.day), 
                            str(self.pub_date.year))
    
    def get_time(self):
        return '{0}:{1}'.format(self.pub_date.hour, self.pub_date.minute)

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
            return render_template('newpost.html', title='Add Blog Post',
                                    post_title = post_title,
                                    post_body = post_body,
                                    posts = posts)
                                    
        # success - neither field is empty
        elif not title_err and not body_err:
            flash('Added post!', 'success')
            new = Blog(post_title, post_body)
            db.session.add(new)
            db.session.commit()
            posts = Blog.query.all()
            post_id = Blog.query.filter_by(title=post_title).first().id
            return redirect('/blog?id={0}'.format(post_id))

    return render_template('newpost.html', title='Add a Blog Post')


@app.route('/blog', methods=['POST', 'GET'])
def index():
    if request.args.get('id'):
        post_id = request.args.get('id')
        post = Blog.query.filter_by(id=post_id).first()
        post_title = post.title
        return render_template('entry.html', title=post_title, post=post)

    if request.method == 'POST':
        post_title = request.form['post_title']
        post_body = request.form['post_body']
        a_new_post = Blog(post_title, post_body)
        db.session.add(a_new_post)
        db.session.commit()

    posts = Blog.query.all()
    return render_template('blog.html', title='Home', posts=posts)


@app.route('/', methods=['GET', 'POST'])
def watch_it():
    return redirect('/blog')


if __name__ == "__main__":
    app.run()