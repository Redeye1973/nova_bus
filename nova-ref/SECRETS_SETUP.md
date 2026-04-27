# SECRETS_SETUP

## Doel
Zorg dat secrets buiten de repo staan en consistent geladen worden.

## Locaties
- Secrets directory: `C:/nova/secrets/`
- Nova ref env file: `C:/nova/secrets/nova-ref.env`
- Nova learn env file: `C:/nova/secrets/nova-learn.env`

## Minimale inhoud
Voor `nova-ref.env`:
- `NOVA_REF_DB_HOST`
- `NOVA_REF_DB_PORT`
- `NOVA_REF_DB_NAME`
- `NOVA_REF_DB_USER`
- `NOVA_REF_DB_PASS`
- `REDIS_URL`
- `REDIS_PASSWORD`

Voor `nova-learn.env`:
- `NOVA_REF_DB_HOST`
- `NOVA_REF_DB_PORT`
- `NOVA_REF_DB_NAME`
- `NOVA_REF_DB_USER`
- `NOVA_REF_DB_PASS`
- `REDIS_URL`
- `REDIS_PASSWORD`

## Compose koppeling
`infrastructure/docker-compose.nova-reference.yml` laadt:
- `C:/nova/secrets/nova-ref.env`
- `C:/nova/secrets/nova-learn.env`

## Veiligheidsregels
- Commit nooit `.env` files.
- Commit alleen `.env.example` met dummy values.
- Houd permissies op `C:/nova/secrets/` beperkt tot de eigen gebruiker.

