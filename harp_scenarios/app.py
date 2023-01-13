from microservice_template_core import Core
from microservice_template_core.settings import ServiceConfig, FlaskConfig, DbConfig
from harp_scenarios.endpoints.scenarios import ns as scenarios
from harp_scenarios.endpoints.health import ns as health


def main():
    ServiceConfig.configuration['namespaces'] = [scenarios, health]
    FlaskConfig.FLASK_DEBUG = False
    DbConfig.USE_DB = True
    app = Core()
    app.run()


if __name__ == '__main__':
    main()

