from odoo import http
from odoo.http import request
from datetime import date, datetime
import json

class BaseApiController(http.Controller):
    """
        A Base class for API controllers
        Adds consistent JSON response formatting and datetime-safe serialization.
    """

    def _ensure_user_env(self):
        """Ensure the request has a valid user environment."""
        if not request.env.user or not request.env.uid:
            user = request.env['res.users'].sudo().search([], limit=1)
            request.update_env(user=user.id)

    def _json_response(self, status, message=None, data=None, http_status=200):
        def convert_value(value):
            """Convert non-serializable values (like datetime) to strings."""
            if isinstance(value, datetime):
                return value.strftime('%d-%m-%Y %H:%M:%S')
            elif isinstance(value,  date):
                return value.strftime('%d-%m-%Y')
            elif isinstance(value, list):
                return [convert_value(v) for v in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            return value

        safe_data = convert_value(data) if data is not None else None

        response = {'status': status}
        if message:
            response['message'] = message
        if safe_data is not None:
            response['data'] = safe_data

        return request.make_response(
            json.dumps(response),
            headers=[('Content-Type', 'application/json')],
            status=http_status
        )
