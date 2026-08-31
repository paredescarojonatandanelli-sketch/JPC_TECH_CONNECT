import os

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_FILE = os.path.join(DATABASE_DIR, "clientes.db")

os.makedirs(DATABASE_DIR, exist_ok=True)


app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "JPC-TECH-CLAVE-LOCAL-2026"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + DATABASE_FILE.replace("\\", "/")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)
with app.app_context():
    db.create_all()


class Cliente(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(100), nullable=False)

    whatsapp = db.Column(db.String(30), nullable=False)

    correo = db.Column(db.String(120))

    equipo = db.Column(db.String(100))

    necesidad = db.Column(db.Text)

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="Nuevo"
    )

    origen = db.Column(
        db.String(50),
        nullable=False,
        default="QR"
    )

    fecha_registro = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

class HistorialCliente(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("cliente.id"),
        nullable=False
    )

    tipo = db.Column(
        db.String(50),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    fecha = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref(
            "historial",
            lazy=True
        )
    )

class SolicitudAsesoria(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("cliente.id"),
        nullable=False
    )

    tipo = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="Nueva"
    )

    fecha = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref(
            "solicitudes",
            lazy=True
        )
    )


class Cotizacion(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("cliente.id"),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    cantidad = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    precio_unitario = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    estado = db.Column(
        db.String(30),
        nullable=False,
        default="Pendiente"
    )

    observaciones = db.Column(
        db.Text
    )

    fecha = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref(
            "cotizaciones",
            lazy=True
        )
    )



@app.route("/")
def inicio():


    return render_template("inicio.html")
@app.route("/beneficios")

def beneficios():
    return render_template("beneficios.html")

@app.route("/perfil/<int:cliente_id>")
def perfil(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    historial = HistorialCliente.query.filter_by(
        cliente_id=cliente.id
    ).order_by(
        HistorialCliente.fecha.desc()
    ).all()

    return render_template(
        "perfil.html",
        cliente=cliente,
        historial=historial
    )
@app.route(
    "/solicitar-asesoria/<int:cliente_id>",
    methods=["GET", "POST"]
)
def solicitar_asesoria(cliente_id):

    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == "POST":

        tipo = request.form.get("tipo")
        descripcion = request.form.get("descripcion")

        solicitud = SolicitudAsesoria(
            cliente_id=cliente.id,
            tipo=tipo,
            descripcion=descripcion
        )

        db.session.add(solicitud)
        db.session.commit()

        return redirect(
            url_for(
                "perfil",
                cliente_id=cliente.id
            )
        )

    return render_template(
        "solicitar_asesoria.html",
        cliente=cliente
    )
@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre")
        whatsapp = request.form.get("whatsapp")
        correo = request.form.get("correo")
        equipo = request.form.get("equipo")
        necesidad = request.form.get("necesidad")
        origen = request.form.get("origen", "QR")
        nuevo_cliente = Cliente(
            nombre=nombre,
            whatsapp=whatsapp,
            correo=correo,
            equipo=equipo,
            necesidad=necesidad,
            origen=origen
        )

        db.session.add(nuevo_cliente) 
        db.session.commit()

        return render_template(
            "bienvenida.html",
            cliente=nuevo_cliente
        )
        
    return render_template("registro.html")


@app.route("/registro-exitoso")
def registro_exitoso():

    nombre = request.args.get("nombre", "Cliente")

    return render_template(
        "registro_exitoso.html",
        nombre=nombre
    )

@app.route("/admin", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form.get("usuario")
        password = request.form.get("password")

        if usuario == "admin" and password == "JPC2026":

            session["admin"] = True

            return redirect(url_for("panel"))

        return render_template(
            "login.html",
            error="Usuario o contraseÃ±a incorrectos."
        )

    return render_template("login.html")

@app.route("/admin/panel")
def panel():

    if not session.get("admin"):
        return redirect(url_for("login"))

    busqueda = request.args.get("buscar", "").strip()

    if busqueda:

        clientes = Cliente.query.filter(
            db.or_(
                Cliente.nombre.ilike(f"%{busqueda}%"),
                Cliente.whatsapp.ilike(f"%{busqueda}%")
            )
        ).order_by(
            Cliente.id.desc()
        ).all()

    else:

        clientes = Cliente.query.order_by(
            Cliente.id.desc()
        ).all()

    solicitudes = SolicitudAsesoria.query.order_by(
        SolicitudAsesoria.id.desc()
    ).all()

    total_solicitudes = len(solicitudes)

    nuevas = sum(
        1 for s in solicitudes
        if s.estado == "Nueva"
    )

    en_revision = sum(
        1 for s in solicitudes
        if s.estado == "En revisiÃ³n"
    )

    contactadas = sum(
        1 for s in solicitudes
        if s.estado == "Contactado"
    )

    atendidas = sum(
        1 for s in solicitudes
        if s.estado == "Atendida"
    )

    cerradas = sum(
        1 for s in solicitudes
        if s.estado == "Cerrada"
    )

    return render_template(
        "panel.html",
        clientes=clientes,
        busqueda=busqueda,
        solicitudes=solicitudes,
        total_solicitudes=total_solicitudes,
        nuevas=nuevas,
        en_revision=en_revision,
        contactadas=contactadas,
        atendidas=atendidas,
        cerradas=cerradas
    )

@app.route(
    "/admin/solicitud/<int:solicitud_id>/estado",
    methods=["POST"]
)
def actualizar_estado_solicitud(solicitud_id):

    if not session.get("admin"):
        return redirect(url_for("login"))

    solicitud = SolicitudAsesoria.query.get_or_404(
        solicitud_id
    )

    nuevo_estado = request.form.get("estado")

    estados_validos = [
    "Nuevo",
    "Contactado",
    "Consulta",
    "CotizaciÃ³n",
    "Servicio",
    "Finalizado",
    "Cliente recurrente"
]
    if nuevo_estado in estados_validos:

        solicitud.estado = nuevo_estado

        db.session.commit()

    return redirect(
        url_for("panel")
    )


@app.route(
    "/admin/solicitud/<int:solicitud_id>/registrar-servicio",
    methods=["POST"]
)
def registrar_servicio_solicitud(solicitud_id):

    if not session.get("admin"):
        return redirect(url_for("login"))

    solicitud = db.session.get(
        SolicitudAsesoria,
        solicitud_id
    )

    if solicitud is None:
        return "Solicitud no encontrada", 404

    # Solo se puede registrar como servicio
    # una solicitud que estÃ© atendida.
    if solicitud.estado != "Atendida":
        return redirect(
            url_for("panel")
        )

    # Evitar registrar dos veces
    servicio_existente = HistorialCliente.query.filter_by(
        cliente_id=solicitud.cliente_id,
        tipo="Servicio",
        descripcion=solicitud.descripcion
    ).first()

    if servicio_existente is None:

        historial = HistorialCliente(
            cliente_id=solicitud.cliente_id,
            tipo="Servicio",
            descripcion=solicitud.descripcion
        )

        db.session.add(historial)

    # La solicitud queda cerrada
    solicitud.estado = "Cerrada"

    db.session.commit()

    return redirect(
        url_for(
            "cliente_detalle",
            cliente_id=solicitud.cliente_id
        )
    )

@app.route("/admin/logout")
def logout():

    session.pop("admin", None)

    return redirect(url_for("login"))
@app.route(
    "/admin/cliente/<int:cliente_id>",
    methods=["GET", "POST"]
)
def cliente_detalle(cliente_id):

    if not session.get("admin"):
        return redirect(url_for("login"))

    cliente = db.session.get(Cliente, cliente_id)

    if cliente is None:
        return "Cliente no encontrado", 404

    if request.method == "POST":

        nuevo_estado = request.form.get("estado", "").strip()

        estados_validos = [
            "Nuevo",
            "Contactado",
            "Consulta",
            "CotizaciÃ³n",
            "Servicio",
            "Finalizado",
            "Cliente recurrente"
        ]

        if nuevo_estado in estados_validos:

            cliente.estado = nuevo_estado
            db.session.commit()

        return redirect(
            url_for(
                "cliente_detalle",
                cliente_id=cliente.id
            )
        )
    historial = HistorialCliente.query.filter_by(
        cliente_id=cliente.id
    ).order_by(
        HistorialCliente.fecha.desc()
    ).all()

    total_solicitudes = SolicitudAsesoria.query.filter_by(
        cliente_id=cliente.id
    ).count()

    total_historial = HistorialCliente.query.filter_by(
        cliente_id=cliente.id
    ).count()

    total_seguimientos = HistorialCliente.query.filter_by(
        cliente_id=cliente.id,
        tipo="Seguimiento"
    ).count()

    total_servicios = HistorialCliente.query.filter(
        HistorialCliente.cliente_id == cliente.id,
        db.func.trim(HistorialCliente.tipo) == "Servicio"
    ).count()

    cotizaciones = Cotizacion.query.filter_by(
        cliente_id=cliente.id
    ).order_by(
        Cotizacion.fecha.desc()
    ).all()

    total_cotizaciones = len(cotizaciones)

    return render_template(
        "cliente_detalle.html",
        cliente=cliente,
        historial=historial,
        total_solicitudes=total_solicitudes,
        total_historial=total_historial,
        total_seguimientos=total_seguimientos,
        total_servicios=total_servicios,
        total_cotizaciones=total_cotizaciones,
        cotizaciones=cotizaciones
    )

@app.route(
    "/admin/cliente/<int:cliente_id>/historial",
    methods=["POST"]
)
def agregar_historial(cliente_id):

    if not session.get("admin"):
        return redirect(url_for("login"))

    cliente = db.session.get(Cliente, cliente_id)

    if cliente is None:
        return "Cliente no encontrado", 404

    tipo = request.form.get("tipo", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    tipos_validos = [
        "Contacto",
        "Consulta",
        "DiagnÃ³stico",
        "CotizaciÃ³n",
        "Servicio",
        "Seguimiento",
        "Otro"
    ]

    if tipo not in tipos_validos:
        return "Tipo de seguimiento no vÃ¡lido", 400

    if not descripcion:
        return "La descripciÃ³n es obligatoria", 400

    nuevo_historial = HistorialCliente(
        cliente_id=cliente.id,
        tipo=tipo,
        descripcion=descripcion
    )

    db.session.add(nuevo_historial)
    db.session.commit()

    return redirect(
        url_for(
            "cliente_detalle",
            cliente_id=cliente.id
        )
    )

@app.route(
    "/admin/cliente/<int:cliente_id>/cotizacion/nueva",
    methods=["GET", "POST"]
)
def nueva_cotizacion(cliente_id):

    if not session.get("admin"):
        return redirect(url_for("login"))

    cliente = db.session.get(Cliente, cliente_id)

    if cliente is None:
        return "Cliente no encontrado", 404

    if request.method == "POST":

        descripcion = request.form.get(
            "descripcion",
            ""
        ).strip()

        cantidad = request.form.get(
            "cantidad",
            "1"
        ).strip()

        precio_unitario = request.form.get(
            "precio_unitario",
            "0"
        ).strip()

        estado = request.form.get(
            "estado",
            "Pendiente"
        ).strip()

        observaciones = request.form.get(
            "observaciones",
            ""
        ).strip()

        if not descripcion:
            return "La descripciÃ³n es obligatoria", 400

        try:
            cantidad = int(cantidad)
            precio_unitario = float(precio_unitario)
        except ValueError:
            return "Cantidad o precio no vÃ¡lido", 400

        if cantidad <= 0:
            return "La cantidad debe ser mayor que cero", 400

        if precio_unitario < 0:
            return "El precio no puede ser negativo", 400

        estados_validos = [
            "Pendiente",
            "Enviada",
            "Aceptada",
            "Rechazada",
            "Vencida"
        ]

        if estado not in estados_validos:
            return "Estado de cotizaciÃ³n no vÃ¡lido", 400

        total = cantidad * precio_unitario

        cotizacion = Cotizacion(
            cliente_id=cliente.id,
            descripcion=descripcion,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            total=total,
            estado=estado,
            observaciones=observaciones
        )

        db.session.add(cotizacion)
        db.session.commit()

        return redirect(
            url_for(
                "cliente_detalle",
                cliente_id=cliente.id
            )
        )

    return render_template(
        "nueva_cotizacion.html",
        cliente=cliente
    )


@app.route(
    "/admin/cotizacion/<int:cotizacion_id>/estado",
    methods=["POST"]
)
def cambiar_estado_cotizacion(cotizacion_id):

    if not session.get("admin"):
        return redirect(url_for("login"))

    cotizacion = db.session.get(
        Cotizacion,
        cotizacion_id
    )

    if cotizacion is None:
        return "CotizaciÃ³n no encontrada", 404

    nuevo_estado = request.form.get(
        "estado",
        ""
    ).strip()

    estados_validos = [
        "Pendiente",
        "Enviada",
        "Aceptada",
        "Rechazada",
        "Vencida"
    ]

    if nuevo_estado not in estados_validos:
        return "Estado de cotizaciÃ³n no vÃ¡lido", 400

    cotizacion.estado = nuevo_estado

    db.session.commit()

    return redirect(
        url_for(
            "cliente_detalle",
            cliente_id=cotizacion.cliente_id
        )
    )

    
@app.route(
    "/admin/cotizacion/<int:cotizacion_id>",
    methods=["GET"]
)
def ver_cotizacion(cotizacion_id):

    if not session.get("admin"):
        return redirect(url_for("login"))

    cotizacion = db.session.get(
        Cotizacion,
        cotizacion_id
    )

    if cotizacion is None:
        return "Cotizacion no encontrada", 404

    cliente = db.session.get(
        Cliente,
        cotizacion.cliente_id
    )

    if cliente is None:
        return "Cliente no encontrado", 404

    return render_template(
        "ver_cotizacion.html",
        cotizacion=cotizacion,
        cliente=cliente
    )
@app.route("/atencion")
def atencion():
    return render_template("atencion.html")


@app.route("/atencion/registro", methods=["GET", "POST"])
def registro_atencion():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        whatsapp = request.form.get("whatsapp", "").strip()
        correo = request.form.get("correo", "").strip()
        equipo = request.form.get("equipo", "").strip()
        necesidad = request.form.get("necesidad", "").strip()

        if not nombre:
            return "El nombre es obligatorio", 400

        if not whatsapp:
            return "El WhatsApp es obligatorio", 400

        cliente = Cliente(
            nombre=nombre,
            whatsapp=whatsapp,
            correo=correo,
            equipo=equipo,
            necesidad=necesidad,
            estado="Nuevo",
            origen="QR"
        )

        db.session.add(cliente)
        db.session.commit()

        return redirect(
            url_for(
                "solicitar_asesoria",
                cliente_id=cliente.id
            )
        )

    return render_template("registro_atencion.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)