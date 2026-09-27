#!/usr/bin/env bash
# community-smoke.sh — confirm a TOKN install can run the free Community tier.
#
# Runs the three domain previews and the offline governed-judgment example.
# No API key, no model provider, no trial. The checks themselves send nothing;
# set TOKN_NO_REGISTER=1 and TOKN_NO_UPDATE_CHECK=1 to silence TOKN's startup
# install-count and update-check too.
# All scratch files go in a temp directory that is removed on exit.

set -uo pipefail

fail=0
step() { printf '\n== %s\n' "$1"; }
ok()   { printf '   ok   %s\n' "$1"; }
bad()  { printf '   FAIL %s\n' "$1"; fail=1; }

step "preflight"
if ! command -v tokn >/dev/null 2>&1; then
  cat >&2 <<'EOF'
   FAIL tokn is not on your PATH.

   This script needs the TOKN binary and nothing else — no API key, no model
   provider, no trial. Install it first:

     1. Download for your OS:  https://github.com/bhakthan/tokn-dist/releases/latest
     2. Verify the signature:  see README.md section 2 (needs openssl 3.x)
     3. Put it on your PATH:   see README.md section 3

   Then re-run this script.
EOF
  exit 1
fi
ok "tokn found: $(command -v tokn)"
tokn --version || bad "tokn --version failed"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cd "$work" || exit 1

step "developer on-ramp"
guide="$(tokn community guide 2>&1)" || bad "community guide (exit)"
if printf '%s' "$guide" | grep -q "DISCOVER" &&
   printf '%s' "$guide" | grep -q "INSPECT" &&
   printf '%s' "$guide" | grep -q "OPT IN"; then
  ok "community guide renders the discover/inspect/opt-in path"
else
  bad "community guide did not render the expected sections"
fi
if [ "$guide" = "$(tokn community 2>&1)" ]; then
  ok "bare 'tokn community' renders the same on-ramp"
else
  bad "bare 'tokn community' and 'tokn community guide' differ"
fi

step "domain previews"
tokn community list >/dev/null 2>&1 && ok "community list" || bad "community list"
for domain in powergrid geospatial batterypass; do
  out="$(tokn community demo --domain "$domain" 2>&1)" || { bad "demo $domain (exit)"; continue; }
  if printf '%s' "$out" | grep -q "Verdict: ACCEPTED" &&
     printf '%s' "$out" | grep -q "Verdict: BLOCKED"; then
    ok "demo $domain (one accepted case, one blocked case)"
  else
    bad "demo $domain did not report both an accepted and a blocked case"
  fi
done

step "unknown preview is rejected"
if tokn community demo --domain not-a-domain >/dev/null 2>&1; then
  bad "an unknown preview name was accepted"
else
  ok "unknown preview rejected"
fi

step "offline governed judgments"
tokn judgments example > bundle.json 2>/dev/null || bad "judgments example"
tokn judgments validate --bundle bundle.json >/dev/null 2>&1 \
  && ok "bundle validates" || bad "bundle validate"

cat > request-clean.json <<'JSON'
{"state":{"status":"completed","answer_present":true,"telemetry_complete":true,
"tool_calls":12,"tool_errors":0,"tool_blocks":0,"steps":7},
"context":{"trace_id":"smoke-clean","environment":"local"}}
JSON
cat > request-errors.json <<'JSON'
{"state":{"status":"completed","answer_present":true,"telemetry_complete":true,
"tool_calls":12,"tool_errors":2,"tool_blocks":1,"steps":7},
"context":{"trace_id":"smoke-errors","environment":"local"}}
JSON

clean="$(tokn judgments evaluate --bundle bundle.json --file request-clean.json \
  --mode advisory --air-gap 2>&1)"
printf '%s' "$clean" | grep -q '"action": "continue"' \
  && ok "clean run judged: continue" || bad "clean run did not judge continue"

errs="$(tokn judgments evaluate --bundle bundle.json --file request-errors.json \
  --mode advisory --air-gap 2>&1)"
printf '%s' "$errs" | grep -q '"action": "revise"' \
  && ok "failing run judged: revise" || bad "failing run did not judge revise"

printf '%s' "$errs" | grep -q '"applied": false' \
  && ok "judgment is advisory (applied: false)" || bad "judgment reported applied: true"

step "result"
if [ "$fail" -eq 0 ]; then
  echo "   All Community-tier checks passed. Next: GETTING_STARTED.md"
else
  echo "   Some checks failed. See the troubleshooting table in GETTING_STARTED.md"
fi
exit "$fail"
