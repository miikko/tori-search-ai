from constructs import Construct
from cdktf_cdktf_provider_azurerm.resource_group import ResourceGroup
from cdktf_cdktf_provider_azurerm.linux_web_app import LinuxWebApp
from cdktf_cdktf_provider_azurerm.service_plan import ServicePlan

def create_web_app(scope: Construct, name_prefix: str, rg: ResourceGroup, env_vars: dict):
    env_vars_copy = env_vars.copy()
    # Azure assumes that container is listening on port 80, so we need to set this explicitly
    env_vars_copy["WEBSITES_PORT"] = "8000"
    service_plan = ServicePlan(
        scope,
        f"{name_prefix}-service-plan",
        location=rg.location,
        name=f"{name_prefix}-service-plan",
        os_type="Linux",
        resource_group_name=rg.name,
        sku_name="F1",
        worker_count=1,
    )
    LinuxWebApp(
        scope,
        f"{name_prefix}-web-app",
        name=f"{name_prefix}-web-app",
        location=rg.location,
        resource_group_name=rg.name,
        service_plan_id=service_plan.id,
        site_config={
            "always_on": False,
            "application_stack": {
                "docker_image_name": f"hovvk/{name_prefix}-web:latest",
                "docker_registry_url": "https://docker.io",
            },
            "ftps_state": "Disabled",
            "http2_enabled": True,
            "remote_debugging_enabled": False,
            "use32_bit_worker": True, # 64 bit workers are not supported in Free tier
            "websockets_enabled": False,
        },
        app_settings=env_vars_copy,
        # Check this link for more info about client affinity
        # https://azure.github.io/AppService/2016/05/16/Disable-Session-affinity-cookie-(ARR-cookie)-for-Azure-web-apps.html
        # (spoiler: this setting doesn't really matter with just 1 worker)
        client_affinity_enabled=True,
        client_certificate_enabled=False,
        https_only=True,
        public_network_access_enabled=True,
    )

