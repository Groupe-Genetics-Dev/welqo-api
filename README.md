# Welqo Project

## Environment Variable

To run this app you need to define theses env var beafore reunning docker compose file :

```shell

export POSTGRES_USER="welqo_user"
export POSTGRES_PASSWORD="your_secure_password_here"
export POSTGRES_DATABASE="welqo_db"
export SECRET_KEY="your_jwt_secret_key_min_32_characters_long"
export ALGORITHM="HS256"
export CORS_ORIGIN="http://localhost"

```