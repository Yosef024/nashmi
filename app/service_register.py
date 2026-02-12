services_registry = []

def register_service(service_info: dict):
    services_registry.append(service_info)

def get_services():
    return services_registry
