from flask import Flask

def create_app():
    app = Flask(__name__)
    # existing code omitted

    from . import views
    app.register_blueprint(views.bp)

    return app