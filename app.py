from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = '7Tb4sLp8gX3qA2y9Zw6uH1vM0eJ2bG7dN8K9c2Y5pO4zG1t3L6'  # Add a secret key for session management
db = SQLAlchemy(app)

class User(db.Model):
    userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    commit_number = db.Column(db.Integer)
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.commit_number = 0
        
class Commit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    commit_title = db.Column(db.String(100), nullable=False)
    commit_description = db.Column(db.Text(1000), nullable=True)
    
    def __init__(self, userid, commit_title, commit_description):
        self.userid = userid
        self.commit_title = commit_title
        self.commit_description = commit_description
        
        
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.userid # Store the user ID in the session
            session['user_name'] = user.username # Store the user ID in the session
            return redirect('/home')
        else:
            return render_template('login.html', message="Ur credentials don't match. Maybe u wanna register?")
            # return redirect('/')
    return render_template('login.html', message=None)

@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('user_id', None)
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirmpassword = request.form.get('confirmpassword')

        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', message='Username already taken')
        if password == confirmpassword:
        # Create a new user
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()

        # Log in the new user automatically after registration
            session['user_id'] = new_user.userid

        return redirect('/')

    return render_template('register.html')


@app.route('/home', methods=['GET', 'POST'])
def index():
    print(session)
    if 'user_id' not in session:
        return redirect('/')

    userid = session['user_id']
    user = User.query.get(userid)

    if request.method == 'POST':
        commit_title = request.form.get('commit_title')
        commit_description = request.form.get('commit_description')

        # Create a new Commit associated with the logged-in user
        commit = Commit(userid=userid, commit_title=commit_title, commit_description=commit_description)
        db.session.add(commit)
        db.session.commit()

        # Increment the commit number for the user
        user = User.query.filter_by(userid=userid).first()

        if user:
            user.commit_number += 1
            db.session.commit()
        else:
            # Handle the case where the user is not found
            print("User not found")

        return redirect('/home')

    posts = Commit.query.order_by(desc(Commit.id)).all()
    
    commit_history = (
        db.session.query(User.username, Commit.commit_title, Commit.commit_description)
        .join(Commit, User.userid == Commit.userid)
        .order_by(desc(Commit.id))
        .all()
    )
    
    return render_template('index.html', commit_history = commit_history)

@app.route('/chart')
def chart():
    users = User.query.all()

    user_names = [user.username for user in users]
    commit_numbers = [user.commit_number for user in users]

    plt.bar(user_names, commit_numbers)
    plt.xlabel('Users')
    plt.ylabel('Commit Numbers')
    plt.title('Comparison of Commit Numbers')

    # Save the plot to a BytesIO object
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    
    # Encode the plot image as base64 to embed in the HTML
    img_str = base64.b64encode(img.read()).decode('utf-8')
    img_url = f'data:image/png;base64,{img_str}'

    plt.close()
    return render_template('chart.html', img_url = img_url)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)