import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-antes-de-publicar")
database_url = os.environ.get("DATABASE_URL", "sqlite:///emanuely.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Text, default="")

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.String(40), default="Consultar")
    image_url = db.Column(db.Text, default="")
    active = db.Column(db.Boolean, default=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.String(40), default="Consultar")
    image_url = db.Column(db.Text, default="")
    active = db.Column(db.Boolean, default=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    service_name = db.Column(db.String(120), nullable=False)
    requested_date = db.Column(db.String(40), nullable=False)
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(30), default="Pendente")

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

def get_setting(key, default=""):
    item = Setting.query.filter_by(key=key).first()
    return item.value if item else default

@app.context_processor
def shared_settings():
    return {"site_name": get_setting("site_name", "Emanuely Matos"),
            "whatsapp": get_setting("whatsapp", "")}

@app.route("/")
def home():
    services = Service.query.filter_by(active=True).all()
    products = Product.query.filter_by(active=True).all()
    return render_template("home.html", services=services, products=products,
        headline=get_setting("headline", "Realce sua beleza com cuidado e naturalidade."),
        about=get_setting("about", "Um atendimento acolhedor, pensado para você."),
        hero_image=get_setting("hero_image", ""))

@app.route("/agendar", methods=["POST"])
def book():
    appointment = Appointment(
        customer_name=request.form.get("name", "").strip(),
        phone=request.form.get("phone", "").strip(),
        service_name=request.form.get("service", "").strip(),
        requested_date=request.form.get("date", "").strip(),
        message=request.form.get("message", "").strip()
    )
    if not all([appointment.customer_name, appointment.phone, appointment.service_name, appointment.requested_date]):
        flash("Preencha nome, telefone, procedimento e data desejada.")
        return redirect(url_for("home") + "#agendar")
    db.session.add(appointment)
    db.session.commit()
    flash("Solicitação recebida! Aguarde a confirmação do atendimento.")
    return redirect(url_for("home") + "#agendar")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = get_setting("admin_username", "")
        password_hash = get_setting("admin_password_hash", "")
        if request.form.get("username") == username and password_hash and check_password_hash(password_hash, request.form.get("password", "")):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Usuário ou senha incorretos.")
    return render_template("login.html")

@app.route("/admin/sair")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html",
        services=Service.query.order_by(Service.id.desc()).all(),
        products=Product.query.order_by(Product.id.desc()).all(),
        appointments=Appointment.query.order_by(Appointment.id.desc()).all(),
        settings={k:get_setting(k, d) for k,d in [
            ("site_name","Emanuely Matos"),("headline",""),("about",""),
            ("hero_image",""),("whatsapp","") ]})

@app.route("/admin/configurar", methods=["POST"])
@admin_required
def save_settings():
    for key in ["site_name", "headline", "about", "hero_image", "whatsapp"]:
        item = Setting.query.filter_by(key=key).first()
        if not item:
            item = Setting(key=key)
            db.session.add(item)
        item.value = request.form.get(key, "").strip()
    db.session.commit()
    flash("Informações do site atualizadas.")
    return redirect(url_for("admin"))

@app.route("/admin/item/<kind>", methods=["POST"])
@admin_required
def save_item(kind):
    model = Service if kind == "procedimentos" else Product if kind == "produtos" else None
    if not model:
        return redirect(url_for("admin"))
    item_id = request.form.get("id", type=int)
    item = db.session.get(model, item_id) if item_id else model()
    if not item_id:
        db.session.add(item)
    item.name = request.form.get("name", "").strip()
    item.description = request.form.get("description", "").strip()
    item.price = request.form.get("price", "Consultar").strip()
    item.image_url = request.form.get("image_url", "").strip()
    item.active = request.form.get("active") == "on"
    if not item.name:
        flash("O nome é obrigatório.")
    else:
        db.session.commit()
        flash("Cadastro salvo.")
    return redirect(url_for("admin") + "#" + kind)

@app.route("/admin/item/<kind>/<int:item_id>/excluir", methods=["POST"])
@admin_required
def delete_item(kind, item_id):
    model = Service if kind == "procedimentos" else Product if kind == "produtos" else None
    item = db.session.get(model, item_id) if model else None
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Cadastro excluído.")
    return redirect(url_for("admin") + "#" + kind)

@app.route("/admin/agendamento/<int:appointment_id>", methods=["POST"])
@admin_required
def update_appointment(appointment_id):
    item = db.session.get(Appointment, appointment_id)
    if item:
        item.status = request.form.get("status", "Pendente")
        db.session.commit()
        flash("Status do agendamento atualizado.")
    return redirect(url_for("admin") + "#agendamentos")

def initialize():
    with app.app_context():
        db.create_all()
        defaults = {
            "site_name": "Emanuely Matos",
            "headline": "Realce sua beleza com cuidado e naturalidade.",
            "about": "Um atendimento acolhedor, pensado para valorizar sua beleza. Edite este texto no painel administrativo.",
            "hero_image": "",
            "whatsapp": "",
        }
        for key, value in defaults.items():
            if not Setting.query.filter_by(key=key).first():
                db.session.add(Setting(key=key, value=value))
        # Cria o primeiro acesso apenas se as variáveis de ambiente forem fornecidas.
        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")
        if username and password and not Setting.query.filter_by(key="admin_username").first():
            db.session.add(Setting(key="admin_username", value=username))
            db.session.add(Setting(key="admin_password_hash", value=generate_password_hash(password)))
        db.session.commit()

initialize()

if __name__ == "__main__":
    app.run(debug=True)
