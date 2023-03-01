######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		fname=request.form.get('fname')
		lname=request.form.get('lname')
		dob=request.form.get('dob')
		gender=request.form.get('gender')
		hometown=request.form.get('hometown')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, fname, lname, dob, gender, hometown) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}','{5}','{6}')".format(email, password, fname, lname, dob, gender, hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )''', (photo_data, uid, caption))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

# Begin photo viewing process
@app.route('/photos_list', methods=['GET','POST'])
def view_photos():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('view_photos.html', photos=getUsersPhotos(uid), base64=base64)
	

# End photo viewing process 



#Friends part
@app.route('/addfr', methods=['GET', 'POST'])
@flask_login.login_required
def add():
	usid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'GET':
		return render_template('addf.html', friends = getUsersFriends(usid))
	email = flask.request.form['email']
	cursor = conn.cursor()

	#check if email is registered
	if isEmailUnique(email):
		return render_template('addf.html', notfound = 'True', friends = getUsersFriends(usid))
	fid = getUserIdFromEmail(email)
	if isFriend(usid, fid):
		return render_template('addf.html', already = 'True', friends = getUsersFriends(usid))
	if usid == fid:
		return render_template('addf.html', err = 'True')
	if cursor.execute('''INSERT INTO Friends (usid, fid) VALUES (%s, %s)''',(usid,fid)):
		conn.commit()
		return render_template('addf.html', added = 'True', friends = getUsersFriends(usid))

	return render_template('addf.html', err = 'True', friends = getUsersFriends(usid))
		

	#information did not match
	return "<a href='/addfr'>Try again</a>\
			</br><a href='/'>or back home</a>"

def isFriend(userid,friend_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT fid FROM Friends WHERE usid = '{0}' AND fid = '{1}' ".format(userid,friend_id)):
		#this means there are greater than zero entries with that email
		return True
	else:
		return False

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT fid FROM Friends WHERE usid = '{0}'".format(uid))
	ids = cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]
	return [getUserEmail(x[0]) for x in ids]
	
def getUserEmail(id):
	cursor = conn.cursor()
	cursor.execute("SELECT email  FROM Users WHERE user_id = '{0}'".format(id))
	return cursor.fetchone()[0]


@app.route('/inspect', methods=['GET', 'POST'])
def vimage():
		photo_id = flask.request.form['pho']
		owenerId = getPhotoOwner(photo_id)
		action = flask.request.form['action']
		uid = getUserIdFromEmail(flask_login.current_user.id)
		isOwener = False
		isLiked = LikedBy(photo_id, uid)
		if owenerId == uid:
			isOwener = True
		if action == 'no':
			return render_template("inspect.html", owner = isOwener, picdata = getPhotoData(photo_id),liked = isLiked,\
				caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(photo_id), comments = getPhotoComments(photo_id),imid = photo_id)
		if action == 'like':
			if cursor.execute('''INSERT INTO Likes (user_id, picture_id) VALUES (%s, %s)''',(uid,photo_id)):
				conn.commit()
				return render_template("inspect.html", owner = isOwener, picdata = getPhotoData(photo_id),liked = True,\
					caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(photo_id), comments = getPhotoComments(photo_id),imid = photo_id)
		if action == 'comment':
			txt = flask.request.form['text']
			if cursor.execute('''INSERT INTO Comments (user_id, picture_id,ctext) VALUES (%s, %s,%s)''',(uid,photo_id,txt)):
				conn.commit()
				return render_template("inspect.html", owner = isOwener, picdata = getPhotoData(photo_id),liked = isLiked,\
					caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(iphoto_idd), comments = getPhotoComments(photo_id),imid = photo_id)
		
		return render_template("inspect.html", owner = isOwener, picdata = getPhotoData(photo_id),liked = isLiked,\
				caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(photo_id), comments = getPhotoComments(photo_id), imid = photo_id)

def getPhotoOwner(id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Pictures WHERE picture_id = '{0}'".format(id))
	return cursor.fetchone()[0]

def getPhotoData(id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata FROM Pictures WHERE picture_id = '{0}'".format(id))
	return cursor.fetchone()[0]

def getPhotoCap(id):
	cursor = conn.cursor()
	cursor.execute("SELECT caption FROM Pictures WHERE picture_id = '{0}'".format(id))
	return cursor.fetchone()[0]
def getPhotoComments(id):
	cursor = conn.cursor()
	if cursor.execute("SELECT  ctext, user_id FROM Comments WHERE picture_id = '{0}'".format(id)):
		ucoms = []
		for uc in cursor.fetchall():
			ucoms  = ucoms + [(getUserEmail(uc[1]),uc[0])]
		return ucoms
	else:
		return []
def getPhotoLikes(id):
	cursor = conn.cursor()
	if cursor.execute("SELECT email FROM Likes, Users WHERE picture_id = '{0}' And likes.user_id = Users.user_id".format(id)):
		eml = []
		for em in cursor.fetchall():
			eml  = eml + [em[0]]
		return eml
	else:
		return []

def LikedBy(pid,uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}' ".format(uid,pid)):
		#this means there are greater than zero entries with that email
		return True
	else:
		return False


#default page
@app.route("/", methods=['GET'])
def hello():
	if not current_user.is_authenticated():
		return render_template('hello.html', message='Welecome to Photoshare')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', message='Welecome to Photoshare', photos=getUsersPhotos(uid), base64=base64)





if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
