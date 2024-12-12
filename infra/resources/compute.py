from constructs import Construct
from cdktf_cdktf_provider_azurerm.container_app_environment import ContainerAppEnvironment
from cdktf_cdktf_provider_azurerm.container_app_job import ContainerAppJob
from cdktf_cdktf_provider_azurerm.resource_group import ResourceGroup

def create_compute(scope: Construct, name_prefix: str, rg: ResourceGroup, env_vars: dict):
    container_app_environment = ContainerAppEnvironment(
        scope,
        f"{name_prefix}-container-app-environment",
        resource_group_name=rg.name,
        location=rg.location,
        name=f"{name_prefix}-container-app-environment",
        workload_profile=[{
            "name": "Consumption",
            "workloadProfileType": "Consumption" # Likely a bug in the cdktf Python mapping that this key needs to be camel case instead of snake case
        }]
    )
    env = [ { "name": key, "value": value } for key, value in env_vars.items() ]
    job_configs = [
        {
            "name": "scraper-job",
            # Every hour
            "cron_expression": "0 * * * *",
            "timeout_seconds": 300
        },
        {
            "name": "updater-job",
            # Every day at 12:30 AM UTC
            "cron_expression": "30 0 * * *",
            "timeout_seconds": 1000
        },
        {
            "name": "processor-job",
            # Every hour
            "cron_expression": "10 * * * *",
            "timeout_seconds": 600
        }
    ]
    for job_config in job_configs:
        ContainerAppJob(
            scope,
            f"{name_prefix}-{job_config['name']}",
            resource_group_name=rg.name,
            location=rg.location,
            name=f"{name_prefix}-{job_config['name']}",
            container_app_environment_id=container_app_environment.id,
            template={
                "container": [{
                    "name": f"{name_prefix}-{job_config['name']}",
                    "cpu": 0.25,
                    "memory": "0.5Gi",
                    "image": f"hovvk/{name_prefix}-{job_config['name']}:latest",
                    "env": env
                }],
            },
            replica_timeout_in_seconds=job_config["timeout_seconds"],
            workload_profile_name="Consumption",
            replica_retry_limit=0,
            schedule_trigger_config={
                "cron_expression": job_config["cron_expression"],
                "parallelism": 1,
                "replica_completion_count": 1
            }
        )