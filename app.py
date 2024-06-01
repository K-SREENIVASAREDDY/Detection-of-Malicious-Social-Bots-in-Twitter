from flask import Flask, render_template, request, url_for, Markup, jsonify
import pickle
import pandas as pd
import numpy as np
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
from flask import Flask, render_template, request, url_for, session, redirect, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import pickle
import pandas as pd
import pymsgbox
app = Flask(__name__)
pickle_in = open('model.pkl','rb')
pac = pickle.load(pickle_in)
tfid = open('tfidf_vectorizer.pkl','rb')
tfidf_vectorizer = pickle.load(tfid)

 
 
app.secret_key = 'neha'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'malware'
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

 
@app.route('/login', methods = ['GET',"POST"])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        # cursor = mysql.connection.cursor(MySQLdb.cursors)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM employee WHERE username = %s AND password = %s AND status="Approved" ', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            global Id
            session['Id'] = account['Id']
              
            Id = session['Id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('profile'))
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password! or Account Blocked')
            return redirect(url_for('login'))
    # Show the login form with message (if any)

    return render_template('login.html', msg=msg)

@app.route('/register',methods= ['GET',"POST"])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,10}$"
        pattern = re.compile(reg)
        # try:
        #     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #     # Use the cursor for executing SQL queries
        # except Exception as e:
        #     print("Error:", e)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Check if account exists using MySQL)
        cursor.execute('SELECT * FROM employee WHERE Username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not re.search(pattern,password):
            msg = 'Password should contain atleast one number, one lower case character, one uppercase character,one special symbol and must be between 6 to 10 characters long'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into employee table
            cursor.execute('INSERT INTO employee VALUES (NULL, %s, %s, %s, "Approved")', (username, email, password))
            mysql.connection.commit()
            flash('You have successfully registered! Please proceed for login!')
            return redirect(url_for('login'))
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        return msg
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

 
 
 


@app.route('/loginadmin')
def loginadmin():
	return render_template('loginadmin.html')


@app.route('/upload')
def upload():
	return render_template('upload.html')
@app.route('/preview',methods=["POST"])
def preview():
    if request.method == 'POST':
        dataset = request.files['datasetfile']
        df = pd.read_csv(dataset,encoding = 'unicode_escape')
        df.set_index('Id', inplace=True)
        return render_template("preview.html",df_view = df)

@app.route('/prediction')
def prediction():
 	return render_template("prediction.html")


@app.route('/chart')
def chart():
    #if request.method == 'POST':    
         
       #query_content=request.form['news']
       #news=['query_content']
       #msg = '' 
       abc = request.args.get('news')
       
       #input_data=re.search("(?P<url>https?://[^\s]+)",abc).group("url")
       #string = [input_data.rstrip()]
       pattern =  r'(?:http://)?\w+\.\S*[^.\s]'
       input_data=re.findall(pattern, abc)
	    
       if input_data:
           
 
         tfidf_test = tfidf_vectorizer.transform(input_data)
	# predicting the input
        
         y_pred = pac.predict(tfidf_test)
	#if y_pred[0] == 'bad':
	 #  label="malware"
	#elif y_pred[0] == 'good':
	 #  label="no malware"
         pred=format(y_pred[0])
   
         login()
         cur = mysql.connection.cursor()
         cur.execute("INSERT INTO review(news_content,pred,userid,url) VALUES ( %s, %s,%s,%s) ", (input_data,pred,Id,abc))
         
         mysql.connection.commit()
         cur.close()
         
        
         
        
         
         
       else:
         #msg = 'Enter the url'
         #return msg
         #return render_template('prediction.html', msg=msg)
         pymsgbox.alert('Enter the url', 'warning')
         return render_template('prediction.html')
       return redirect('/users')
         
@app.route('/users')
def users():
     
    cur = mysql.connection.cursor()
    resultValue = cur.execute(" SELECT * from employee INNER JOIN review ON employee.ID = review.USERID WHERE status !='Blocked';")
     
    if resultValue > 0:
        userDetails = cur.fetchall()
         
        return render_template('users.html',userDetails=userDetails)
         
@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    resultValue = cur.execute(" SELECT * from employee INNER JOIN review ON employee.ID = review.USERID;")
     
    if resultValue > 0:
        userDetails = cur.fetchall()
         
        return render_template('admin.html',userDetails=userDetails) 
@app.route('/profile')    
def profile():
    
     
         
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * from employee WHERE Id = %s', (Id,))
        account = cursor.fetchone()
       
        return render_template('profile.html', account=account)         
        
@app.route('/userdetail')
def userdetail():  
   cur = mysql.connection.cursor()      
   cur.execute("SELECT * from employee")
   useradmin=cur.fetchall()
   print(useradmin)
       
   return render_template('userdetail.html',useradmin=useradmin)
     
         
@app.route('/blockUser',methods=['GET','POST'])
def blockUser():
    if request.method == 'POST' and 'fid' in request.form:
       f1 = request.form['fid']
        
       con=mysql.connection.cursor()
       con.execute("UPDATE employee SET status='Blocked' WHERE Id=%s " , (f1,))
       mysql.connection.commit()
            
       con.close()
     
        
       return redirect(url_for('admin'))

@app.route('/user')
def user():
    legend = "review by pred"
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT pred from review GROUP BY pred")
        # data = cursor.fetchone()
        rows1 = cursor.fetchall()
        labels = list()
        i = 0
        for row1 in rows1:
            labels.append(row1[i])
         

         
        cursor.execute("SELECT pred from review GROUP BY pred")
        # data = cursor.fetchone()
        rows2 = cursor.fetchall()
        
        label = list()
        j = 0
        values = list()
        k = 0
        for row2 in rows2:
            label.append(row2[j])
            cursor.execute("SELECT COUNT(id) from review WHERE pred=%s", (row2[j],))
            rows3 = cursor.fetchall()
             
            #j=j+1
        # Convert query to objects of key-value pairs
            
            for row3 in rows3:
	              values.append(row3[k])
            #k=k+1
        mysql.connection.commit()
        cursor.close()
        
        
        
    except:
        print('Error: unable to fetch items')    

    return render_template('user.html', values=values, labels = labels, legend=legend)


if __name__=='__main__':
    app.run(debug=False)
