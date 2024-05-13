from flask import Flask, render_template, request, session, redirect,flash,jsonify, url_for
from supabase import create_client
import os


app = Flask(__name__)
app.secret_key = os.urandom(32)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Global variable to track user authentication status
authenticated = False

# Function to check if the user is authenticated
def is_authenticated():
    global authenticated
    return authenticated

def set_authenticated(status):
    global authenticated
    authenticated = status

@app.route('/', methods=['GET','POST'])
def index(): 
    session.clear()
    set_authenticated(False)  
    return render_template('index.html')

@app.route('/index', methods=['GET','POST'])
def indexd():  
    return render_template('index.html')


@app.route('/signup', methods=['GET','POST'])
def signup():
    set_authenticated(False)
    if request.method == "POST": 
        username = request.form['username']
        password = request.form['password']
        # Check if username already exists
        existing_user_response = supabase.table('users').select('*').eq('username', username).execute()
        existing_user_data = existing_user_response.data        
        if existing_user_data:
            flash('Username already exists', 'success')
            return redirect('/signup')  
              
        # Create new user
        new_user_response = supabase.table('users').insert({'username': username, 'password': password}).execute()
        new_user_data = new_user_response.data

        if not new_user_data:
            flash('Error creating user', 'success')
            return redirect('/signup')  
        else:     
            set_authenticated(True) 
            return redirect('/welcome')
    return render_template('signup.html') #get req render template
  

@app.route('/login', methods=['GET', 'POST'])
def login(): 
    set_authenticated(False)
    if request.method == "POST": 
        username = request.form['username']
        password = request.form['password']
                
        # Fetch user from database
        response = supabase.table('users').select('*').eq('username', username).execute()
        user = response.data
                
        if user:
            if user[0]['password'] == password:
                session['user_id'] = user[0]['id']
                set_authenticated(True)
                return redirect('/welcome')
            else:
                flash('Incorrect password', 'success') 
                return redirect('/login')
        else:
            flash('Username does not exist', 'success')
            return redirect('/login')    
    return render_template('login.html')


def check_authentication(func):
    def wrapper(*args, **kwargs):
        if is_authenticated():
            return func(*args, **kwargs)
        else:
            current_page = request.path
            return redirect(current_page)
    wrapper.__name__ = func.__name__  # Preserve the original function name
    return wrapper

def get_current_user_id():
    return session.get('user_id')  # Assuming you store the user ID in the session



@app.route('/add_task', methods=['GET','POST'])
@check_authentication
def add_task():
    if request.method == "POST":
        user_id = session.get('user_id')
        if user_id is None:
            return redirect('/login')
        
        task_name = request.form['task_name']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        
        task_data = {
            'user_id': user_id,
            'task_name': task_name,
            'start_time': start_time,
            'end_time': end_time
        }
        supabase.table('tasks').insert(task_data).execute()
        flash('Task added successfully', 'success')
        return redirect('/add_task')
    return render_template('createtask.html')


@app.route('/view_tasks')
@check_authentication
def view_tasks():
    user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
    tasks_response = supabase.table('tasks').select('*').eq('user_id', user_id).execute()
    tasks = tasks_response.data
    print(tasks)
    return render_template('tasks.html', tasks=tasks)

@app.route('/tasks')
@check_authentication
def tasks():
    user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
    tasks_data = get_tasks_for_user(user_id)
    return render_template('tasks.html', tasks=tasks_data)

def get_tasks_for_user(user_id):
    tasks_query = supabase.table('tasks').select('*').eq('user_id', user_id).execute()
    tasks_data = tasks_query.data
    return tasks_data



@app.route('/delete_task', methods=['POST'])
@check_authentication
def delete_task():
    task_id = request.form.get('deleteId')  # Get the task_id from the form
    if task_id:
        response = supabase.table('tasks').delete().eq('id', task_id).execute()
    return redirect('/tasks')


@app.route('/update', methods=['POST'])
@check_authentication
def update_task():
    update_id = request.form['updateId']
    new_name = request.form['name']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    response = supabase.table('tasks').update({'task_name': new_name, 'start_time': start_time, 'end_time': end_time}).eq('id', update_id).execute()
    return redirect('/view_tasks')


@app.route('/complete/<int:id>', methods=['GET','POST'])
@check_authentication
def complete_task(id):
    if request.method == "POST":
        # Update task_status to 1 for the specified ID
        response = supabase.table('tasks').update({'task_status': 1}).eq('id', id).execute()
        return '', 204  # Return 204 status code for successful completion
    return render_template('tasks.html')

@app.route('/redo/<int:id>', methods=['GET','POST'])
@check_authentication
def redo(id):
    if request.method == "POST":
        # Update task_status to 1 for the specified ID
        response = supabase.table('tasks').update({'task_status': 0}).eq('id', id).execute()
        return '', 204  # Return 204 status code for successful completion
    return render_template('tasks.html')


@app.route('/completed-tasks', methods=['GET'])
@check_authentication
def completed_tasks():
    user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
    response = supabase.table('tasks').select('*').eq('user_id', user_id).eq('task_status', 1).execute()
    completed_tasks = response.data
    return render_template('completed_tasks.html', completed_tasks=completed_tasks)

@app.route('/pending-tasks')
@check_authentication
def pending_tasks():
    user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
    response = supabase.table('tasks').select('*').eq('user_id', user_id).eq('task_status', 0).execute()
    pending_tasks = response.data
    return render_template('pending_tasks.html', pending_tasks=pending_tasks)

@app.route('/task_analysis')
@check_authentication
def task_analysis():
    return render_template('task_analysis.html')

@app.route('/total-tasks')
@check_authentication
def total_tasks():
    user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
    response = supabase.table('tasks').select('task_name', 'start_time', 'end_time', 'task_status').eq('user_id', user_id).execute()
    total_tasks = response.data
    return render_template('total_tasks.html', total_tasks=total_tasks)



@app.route('/date_wise_tasks')
def date_wise_tasks():
    user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
    # Fetch tasks data from Supabase
    response = supabase.table('tasks').select('task_name', 'start_time', 'end_time', 'task_status').eq('user_id', user_id).execute()
    tasks_data = response.data
        # Sort tasks based on start_time (assuming start_time is in ISO 8601 format)
    tasks_sorted = sorted(tasks_data, key=lambda x: x.get('start_time', ''))
    
    return render_template('date_wise_tasks.html', tasks=tasks_sorted)

# @app.route('/welcome')
# def welcome():
#     if 'user_id' in session:
#         # User is logged in, render the welcome page
#         return render_template('welcome.html')
#     else:
#         # User is not logged in, redirect to the login page
@app.route('/usersettings')
def user_settings():
    return render_template('usersettings.html')

@app.route('/update_user', methods=['POST'])
def update_user():
    if request.method == "POST":
        user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
        # if user_id:       
        new_username = request.form['username']
        new_password = request.form['password']

        # Get the current user's details
        current_user = supabase.table('users').select('*').eq('id', user_id).execute().data
        current_username = current_user[0]['username']
        current_password = current_user[0]['password']

        # Check if username and password have changed
        username_changed = current_username != new_username
        password_changed = current_password != new_password

        # Check if the new username already exists (except for the current username)
        if username_changed:
            # Query the database for user data with the new username
            user_data = supabase.table('users').select('*').eq('username', new_username).execute().data
            # Exclude the current user's data from the query result
            user_data_filtered = [user for user in user_data if user['username'] != current_username]
            # Check if any data exists with the new username (excluding the current user)
            if user_data_filtered:
                flash('Username already taken!', 'error')
                return redirect(url_for('user_settings'))

        # Update user details in the 'users' table
        update_data = {}
        if username_changed:
            update_data['username'] = new_username
        if password_changed:
            update_data['password'] = new_password

        if username_changed or password_changed:
            supabase.table('users').update(update_data).eq('id', user_id).execute()
            if username_changed and password_changed:
                flash('Username and password changed successfully!', 'info')
            elif username_changed:
                flash('Username changed successfully!', 'info')
            else:
                flash('Password changed successfully!', 'info')
            return redirect(url_for('user_settings'))
        else:
            flash('No changes made!', 'info')
            return redirect(url_for('user_settings'))
    # else:
    #     flash('User ID not found!', 'error')
    #     return redirect(url_for('user_settings'))
    return render_template('usersettings.html')


# @app.route('/update_user', methods=['POST'])
# def update_user():
#     if request.method == "POST":
#         user_id = get_current_user_id()  # Assuming you have a function to get the current user's ID
#         if user_id:       
#             new_username = request.form['username']
#             new_password = request.form['password']

#             # Check if the new username already exists
#             current_username = current_user[0]['username']
#             if current_username!=new_username:
#                 user_exists = supabase.from_('users').select('*').eq('username', new_username).execute().data
#                 if user_exists:
#                     flash('Username already taken!', 'error')
#                     return redirect(url_for('user_settings'))

#             # Get the current user's details
#             current_user = supabase.from_('users').select('*').eq('id', user_id).execute().data
#             current_username = current_user[0]['username']
#             current_password = current_user[0]['password']

#             # Check if username and password have changed
#             username_changed = current_username != new_username
#             password_changed = current_password != new_password

#             # Update user details in the 'users' table
#             update_data = {}
#             if username_changed:
#                 update_data['username'] = new_username
#             if password_changed:
#                 update_data['password'] = new_password

#             if username_changed or password_changed:
#                 supabase.from_('users').update(update_data).eq('id', user_id).execute()
#                 if username_changed and password_changed:
#                     flash('Username and password changed successfully!', 'info')
#                 elif username_changed:
#                     flash('Username changed successfully!', 'info')
#                 else:
#                     flash('Password changed successfully!', 'info')
#                 return redirect(url_for('user_settings'))
#             else:
#                 flash('No changes made!', 'info')
#                 return redirect(url_for('user_settings'))
#         else:
#             flash('User ID not found!', 'error')
#             return redirect(url_for('user_settings'))
#     return render_template('usersettings.html')


# @app.route('/deletettask', methods=['POST'])
# @check_authentication
# def deletettask():
#     task_id = request.form.get('deleteId')  # Get the task_id from the form
#     if task_id:
#         response = supabase.table('tasks').delete().eq('id', task_id).execute()
#     return redirect('/tasks')

@app.route('/usersettings')
@check_authentication
def usersettings():
    user_data = get_current_user_id()  # Assuming you have a function to get the current user's ID
    return render_template('usersettings.html', users=user_data)

@app.route('/delete_user', methods=['POST'])
@check_authentication
def delete_user():
    user_id = get_current_user_id()
    #user_id = request.form.get('deleteId')  # Get the task_id from the form
    #if user_id:
    supabase.table('tasks').delete().eq('user_id', user_id).execute()
    supabase.table('users').delete().eq('id', user_id).execute()
    return render_template("index.html")



@app.route('/aboutus')
def about_us():
    return render_template('aboutus.html')

@app.route('/welcome')
def welcome():
    if is_authenticated():
        return render_template('welcome.html')
    else:
        return redirect('/index')


# @app.route('/welcome')
# @check_authentication
# def welcome():
#     if is_authenticated():
#         user_id = session.get('user_id')
#         # Fetch user details from the database using user_id
#         response = supabase.table('users').select('username').eq('id', user_id).execute()
#         user_data = response.data
#         if user_data:
#             username = user_data[0]['username']
#             return render_template('welcome.html', username=username)
#         else:
#             flash('User not found', 'error')
#             return redirect('/login')
#     else:
#         flash('Please login or sign up to access this page', 'info')
#         return redirect('/index')



@app.route('/logout', methods=['GET','POST'])
def logout():
    set_authenticated(False)
    if request.method == "POST":
        set_authenticated(False)
        session.pop('user_id')
        flash('You have been logged out', 'info')
        return jsonify({'message': 'Logout successful'}), 200
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run(debug=True)
