from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Makale Form
class AddArticlesForm(Form):
    title = StringField("Makale Başlığı")
    content = TextAreaField("Makale İçeriği")

#Giriş Kontrol
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfaya Erişmek İçin Giriş Yapmalısınız")
            return redirect(url_for("login"))
    return decorated_function

#Şifre Güncelleme
class PasswordUpdateForm(Form):
    password = PasswordField("Mevcut Şifrenizi Girin")
    NewPassword = PasswordField("Yeni Şifrenizi Girin")
    confirm = PasswordField("Yeni Şifrenizi Girin")

# Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.DataRequired()])
    username = StringField("Kullanıcı Adı", validators=[validators.DataRequired()])
    email = StringField("Mail",validators=[validators.Email(message="Doğru e-posta giriniz"),validators.DataRequired()])
    password = PasswordField("Parola:",validators=[
        validators.EqualTo(fieldname="confirm",message="Parola uyuşmuyor")
    ])
    confirm = PasswordField("Şifrenizi Tekrar Giriniz")

# Login Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")

app = Flask(__name__)

app.secret_key="blog" # flash mesaj için

app.config["MYSQL_HOST"] ="localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blog"

#veritabanından alınan bilgilerin güzel gözükmesi için
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

#kök dizin
@app.route("/")#request
def index():
    return render_template("index.html") #response

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    cursor.execute(sorgu)
    data = cursor.fetchall()
    return render_template("articles.html",articles=data)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/articles/<string:id>") # Dinamik url
def article_dynamic(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select content FROM articles"
    cursor.execute(sorgu)
    data = cursor.fetchone()
    return data["content"]

@app.route("/my_articles/<string:id>") # Dinamik url
def myarticle_dynamic(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id = %s"
    cursor.execute(sorgu,(id,))
    data = cursor.fetchone()
    return data["content"]


# Kayıt Olma
@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        k_sorgu = "Select * FROM users WHERE username = %s "
        cursor = mysql.connection.cursor() # veritabanında işlem yapabilmek için cursor oluşturulmalı
        kontrol =cursor.execute(k_sorgu,(username,))
        m_sorgu = "Select * FROM users WHERE email = %s "
        if kontrol > 0:
            flash("Kullanıcı adı kullanılıyor","danger")
            return redirect(url_for("register"))
        kontrol = cursor.execute(m_sorgu,(email,))
        if kontrol > 0:
            flash("Mail Kullanılıyor","danger")
            return redirect(url_for("register"))
        sorgu = "Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()

        cursor.close()
        flash("Başarıyla Kayıt Olundu","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

#login işlemi
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        
        username = form.username.data
        password = form.password.data
        
        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password,real_password):
                flash("Başarıyla Giriş Yaptınız","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Şifrenizi Kontrol ediniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Yanlış Kullanıcı Adı","danger")
            return redirect(url_for("login"))

    else:
        return render_template("login.html",form=form)

#logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış Yaptınız","success")
    return redirect(url_for("index"))

#Hesap Ayarları
@app.route("/account")
@login_required
def account():
    sorgu = "Select * from users where username = %s"
    cursor = mysql.connection.cursor()
    cursor.execute(sorgu,(session["username"],))
    data = cursor.fetchone()
    return render_template("account.html",name=data["name"],mail=data["email"])

#Şifre Güncelleme
@app.route("/password_update",methods=["GET","POST"])
def password_update():
    form = PasswordUpdateForm(request.form)

    if request.method == "POST":
        password = form.password.data
        sorgu = "Select * from users where username = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu,(session["username"],))
        data = cursor.fetchone()
        real_password = data["password"]
        if sha256_crypt.verify(password,real_password):
            NewPassword = sha256_crypt.encrypt(form.NewPassword.data)
            sorgu2 = "UPDATE users SET password = %s WHERE username = %s "
            cursor.execute(sorgu2,(NewPassword,data["username"]))
            mysql.connection.commit()
            flash("Şifreniz Güncellenmiştir","success")
            return redirect(url_for("index"))
        else:
            flash("Şifrenizi Yanlış Girdiniz")
            return redirect(url_for("password_update"))
    else: 
        return render_template("password_update.html",form=form)

@app.route("/my_articles",methods=["GET","POST"])
@login_required
def my_articles():
    m_sorgu = "SELECT * FROM articles WHERE author = %s"
    cursor = mysql.connection.cursor()
    form = AddArticlesForm(request.form)
    cursor.execute(m_sorgu,(session["username"],))
    data = cursor.fetchall()
    if request.method == "POST":
        title = form.title.data
        content = form.content.data
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("account"))
    return render_template("my_articles.html",form=form,articles=data)

if __name__ == "__main__":
    app.run(debug=True) 