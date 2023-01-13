import traceback
from flask import abort
from microservice_template_core import db
import datetime
import json
from marshmallow import Schema, fields
from microservice_template_core.tools.logger import get_logger

logger = get_logger()


class Scenarios(db.Model):
    __tablename__ = 'scenarios'

    scenario_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scenario_name = db.Column(db.VARCHAR(256), nullable=False)
    environment_id = db.Column(db.VARCHAR(256), nullable=True)
    description = db.Column(db.String(1000), nullable=False)
    external_url = db.Column(db.String(200), nullable=True)
    requested_by = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.Text(4294000000), nullable=False, default='[]')
    scenario_type = db.Column(db.Integer, nullable=False, default=0)
    scenario_review_status = db.Column(db.String(50), default=None)
    edited_by = db.Column(db.String(50), default=None)
    scenario_actions = db.Column(db.Text(4294000000), default='[]')
    last_update_ts = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow(), nullable=False)
    create_ts = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow(), nullable=False)

    def __repr__(self):
        return f"{self.scenario_id}_{self.scenario_name}"

    def dict(self):
        return {
            'scenario_id': self.scenario_id,
            'scenario_name': self.scenario_name,
            'environment_id': self.environment_id,
            'description': self.description,
            'external_url': self.external_url,
            'requested_by': self.requested_by,
            'tags': json.loads(self.tags),
            'scenario_type': self.scenario_type,
            'scenario_review_status': self.scenario_review_status,
            'edited_by': self.edited_by,
            'scenario_actions': json.loads(self.scenario_actions),
            'create_ts': self.create_ts,
            'last_update_ts': self.last_update_ts
        }

    def return_all_scenario_dict(self):
        return {
            'scenario_id': self.scenario_id,
            'scenario_name': self.scenario_name,
            'environment_id': self.environment_id,
            'description': self.description,
            'external_url': self.external_url,
            'requested_by': self.requested_by,
            'tags': json.loads(self.tags),
            'scenario_type': self.scenario_type,
            'scenario_review_status': self.scenario_review_status,
            'edited_by': self.edited_by,
            'scenario_actions': json.loads(self.scenario_actions)
        }

    def update_existing_scenario(self, data, scenario_id):
        same_name_scenario = Scenarios.query.filter_by(
            scenario_name=data['scenario_name']
        ).all()

        if same_name_scenario:
            if len(same_name_scenario) == 1 and same_name_scenario[0].scenario_id == self.scenario_id:
                pass
            else:
                abort(400, f"Scenario with the same name is already exist - {data['scenario_name']}")

        if 'tags' in data:
            data['tags'] = json.dumps(data['tags'])

        if 'scenario_actions' in data:
            data['scenario_actions'] = json.dumps(data['scenario_actions'])

        self.query.filter_by(scenario_id=scenario_id).update(data)

        db.session.commit()

    @classmethod
    def add(cls, data):
        exist_scenarios = cls.query.filter_by(scenario_name=data['scenario_name']).one_or_none()
        if exist_scenarios:
            raise ValueError(f"Scenario with name: {data['scenario_name']} already exist")

        new_obj = Scenarios(
            scenario_name=data['scenario_name'],
            description=data['description'],
            external_url=data['external_url'],
            requested_by=data['requested_by'],
            edited_by=data['edited_by'],
            tags=json.dumps(data['tags']),
            scenario_type=data['scenario_type'],
            scenario_actions=json.dumps(data['scenario_actions']),
            environment_id=data['environment_id']
        )

        new_obj = new_obj.save()
        return new_obj

    @classmethod
    def get_all_scenarios(cls):
        get_all_scenarios = cls.query.filter_by().all()
        all_scenarios = [single_event.return_all_scenario_dict() for single_event in get_all_scenarios]

        return all_scenarios

    @classmethod
    def obj_exist(cls, scenario_id=None, scenario_name=None):
        if scenario_id:
            return cls.query.filter_by(scenario_id=scenario_id).one_or_none()
        if scenario_name:
            return cls.query.filter_by(scenario_name=scenario_name).one_or_none()

    @classmethod
    def get_scenario_by_name(cls, scenario_id):
        return cls.query.filter_by(scenario_id=scenario_id).one_or_none()

    def save(self):
        try:
            db.session.add(self)
            db.session.flush()
            db.session.commit()

            return self
        except Exception as exc:
            logger.error(
                msg=f"Can't commit changes to DB - {exc}\n{traceback.format_exc()}"
            )
            db.session.rollback()

    def delete_obj(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def search_actions(cls, data):
        scenario_channels = {
            "ui": False,
            "jira": False,
            "email": False,
            "skype": False,
            "teams": False,
            "telegram": False,
            "pagerduty": False,
            "sms": False,
            "voice": False,
            "whatsapp": False,
            "signl4": False,
            "webhook": False,
            "slack": False
        }
        objects = cls.query

        if data['environment_id'] == 'all':
            objects = objects.filter_by()
        else:
            objects = objects.filter_by(environment_id=data['environment_id'])

        for item in objects.all():
            scenario_actions = json.loads(item.scenario_actions)
            for action in scenario_actions:
                if action['type'] in scenario_channels:

                    scenario_channels[action['type']] = True
                else:
                    logger.error(msg=f"Unknown channel identifiers - {action['type']}\nScenario Action - {scenario_actions}\nExpected list: {scenario_channels}")

        return scenario_channels

    @classmethod
    def search(cls, data):
        result = []
        objects = cls.query
        if 'scenario_name' in data:
            objects = objects.filter_by(scenario_name=data['scenario_name'])
        if 'pattern' in data:
            objects = objects.filter(cls.scenario_name.like("%{}%".format(data['pattern'])))
        if 'tags' in data:
            objects = objects.filter(cls.tags.like('%"{}"%'.format(data['tags'])))
        if 'scenario_type' in data != '1':
            objects = objects.filter_by(scenario_type=data['scenario_type'])
        if 'scenario_id' in data:
            objects = objects.filter_by(scenario_id=data['scenario_id'])
        if 'environment_id' in data:
            objects = objects.filter_by(environment_id=data['environment_id'])

        for item in objects.all():
            scenario_channels = {
                "ui": False,
                "jira": False,
                "email": False,
                "skype": False,
                "teams": False,
                "telegram": False,
                "pagerduty": False,
                "sms": False,
                "voice": False,
                "whatsapp": False,
                "signl4": False,
                "webhook": False,
                "slack": False
            }
            scenario_actions = json.loads(item.scenario_actions)
            for action in scenario_actions:
                if action['type'] in scenario_channels:
                    scenario_channels[action['type']] = True
                else:
                    logger.error(msg=f"Unknown channel identifiers - {action['type']}\nScenario Action - {scenario_actions}\nExpected list: {scenario_channels}")

            result.append({
                'scenario_id': item.scenario_id,
                'scenario_name': item.scenario_name,
                'scenario_actions': scenario_actions,
                'scenario_channels': scenario_channels,
                'edited_by': item.edited_by,
                'last_update_ts': str(item.last_update_ts),
            })

        return result


# ###### SCHEMAS #######
class ScenarioSchema(Schema):
    scenario_id = fields.Int(dump_only=True)
    scenario_name = fields.Str(required=True)
    environment_id = fields.Int(dump_only=True)
    description = fields.Str(dump_only=True)
    external_url = fields.Str(dump_only=True)
    requested_by = fields.Str(dump_only=True, required=True)
    tags = fields.List(fields.Str, dump_only=True)
    scenario_type = fields.Int(dump_only=True)
    edited_by = fields.Str(dump_only=True)
    scenario_review_status = fields.Str(dump_only=True)
    scenario_actions = fields.List(fields.Dict(cls_or_instance=fields.List), required=True)
    create_ts = fields.DateTime("%Y-%m-%d %H:%M:%S", dump_only=True)
    last_update_ts = fields.DateTime("%Y-%m-%d %H:%M:%S", dump_only=True)

