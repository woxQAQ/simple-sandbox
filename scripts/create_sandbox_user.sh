#!/bin/sh
set -o errexit
set -o pipefail
set -o nounset
SANDBOX_USER="sandbox-user"
SANDBOX_USER_ID=65537
SANDBOX_GROUP_ID=0

if ! id "$SANDBOX_USER" &>/dev/null; then
    useradd -u "$SANDBOX_USER_ID" "$SANDBOX_USER"
fi

SANDBOX_GROUP_ID=${id -g "${SANDBOX_USER}"}
export SANDBOX_USER_ID
export SANDBOX_GROUP_ID
