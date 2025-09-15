#!/bin/bash
SECRETS=("session" "supabase" "isda" "gee")
PREFIX="regen_organics_analytics_app/env"

for s in "${SECRETS[@]}"; do
    # Fetch secret JSON
    secret_json=$(aws secretsmanager get-secret-value \
        --secret-id "$PREFIX/$s" \
        --query SecretString \
        --output text)

    # Convert JSON keys into env vars
    eval $(echo "$secret_json" | jq -r 'to_entries | map("export \(.key)=\(.value|@sh)") | .[]')
done