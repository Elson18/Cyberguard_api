from flask import jsonify

def success_response(message="Operation completed successfully.", data=None, status_code=200):
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code

def error_response(message="Error occurred.", status_code=400):
    response = {
        "success": False,
        "message": message
    }
    return jsonify(response), status_code
