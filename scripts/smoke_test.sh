#!/usr/bin/env bash
# Smoke test: start docker-compose stack and verify all /health endpoints return 200
set -euo pipefail

echo "Starting stack..."
docker compose up -d

echo "Waiting for services to be healthy (up to 120s)..."
TIMEOUT=120
ELAPSED=0
SERVICES=(
  "http://localhost:8001/health"
  "http://localhost:8002/health"
  "http://localhost:8003/health"
  "http://localhost:8004/health"
  "http://localhost:8005/health"
)

for URL in "${SERVICES[@]}"; do
  echo -n "Waiting for $URL..."
  until curl -sf "$URL" > /dev/null 2>&1; do
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    if [ $ELAPSED -ge $TIMEOUT ]; then
      echo " TIMEOUT"
      docker compose logs
      docker compose down
      exit 1
    fi
    echo -n "."
  done
  echo " OK"
done

echo ""
echo "All health checks passed!"
echo ""

# Verify each endpoint returns expected status
for URL in "${SERVICES[@]}"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
  if [ "$STATUS" != "200" ]; then
    echo "FAIL: $URL returned $STATUS"
    docker compose down
    exit 1
  fi
  echo "PASS: $URL -> $STATUS"
done

echo ""
echo "Smoke tests passed!"
docker compose down
