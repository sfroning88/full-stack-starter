#!/bin/sh
sed 's/\x1b\[[0-9;]*m//g' "$1" \
  | grep -v "^react-doctor v" \
  | grep -v "No feature branch or uncommitted changes detected" \
  | grep -v "^Scanning /" \
  | grep -v "Full diagnostics written to /tmp/" \
  | grep -v "Share your results:" \
  | sed 's/^[[:space:]]*//' \
  | cat -s
  