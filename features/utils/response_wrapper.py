# utils/response_wrapper.py
from rest_framework.response import Response

def success_response(data=None, message="Success", status=200):
    return Response({
        "status": "success",
        "message": message,
        "data": data
    }, status=status)

def error_response(message="Something went wrong", status=400, data=None):
    return Response({
        "status": "error",
        "message": message,
        "data": data or {}
    }, status=status)
