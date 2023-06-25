from app import create_app

# Crea una instancia de la aplicación Flask
app = create_app()

# Punto de entrada del programa
if __name__ == '__main__':
    # Ejecuta la aplicación en modo de desarrollo
    app.run(debug=True)
