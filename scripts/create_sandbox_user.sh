#!/bin/sh
SANDBOX_USER="sandbox-user"
SANDBOX_USER_ID=65537

if ! id "$SANDBOX_USER" &>/dev/null; then
    useradd -u "$SANDBOX_USER_ID" "$SANDBOX_USER"
fi

SANDBOX_GROUP_ID=$(id -g "${SANDBOX_USER}" )
export SANDBOX_USER_ID
export SANDBOX_GROUP_ID
