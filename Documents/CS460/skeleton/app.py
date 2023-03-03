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
app.config['MYSQL_DATABASE_PASSWORD'] = 'Mhd050135'
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
		album = request.form.get('album')
		if not exist_album(uid, album):
			create_album(uid,album)
		tag = request.form.get('tag')
		tags = tag.split()
		print(tags)
		cursor = conn.cursor()
		photo_data =imgfile.read()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, getAlbumId(album,uid)))
		picture_id = conn.insert_id()
		if tag:
			for i in range(len(tags)):
				cursor.execute(''' INSERT IGNORE INTO Tags (word) VALUES (%s)''', (tags[i],))
				cursor.execute(''' INSERT INTO Tagged (word, picture_id) VALUES (%s, %s)''', (tags[i], picture_id ))
			conn.commit()
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
	
def create_album(uid, alb):
	cursor.execute('''INSERT INTO Albums (user_id, album_name) VALUES (%s, %s)''',(uid,alb))
	conn.commit()
	return 

def getAlbumId(an, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id  FROM Albums WHERE user_id = '{0}' AND album_name = '{1}' ".format(uid,an))
	return cursor.fetchone()[0]

#end photo uploading code

# Begin photo viewing process
@app.route('/photos_list', methods=['GET','POST'])
def view_photos():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		photo_id = request.form.get('picture_id')
		print('test')
		deletePicture(photo_id)
		return render_template('view_photos.html', photos=getUsersPhotos(uid), base64=base64)
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
	if flask_login.current_user.is_authenticated:
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
					caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(photo_id), comments = getPhotoComments(photo_id),imid = photo_id)
		
		return render_template("inspect.html", owner = isOwener, picdata = getPhotoData(photo_id),liked = isLiked,\
				caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(photo_id), comments = getPhotoComments(photo_id), imid = photo_id)
	else:
		photo_id = flask.request.form['pho']
		action = flask.request.form['action']
		uid = None
		isOwener = False
		if action == 'no':
			return render_template("inspectunr.html",  picdata = getPhotoData(photo_id),\
				caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(photo_id), comments = getPhotoComments(photo_id),imid = photo_id)
		if action == 'comment':
			txt = flask.request.form['text']
			if cursor.execute('''INSERT INTO Comments (user_id, picture_id,ctext) VALUES (null, %s,%s)''',(photo_id,txt)):
				conn.commit()
				return render_template("inspectunr.html", picdata = getPhotoData(photo_id),\
					caption = getPhotoCap(photo_id), base64=base64, likes = getPhotoLikes(photo_id), comments = getPhotoComments(photo_id),imid = photo_id)
		
		return render_template("inspectunr.html", picdata = getPhotoData(photo_id),liked = isLiked,\
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
			if uc[1] == None:
				ucoms  = ucoms + [("unregisterd",uc[0])]
			else:
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

@app.route('/addalb', methods=['GET', 'POST'])
@flask_login.login_required
def malbum():
	usid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'GET':
		return render_template('album.html', albums = getUsersAlbums(usid))
	album = flask.request.form['alb']
	cursor = conn.cursor()
	#check if email is registered
	if exist_album(usid, album):
		return render_template('album.html', already = 'True', albums = getUsersAlbums(usid))
	if cursor.execute('''INSERT INTO Albums (user_id, album_name) VALUES (%s, %s)''',(usid,album)):
		conn.commit()
		return render_template('album.html', added = 'True', albums = getUsersAlbums(usid))

	return render_template('album.html', err = 'True', albums = getUsersAlbums(usid))
		

	#information did not match
	return "<a href='/addfr'>Try again</a>\
			</br><a href='/'>or back home</a>"

def exist_album(userid,album_name):
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id FROM Albums WHERE user_id = '{0}' AND album_name = '{1}' ".format(userid,album_name)):
		#this means there are greater than zero entries with that email
		return True
	else:
		return False

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_name, album_id FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

@app.route("/viewalbum", methods=['GET', 'POST'])
def view_album():
	if request.method == 'POST':
		alb = flask.request.form['alb']
		photo_data = getAlbumPhotos(alb)
		return render_template('viewalbum.html' , photos = photo_data, base64 = base64)
	return render_template('viewalbum.html')

def getAlbumPhotos(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption  FROM  Pictures  WHERE  album_id = '{0}' ".format(aid))
	return cursor.fetchall()

@app.route('/viewfriendalbum', methods=['POST'])
@flask_login.login_required
def falbum():
	friend_email = flask.request.form['friend']
	cursor = conn.cursor()
	#check if email is registered
	return render_template('falbum.html' , albums = getUsersAlbums(getUserIdFromEmail(friend_email)))

@app.route("/search_album", methods=['GET', 'POST'])
def search_alb():
	if request.method == 'POST':
		aname = flask.request.form['album']
		uemail = flask.request.form['uname']
		if isEmailUnique(uemail):
			return render_template('search_album.html' ,notfound = 'True')
		if not exist_album(getUserIdFromEmail(uemail), aname):
			return render_template('search_album.html' ,noalbum = 'True')
		aid = getAlbumId(aname, getUserIdFromEmail(uemail))
		photo_data = getAlbumPhotos(aid)
		return render_template('search_album.html' , photos = photo_data, base64 = base64)
	if request.method == 'GET':
		return render_template('search_album.html')
		

@app.route("/search_tags", methods=['GET', 'POST'])
def search_tags():
	if request.method == 'POST':
		tname = flask.request.form['tag']
		photo_data = getTagPhotos(tname)
		return render_template('search_tags.html' , photos = photo_data, base64 = base64)
	return render_template('search_tags.html')

def getTagPhotos(tname):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption  FROM Tagged AS T, Pictures AS P WHERE T.picture_id = P.picture_id AND T.word = '{0}' ".format(tname))
	return cursor.fetchall()

def getMyTagPhotos(uid, tname):
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.picture_id, P.caption  FROM Tagged AS T, Pictures AS P WHERE T.picture_id = P.picture_id AND T.word = '{0}' AND P.user_id = '{1}' ".format(tname,uid))
	return cursor.fetchall()

@app.route("/search_your_tags", methods=['GET', 'POST'])
@flask_login.login_required
def search_your_tags():
	if request.method == 'POST':
		tname = flask.request.form['tag']
		photo_data = getMyTagPhotos(getUserIdFromEmail(flask_login.current_user.id), tname) 
		return render_template('search_your_tags.html' , photos = photo_data, base64 = base64)
	return render_template('search_your_tags.html')

#default page
@app.route("/", methods=['GET'])
def hello():
	if not flask_login.current_user.is_authenticated:
		return render_template('hello.html', message='Welcome to Photoshare')
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', message='Welecome to Photoshare', photos=getUsersPhotos(uid), base64=base64)


@app.route("/delete", methods=['GET', 'POST'])
def delete_photo():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photo_id = flask.request.form['pho']
	deletePicture(photo_id)
	return render_template('hello.html', message='Welecome to Photoshare', photos=getUsersPhotos(uid), base64=base64)



def deletePicture(photo_id):
	cursor = conn.cursor()
	
	cursor.execute("SELECT word FROM Tagged WHERE picture_id = '{0}'".format(photo_id))
	tags = cursor.fetchall()

	cursor.execute("DELETE FROM Tagged WHERE picture_id = '{0}'".format(photo_id))
	conn.commit()
		
	for i in range(len(tags)):
		cursor.execute("DELETE FROM Tags WHERE word = '{0}'".format(tags[i][0]))
		conn.commit()
	
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(photo_id))
	conn.commit()
	return


def deleteAlbum(aid):
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(aid))
	conn.commit()
	return

@app.route("/delete_album", methods=['GET', 'POST'])
def delete_alb():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	aid = flask.request.form['delete']
	deleteAlbum(aid)
	return render_template('album.html', albums= getUsersAlbums(uid))


@app.route('/top_three_tags', methods=['GET', 'POST'])
def top_tags():
	cursor = conn.cursor()
	cursor.execute("SELECT word, COUNT(word) FROM Tags GROUP BY word ORDER BY COUNT(word) DESC LIMIT 10")
	tags = cursor.fetchall()
	return render_template('topthreetags.html' , tags = tags)

@app.route('/top_comment_matches', methods=['GET', 'POST'])
def search_match():
	if request.method == "POST":
		txt = flask.request.form['comment']
		print("txt = ", txt)
		return render_template("top_com_matches.html",users = top_user_matches(txt) )
	return render_template("top_com_matches.html")


def top_user_matches(txt):
	cursor = conn.cursor()
	ulist = []
	if cursor.execute("SELECT user_id, COUNT(user_id) FROM Comments Where ctext = '{0}' GROUP BY user_id ORDER BY COUNT(user_id) DESC".format(txt)):
		print("im here")
		for uid in cursor.fetchall():
			ulist.append(getUserEmail(uid[0]))
			print(ulist)
	return ulist

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)


