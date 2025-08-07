#!/bin/bash

set -e

copy_and_link() {
    local src="$1"
    local dst="$2"

    if [ ! -e "$src" ]; then
        echo "source file not exists $src"
        exit 1
    fi

    local file_mode
    file_mode=$(stat -c "%F" "$src")

    case "$file_mode" in
        "symbolic link")
            cp -P "$src" "$dst"
            ;;
        "block special file"|"character special file")
            cp -P "$src" "$dst"
            chmod 444 "$dst"
            ;;
        *)
            if ln "$src" "$dst" 2>/dev/null; then
                :
            else
                cp -P "$src" "$dst"
                chmod 444 "$dst"
            fi
            ;;
    esac
}

process_dir() {
    local src="$1"
    local dst="$2"

    src=$(realpath -m "$src")
    dst=$(realpath -m "$dst")

    if [ ! -e "$src" ]; then
        echo "source file not exists $src"
        exit 1
    fi

    if [ -f "$src" ]; then
        mkdir -p "$(dirname "$dst/$src")"
        copy_and_link "$src" "$dst/$src"
    elif [ -d "$src" ]; then
        mkdir -p "$(dirname "$dst/$src")"

        find "$src" -type f l | while read -r src_file; do
            local rel_path
            rel_path="${src_file#$src/}"
            local dest_file
            rel_dir=$(dirname "$rel_path")
            mkdir -p "$dst/$src/$rel_dir"
            copy_and_link "$src_file" "$dst/$src/$rel_path"
        done
    else
        echo "$src is neither a file nor a dir"
        exit 1
    fi
}

main() {
    local TARGETARCH="${TARGETARCH:-}"
    local python_lib=("/usr/local/lib/python3.11")

    if [ "$TARGETARCH" = "amd64" ] || [ -z "$TARGETARCH" ]; then
        python_lib+=("/usr/lib/x86_64-linux-gnu")
    else
        python_lib+=("/usr/lib/aarch64-linux-gnu")
    fi

    local network_lib=(
        "/etc/ssl/certs/ca-certificates.crt"
        "/etc/nsswitch.conf"
        "/etc/resolv.conf"
        "/etc/hosts"
    )

    for lib in "${python_lib[@]}"; do
        process_dir "$lib" "/var/sandbox/python"
    done

    for lib in "${network_lib[@]}"; do
        process_dir "$lib" "/var/sandbox/python"
        process_dir "$lib" "/var/sandbox/nodejs"
    done

    local python_so="/app/build/lib/libseccomp_injector_python.so"
    local nodejs_so="/app/build/lib/libseccomp_injector_nodejs.so"

    process_dir "$python_so" "/var/sandbox/python"
    process_dir "$nodejs_so" "/var/sandbox/nodejs"

    echo "complete copy all lib to /var/sandbox"
}

main "$@"
