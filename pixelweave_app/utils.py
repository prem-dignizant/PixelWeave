from rest_framework.response import Response
from rest_framework import status

def wrap_response(success, code, data=None, errors=None, status_code=status.HTTP_200_OK,message=None):
    response_data = {
        "success": success,
        "code": code
    }
    if errors:
        response_data["errors"] = errors
    if data != None:
        response_data["data"] = data
    if message:
        response_data["message"] = message
    
    if not success:
        status_code = status.HTTP_400_BAD_REQUEST

    return Response(response_data, status=status_code)