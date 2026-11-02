def get_application_name():
    return "Cruft Pack Lab"


def get_application_version():
    return "1.1.0"


def get_deployment_environment():
    return "development"


def get_application_details():
    return {
        "name": get_application_name(),
        "version": get_application_version(),
        "environment": get_deployment_environment(),
    }
