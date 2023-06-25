from flask import Blueprint, request, make_response
from . import controller

import datetime
import os
import shutil
import requests
from flask import jsonify



bp = Blueprint('images', __name__, url_prefix='/')

@bp.route("/upload_image", methods=['POST'])
def upload_image():
    data=request.json.get('data')
    min_confidence = float(request.args.get("min_confidence", 0.8))

    if not data:
        return jsonify({"description": "Debes incluir la ruta de la imagen como un campo llamado data en el body"}), 400
    
    try:
        
        upload_info = controller.upload_image(data)
        print(upload_info)
        image_url = upload_info.url
        tags=controller.get_tags(image_url,min_confidence)
        controller.save_image(image_url)
        controller.update_bbdd(upload_info, tags)
        # controller.delete_image(upload_info.file_id)

        response_data= {
            "id":upload_info.file_id,
            "size": upload_info.size,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tags": tags
        }

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"description": str(e)}), 500

@bp.route("/get_images", methods=['GET'])
def get_images():
    min_date = request.args.get("min_date",None)
    max_date = request.args.get("max_date",None)
    tags = request.args.get("tags",None)

    try:
        images_list = controller.get_all_images(min_date, max_date, tags)
        return jsonify(images_list), 200

    except Exception as e:
        return jsonify({"description": str(e)}), 500



@bp.route("/image/<image_id>", methods=["GET"])
def get_image_by_id(image_id):
    try:
        image_data = controller.get_image_by_id(image_id)
        return jsonify(image_data), 200
    except FileNotFoundError:
        return {"error": "Image not found"}, 404
    except Exception as error:
        return {"error": str(error)}, 500
