from itsdangerous import URLSafeTimedSerializer
from flask import request
from flask_jwt_extended import decode_token
from flask_jwt_extended.jwt_manager import ExpiredSignatureError, InvalidTokenError
from microservice_template_core.tools.logger import get_logger

logger = get_logger()


def get_user_id_by_token(auth_token):
    invalid_msg = {
        'message': 'Invalid token. Registration and / or authentication required',
        'authenticated': False
    }

    expired_msg = {
        'message': 'Expired token. Re authentication required',
        'authenticated': False
    }

    absent_token = {
        'message': 'AuthToken is not present in header of request',
        'authenticated': False
    }

    if auth_token is None:
        return absent_token, 401
    try:
        data = decode_token(auth_token, allow_expired=False)
        if data:
            return data['sub']
        else:
            # You can also redirect the user to the login page.
            logger.error(
                msg=f"User auth was failed\nMessage: {invalid_msg}\nHeader: {request.headers}"
            )
            return invalid_msg, 401

    except ExpiredSignatureError as err:
        logger.error(
            msg=f"User auth was failed\nMessage: {expired_msg}\nHeader: {request.headers}\nError: {err}"
        )
        return expired_msg, 401
    except (InvalidTokenError, Exception) as err:
        logger.error(
            msg=f"User auth was failed\nMessage: {invalid_msg}\nHeader: {request.headers}\nError: {err}"
        )
        return invalid_msg, 401
