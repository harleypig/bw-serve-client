#!/bin/sh
# Register the test account, log the CLI in, and serve with the vault locked.
#
# Needs VW_URL, BW_EMAIL and BW_PASSWORD. The password is a made-up one for
# a throwaway server, but it still goes to bw by environment name only.
# BW_SESSION is never exported, so `bw serve` starts locked and record.py
# can capture the locked-vault failure before it unlocks over HTTP.

set -eu

node /recorder/register.js

bw config server "$VW_URL" > /dev/null

# --raw prints the session key, so it goes nowhere.
bw login "$BW_EMAIL" --passwordenv BW_PASSWORD --raw > /dev/null

exec bw serve --hostname all --port 8087
