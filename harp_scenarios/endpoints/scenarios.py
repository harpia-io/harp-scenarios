from microservice_template_core.tools.flask_restplus import api
from flask_restplus import Resource
from harp_scenarios.models.scenarios import Scenarios, ScenarioSchema
from flask import request
import traceback
from microservice_template_core.tools.logger import get_logger
from werkzeug.exceptions import BadRequest
from microservice_template_core.decorators.auth_decorator import token_required
from harp_scenarios.logic.token import get_user_id_by_token
import json


logger = get_logger()
ns = api.namespace('api/v1/scenarios', description='Harp scenarios endpoints')
scenarios = ScenarioSchema()


@ns.route('')
class CreateScenario(Resource):
    @staticmethod
    # @token_required()
    def put():
        """
        Add scenario object
        Use this method to create new Scenario
        * Send a JSON object
        ```
        {
            "username": "nkondratyk", # Optional - if we don`t use auth token (for communications between services)
            "environment_id": 1, # Optional
            "scenario_name": "New Scenario",
            "description": "Scenario description",
            "external_url": "http://some_url",
            "requested_by": "The reason of creating it",
            "tags": ["tag1", "tag2", "tag3"],
            "scenario_type": 1,
            "scenario_actions": [
                {
                    "execute_after_seconds": 0,
                    "type": "ui",
                    "body": {
                        "recipients": ["asd"], "description": "asd", "affected_func": "asd", "should_check": ["ads"],
                        "players_expirience": "asd", "not_handled_effects": "ads", "notification_period": {}
                    }
                },
                {
                    "execute_after_seconds": 60,
                    "type": "teams",
                    "body": {
                        "ids": ["some_teams_id"], "notification_period": {}, "description": "Teams procedure", "resubmit": null
                    }
                }
            ]
        }
        ```
        """
        auth_token = request.headers.get('AuthToken')
        data = request.get_json()

        if auth_token:
            username = get_user_id_by_token(auth_token)
        elif 'username' in data:
            username = data['username']
        else:
            return f"username was not detected in AuthToken header and not inside scenario JSON Payload", 400

        try:
            data['edited_by'] = username
            if 'environment_id' not in data:
                data['environment_id'] = None

            new_obj = Scenarios.add(data)
            result = scenarios.dump(new_obj.dict())
        except ValueError as err:
            logger.warning(
                msg=f"Client error during adding new scenario - {err}\nTrace: {traceback.format_exc()}")
            return {"msg": f"Client error during adding new scenario - {err}"}, 400
        except Exception as err:
            logger.critical(msg=f"Backend error during adding new scenario - {err}\nTrace: {traceback.format_exc()}")
            return {'msg': f'Client error during adding new scenario - {err}'}, 500

        return result, 200


@ns.route('/<int:scenario_id>')
class EditScenario(Resource):
    # TODO Disable token for internal calls (service to service communication)
    @staticmethod
    # @token_required()
    def get(scenario_id):
        """
            Return Scenario object by ID
        """
        try:
            if not scenario_id:
                return {'msg': 'scenario_id should be specified'}, 404
            obj = Scenarios.obj_exist(scenario_id=scenario_id)
            if not obj:
                return {'msg': f'object with scenario_id - {scenario_id} is not found'}, 404
            result = scenarios.dump(obj.dict())
        except Exception as err:
            logger.error(msg=f"Error: {str(err)}, trace: {traceback.format_exc()}")
            return {"msg": f"Error on backend: {str(err)}. More details you can find in logs"}, 500
        return {"msg": result}, 200

    @staticmethod
    @token_required()
    def post(scenario_id):
        """
        Updates existing object with specified scenario_id
        Use this method to update existing Scenario
        * Send a JSON object
        ```
        {
            "scenario_name": "New Scenario",
            "environment_id": 1, # Optional
            "description": "Scenario description",
            "external_url": "http://some_url",
            "requested_by": "The reason of creating it",
            "tags": ["tag1", "tag2", "tag3"],
            "scenario_type": 1,
            "scenario_actions": [
                {
                    "execute_after_seconds": 0,
                    "type": "ui",
                    "body": {
                        "recipients": ["asd"], "description": "asd", "affected_func": "asd", "should_check": ["ads"],
                        "players_expirience": "asd", "not_handled_effects": "ads", "notification_period": {}
                    }
                },
                {
                    "execute_after_seconds": 60,
                    "type": "teams",
                    "body": {
                        "ids": ["some_teams_id"], "notification_period": {}, "description": "Teams procedure", "resubmit": null
                    }
                }
            ]
        }
        ```
        """
        auth_token = request.headers.get('AuthToken')
        username = get_user_id_by_token(auth_token)

        if not scenario_id:
            return 'scenario_id should be specified', 404
        obj = Scenarios.obj_exist(scenario_id=scenario_id)
        if not obj:
            return f'Scenario with specified id is not exist - {scenario_id}', 404
        try:
            data = request.get_json()
            data['edited_by'] = username
            if 'environment_id' not in data:
                data['environment_id'] = None

            obj.update_existing_scenario(data, scenario_id=scenario_id)
            result = scenarios.dump(obj.dict())
        except ValueError as val_exc:
            logger.warning(
                msg=f"Scenario updating exception - {val_exc}\nTrace: {traceback.format_exc()}")
            return {"msg": str(val_exc)}, 400
        except BadRequest as bad_request:
            logger.warning(
                msg=f"Scenario updating exception - {bad_request}\nTrace: {traceback.format_exc()}")
            return {'msg': str(bad_request)}, 400
        except Exception as exc:
            logger.critical(
                msg=f"Scenario updating exception - {exc}\nTrace: {traceback.format_exc()}")
            return {'msg': f'Exception raised - {exc}. Check logs for additional info'}, 500

        return result, 200

    @staticmethod
    @token_required()
    def delete(scenario_id):
        """
            Delete Scenario object with specified id
        """
        if not scenario_id:
            return {'msg': f'scenario_id should be specified'}, 404
        obj = Scenarios.obj_exist(scenario_id=scenario_id)
        try:
            if obj:
                obj.delete_obj()
                logger.info(msg=f"Scenario deletion. Id: {scenario_id}")
            else:
                return {'msg': f'Object with specified scenario_id - {scenario_id} is not found'}, 404
        except Exception as exc:
            logger.critical(
                msg=f"Scenario deletion exception - {exc}\nTrace: {traceback.format_exc()}")
            return {'msg': f'Deletion of scenario with id: {scenario_id} failed. '
                           f'Exception: {str(exc)}'}, 500
        return {'msg': f"Scenario with id: {scenario_id} successfully deleted"}, 200


@ns.route('/all')
class GetAllScenarios(Resource):
    @staticmethod
    @api.response(200, 'Info has been collected')
    def get():
        """
        Return All exist Scenarios
        """

        new_obj = Scenarios.get_all_scenarios()
        print(new_obj)
        result = {'scenarios': new_obj}

        return result, 200


@ns.route('/search')
class ScenarioSearch(Resource):
    @token_required()
    def post(self):
        """
        Search scenario by different fields
        ```
        You should choose one of the field to search. For example by scenario_name
        {
            "scenario_name": "Some name",
            "pattern": "some pattern",
            "tags": "some_tag",
            "scenario_type": 1,
            "scenario_id": 1,
            "environment_id": 12
        }
        ```
        """
        data = request.get_json()
        logger.info(f"Start search scenario Request body: {json.dumps(data)}")
        result = Scenarios.search(data)

        return {'msg': result}, 200


@ns.route('/search-actions')
class ScenarioSearch(Resource):
    @token_required()
    def post(self):
        """
        Get list of unique actions
        ```
        To get list of actions for specific Env in Org
        {
            "environment_id": 12
        }
        ```
                ```
        To get list of actions for all Env in Org
        {
            "environment_id": "all"
        }
        ```
        """
        data = request.get_json()
        if 'environment_id' not in data:
            return 'environment_id should be specified in JSON Payload', 400

        logger.info(f"Start search scenario Request body: {json.dumps(data)}")
        result = Scenarios.search_actions(data)

        return {'msg': result}, 200


@ns.route('/<string:scenario_name>')
class GetScenarioByName(Resource):
    @staticmethod
    def get(scenario_name):
        """
            Return Scenario object by name
        """
        if not scenario_name:
            return {'msg': 'scenario_name should be specified'}, 404
        obj = Scenarios.obj_exist(scenario_name=scenario_name)
        if not obj:
            return {'msg': f"object with scenario_name - {scenario_name} is not found"}, 404
        result = scenarios.dump(obj.dict())
        return {"msg": result}, 200
