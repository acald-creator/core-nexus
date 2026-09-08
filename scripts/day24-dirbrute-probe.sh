#!/bin/sh
# Mounted into day24-dirbrute-probe Job. Env: BASE, SCENARIO, SCENARIO_ID, RUN_ID
# Mirrors athena-agents dir_bruteforce defaults (UA + Athena labels + lab paths).
set -eu

UA="athena-agents/dir-bruteforce"
WORDS="admin api assets backup config console ftp hidden login metrics rest robots.txt sitemap.xml vendor upload uploads swagger graphql health status .git .env wp-admin"

ah() {
  path="$1"
  code="$(curl -sS -o /tmp/body -w "%{http_code}" \
    -H "X-Athena-Scenario: ${SCENARIO}" \
    -H "X-Athena-Scenario-Id: ${SCENARIO_ID}" \
    -H "X-Athena-Run-ID: ${RUN_ID}" \
    -H "User-Agent: ${UA}" \
    "${BASE}${path}" || true)"
  echo "${path}:${code}"
}

echo "BASE=${BASE}"
echo "UA=${UA}"
for w in $WORDS; do
  ah "/${w}"
done
sleep 2
echo done
