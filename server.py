from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'dhafksld'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods = ['POST'])
def register():
    errors = []
    mysql = connectToMySQL('wall')
    user_query = 'SELECT username FROM users WHERE username = %(username)s;'
    user_data = {
        'username': request.form['username']
    }
    users = mysql.query_db(user_query,user_data)

    if len(users) > 0:
        errors.append("Username already in use")
    if len(request.form['password']) < 8:
        errors.append("Password must contain at least 8 characters")
    if len(errors) > 0:
        for error in errors:
            flash(error)
        return redirect('/')
    else:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])

        mysql = connectToMySQL('wall')
        register_query = 'INSERT INTO users (username,password,created_at,updated_at) Values(%(username)s,%(hashed_pw)s,NOW(),NOW());'
        register_data = {
            'username': request.form['username'],
            'hashed_pw': pw_hash
        }
        user_id = mysql.query_db(register_query,register_data)
        session['user_id'] = user_id
    
    return redirect('/success')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/login', methods = ['POST'])
def login():
    mysql = connectToMySQL('wall')
    login_query = 'SELECT * FROM users WHERE username = %(username)s;'
    login_data = {
        'username': request.form['username']
    }
    match = mysql.query_db(login_query,login_data)

    if len(match) == 0:
        flash("Username or password incorrect")
        return redirect('/')
    user = match[0]
    if bcrypt.check_password_hash(user['password'],request.form['password']):
        session['user_id'] = user['id']
        return redirect('/home')
    else:
        flash("Username or password incorrect")
        return redirect('/')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/')
    mysql = connectToMySQL('wall')
    username_query = 'SELECT * FROM users WHERE id = %(user_id)s;'
    username_data = {
        'user_id': session['user_id']
    }
    user = mysql.query_db(username_query,username_data)[0]

    mysql = connectToMySQL('wall')
    all_user_data = mysql.query_db('SELECT * FROM users')

    get_messages_query = '''SELECT message,users.username,sender.username AS sender_username,messages.created_at, messages.id 
                            FROM messages
                            JOIN users ON messages.receiver_id = users.id
                            JOIN users AS sender ON messages.sender_id = sender.id 
                            WHERE receiver_id = %(user_id)s;'''
    get_messages_data = {
        'user_id': session['user_id']
    }
    mysql = connectToMySQL('wall')
    messages = mysql.query_db(get_messages_query,get_messages_data)

    mysql = connectToMySQL('wall')
    message_num_query = 'SELECT COUNT(messages.id) AS NumOfMessages FROM messages WHERE receiver_id = %(user_id)s;'
    message_num_data = {
        'user_id': session['user_id']
    }
    num_of_messages = mysql.query_db(message_num_query,message_num_data)

    
    current_user = session['user_id']

    return render_template('home.html',username = user['username'],all_users = all_user_data,user_messages = messages,logged_user = current_user, message_num = num_of_messages)

@app.route('/create_message', methods = ['POST'])
def create_message():
    mysql = connectToMySQL('wall')
    message_query = 'INSERT INTO messages (message,created_at,updated_at,receiver_id,sender_id) VALUES (%(message)s,NOW(),NOW(),%(receiving_id)s,%(sender_id)s);'
    message_data = {
        'message': request.form['message'],
        'receiving_id': request.form['receiving_id'],
        'sender_id': session['user_id']
    }
    mysql.query_db(message_query,message_data)
    print(message_data)
    return redirect('/home')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/delete', methods = ['POST'])
def delete():
    mysql = connectToMySQL('wall')
    delete_query = 'DELETE FROM messages WHERE messages.id = %(message_id)s;'
    delete_data = {
        'message_id': request.form['message_id']
    }
    deleted_message = mysql.query_db(delete_query,delete_data)
    print(deleted_message)

    return redirect('/home')



    

if __name__ == '__main__':
    app.run(debug=True)