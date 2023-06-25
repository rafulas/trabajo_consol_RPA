import mysql.connector
import json

class Image:
    def __init__(self, id, path, size, date):
        self.id = id
        self.path = path
        self.size = size
        self.date = date

class Tag:
    def __init__(self, tag, confidence):
        self.tag = tag
        self.confidence = confidence

def get_db_credentials():
    with open("credentials.json") as file:
        credentials = json.load(file)
    db_credentials = {
        'host': credentials['DB_HOST'],
        'user': credentials['DB_USER'],
        'password': credentials['DB_PASSWORD'],
        'database': credentials['DB_NAME']
    }
    return db_credentials

def get_image_by_id(image_id):
    # Obtener las credenciales de la base de datos
    db_credentials = get_db_credentials()

    # Conexión a la base de datos
    connection = mysql.connector.connect(**db_credentials)
    cursor = connection.cursor()

    # Consulta para obtener la imagen por ID
    query = "SELECT id, path, size, date FROM pictures WHERE id = %s"
    cursor.execute(query, (image_id,))
    result = cursor.fetchone()

    # Cerrar la conexión y el cursor
    cursor.close()
    connection.close()

    if result is not None:
        image = Image(*result)
        return image
    else:
        return None

def get_tags_by_image_id(image_id):
    # Obtener las credenciales de la base de datos
    db_credentials = get_db_credentials()

    # Conexión a la base de datos
    connection = mysql.connector.connect(**db_credentials)
    cursor = connection.cursor()

    # Consulta para obtener las etiquetas por ID de imagen
    query = "SELECT tag, confidence FROM tags WHERE picture_id = %s"
    cursor.execute(query, (image_id,))
    results = cursor.fetchall()

    # Cerrar la conexión y el cursor
    cursor.close()
    connection.close()

    tags = []
    for result in results:
        tag = Tag(*result)
        tags.append(tag)

    return tags
