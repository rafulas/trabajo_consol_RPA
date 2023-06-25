from . import models
from . import views
import os
import base64
from imagekitio import ImageKit
import requests
import json
from sqlalchemy import create_engine
import mysql.connector
import shutil
import datetime
import os
from dotenv import load_dotenv
from .models import get_image_by_id, get_tags_by_image_id
from flask import jsonify



# Cargar las variables de entorno desde el archivo credentials.json
# Cargar las variables de entorno desde el archivo credentials.json
def load_credentials():
    with open("credentials.json") as file:
        credentials = json.load(file)
    for key, value in credentials.items():
        os.environ[key] = str(value)
        
    return True



# Función para subir las fotos a imagekit y así obtener la url de la foto
def upload_image(data):
    load_credentials()
    imagekit = ImageKit(
        public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
        private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
        url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT")
    )

    
    # Esto es para subir una imagen a ImageKit. Para ello, necesitamos tener una imagen en la carpeta del proyecto, en este caso, image.jpeg y luego la codificamos en base64 para poder subirla a ImageKit
    with open(data, mode="rb") as img:
        imgstr = base64.b64encode(img.read())

    # Subimos la imagen a ImageKit, usando la instancia que hemos creado antes y la función upload de ImageKit. la url es accesible mediante `upload_info.url`
    upload_info = imagekit.upload(file=imgstr, file_name="image.jpg")
    print(upload_info)
    print("Imagen subida correctamente.")
    
    image_url = upload_info.url

    #Guardar la imagen en una carpeta temporal
    save_image(image_url)

    return upload_info




# Función para con la url de la foto en ImageKit, sacar las tags de la foto usado Imagga y devolverlas en un diccionario con la tag y la confianza

def get_tags (image_url,min_confidence):
    # Ahora hay que sacar las tags de la imagen que hemos subido a ImageKit. Para ello, definidmos las credenciales de Imagga
    load_credentials()
    API_KEY_IMAGGA = os.getenv("IMAGGA_API_KEY")
    API_SECRET_IMAGGA = os.getenv("IMAGGA_API_SECRET")

    # Hacemos la petición a Imagga para sacar las tags de la imagen que hemos subido a ImageKit. para ello, usamos la función get de requests pasándole la url de la imagen y las credenciales de Imagga como parámetros
    # y guardamos la respuesta en la variable response.La respuesta es un json, por lo que lo pasamos a diccionario con response.json()
    try:

        response = requests.get(f"https://api.imagga.com/v2/tags?image_url={image_url}", auth=(API_KEY_IMAGGA, API_SECRET_IMAGGA))

    # Si la petición ha ido bien, la respuesta es 200, por lo que podemos comprobar que las tags han ido bien. Para ello, usamos la función status_code de response. Si el cálculo de la confianza de la tag es mayor que 0.5, la guardamos en un diccionario
    # Sacamos las tags de la imagen que hemos subido a ImageKit. Para ello, hacemos un list comprehension, donde recorremos el diccionario que hemos sacado de la respuesta de Imagga y nos quedamos con las tags que tengan una confianza mayor de 0.5 (opcional) y guardamos las tags en la variable tags
    
        if response.status_code == 200:
            tags = [
                {
                    "tag": t["tag"]["en"],
                    "confidence": t["confidence"]
                }
                for t in response.json()["result"]["tags"]
                if t["confidence"] > min_confidence
            ]
            print(tags)
            return tags
        else:
            raise Exception("Error en la petición para obtener las etiquetas")

    except requests.exceptions.RequestException as e:
        raise Exception("Error en la conexión con Imagga: " + str(e))

    except KeyError as e:
        raise Exception("Error en el formato de respuesta de Imagga: " + str(e))

    except Exception as e:
        raise Exception("Error desconocido al obtener las etiquetas: " + str(e))

def update_bbdd(upload_info, tags):
    load_credentials()
    host = "localhost"
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT")

    # Establecer la conexión a la base de datos
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )

    # Cursor para ejecutar consultas SQL
    cursor = connection.cursor()


# Insertar fila en la tabla "pictures"
    insert_picture_query = "INSERT IGNORE INTO pictures (id, path, date) VALUES (%s, %s, %s)"
    picture_id = upload_info.file_id 
    picture_path = upload_info.url 
    picture_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    picture_values = (picture_id, picture_path, picture_date)
    cursor.execute(insert_picture_query, picture_values)

# Insertar filas en la tabla "tags"
    insert_tag_query = "INSERT IGNORE INTO tags (tag, picture_id, confidence, date) VALUES (%s, %s, %s, %s)"
    for item in tags:
        tag = item['tag']
        confidence = item['confidence']
        tag_values = (tag, picture_id, confidence, picture_date)
        cursor.execute(insert_tag_query, tag_values)

# Confirmar los cambios y cerrar la conexión
    connection.commit()
    cursor.close()
    connection.close()

    return True


# --------------------------------------------------
# Ahora, vamos a crear la carpeta temporal para guardar las imágenes
# --------------------------------------------------
def save_image(image_url):
    
    nombre_imagen = image_url.split("/")[-1] + '.jpg'
    carpeta_destino = './tmp'
    ruta_imagen_destino = os.path.join(carpeta_destino, nombre_imagen)

    # Crear la carpeta temporal si no existe
    # Para ello, usamos la librería os y la función makedirs que nos permite crear carpetas
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    # Obtenemos la imagen mediante la url y el get de requests. El varlor de stream=True es para que la descarga sea en streaming
    response = requests.get(image_url, stream=True)

    # Almacenamos la imagen en una carpeta temporal usando la librería shutil y la función copyfileobj que nos permite copiar el contenido de un fichero a otro
    # el with es para que se cierre el fichero automáticamente al terminar el bloque de código
    # el del es para borrar la imagen de la memoria
    with open(ruta_imagen_destino, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response

    # Comprobamos que la imagen se ha descargado correctamente
    if os.path.exists(ruta_imagen_destino):
        print('La imagen se ha descargado correctamente.')
    else:
        print('Ha ocurrido un error al descargar la imagen.')

    return True

def delete_image(image_file_id):
    load_credentials()
    imagekit = ImageKit(
        public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
        private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
        url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT")
    )
    
    delete = imagekit.delete_file(image_file_id )
    print(delete)
    print("Imagen borrada correctamente.")
    return True


def get_all_images(min_date, max_date, tags):
    load_credentials()
    images = []
    host = "localhost"
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT") 

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )

        cursor = connection.cursor(dictionary=True)
        query = "SELECT DISTINCT pictures.id, pictures.date FROM pictures"

        if tags is not None:
            tags_list = tags.split(",")
            query += " INNER JOIN tags ON pictures.id = tags.picture_id"
            query += " WHERE tags.tag IN (" + ",".join(["%s"] * len(tags_list)) + ")"
            params = tags_list
        else:
            params = []

        if min_date is not None:
            if "WHERE" not in query:
                query += " WHERE"
            else:
                query += " AND"
            query += " pictures.date >= %s"
            params.append(min_date)

        if max_date is not None:
            if "WHERE" not in query:
                query += " WHERE"
            else:
                query += " AND"
            query += " pictures.date <= %s"
            params.append(max_date)

        cursor.execute(query, params)
        for row in cursor.fetchall():
            images.append({
                "id": row["id"],
                "date": row["date"]
            })

    except mysql.connector.Error as e:
        raise Exception("Error al obtener las imágenes: " + str(e))

    finally:
        cursor.close()
        connection.close()

    return images


def get_image_by_id(image_id):
    load_credentials()
    
    host = "localhost"
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    port = os.getenv("DB_PORT") 

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )

        cursor = connection.cursor(dictionary=True)
        query = "SELECT path FROM pictures WHERE id = %s"
        cursor.execute(query, (image_id,))

        row = cursor.fetchone()

        if row is None:
            raise FileNotFoundError("Image not found")

        with open(row["path"], "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        image_data = {"image": img_base64}

    except mysql.connector.Error as error:
        raise Exception(str(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return image_data

