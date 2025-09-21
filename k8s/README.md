Kubernetes notes:
- The manifests are starter templates. They run a python image and attempt to run uvicorn with a module name like '<service>_service.app'.
- Before applying, build proper images for each service and update `spec.template.spec.containers[].image` and `command`.
- Example build/push and kubectl apply steps are provided in the GitLab CI template.
