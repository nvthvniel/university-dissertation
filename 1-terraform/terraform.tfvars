# ArgoCD Web UI admin password
argocd_admin_password = "..."

# Credentials to read code from GitHub
github_app_private_key = <<EOT
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
EOT

slack_signing_secret = "..."

slack_api_token = "xoxb-..."

chatgpt_api_token = "sk-..."

# readonly key to download container images
dev_project_registry = "{\"auths\":{\"https://index.docker.io/v1/\":{\"username\":\"...\",\"password\":\"dckr_pat_...\",\"email\":\"...\",\"auth\":\"...\"}}}"
