#!/bin/bash

copy_and_link() {
    local src="$1"
    local dst="$2"
    
    if [ ! -e "$src" ]; then
        echo "source file not exists $src"
        exit 1
    fi
    
    local file_mode
    file_mode=$(stat -c "%a" "$src")
    
    if [ -L "$src" ]; then
        cp -P "$src" "$dst"
    elif [ -b "$src" ] || [ -c "$src" ]; then
        cp -P "$src" "$dst"
        chmod 444 "$dst"
    else
        if ln "$src" "$dst" 2>/dev/null; then
            true
        else
            cp -P "$src" "$dst"
            chmod 444 "$dst"
        fi
    fi
}

process_dir() {
    local src="$1"
    local dst="$2"
    
    src=$(realpath "$src")
    dst=$(realpath "$dst")
    
    if [ ! -e "$src" ]; then
        echo "source file not exists $src"
        exit 1
    fi
    
    if [ -f "$src" ]; then
        local dest_file
        dest_file="$dst/$(basename "$src")"
        mkdir -p "$(dirname "$dest_file")"
        copy_and_link "$src" "$dest_file"
    elif [ -d "$src" ]; then
        local dest_dir
        dest_dir="$dst/$(basename "$src")"
        mkdir -p "$(dirname "$dest_dir")"
        
        while IFS= read -r -d '' file; do
            local src_file="$file"
            local rel_path="${src_file#$src}"
            rel_path="${rel_path#/}"
            local dest_file="$dest_dir/$rel_path"
            mkdir -p "$(dirname "$dest_file")"
            copy_and_link "$src_file" "$dest_file"
        done < <(find "$src" -type f -print0)
    else
        echo "$src is neither a file nor a dir"
        exit 1
    fi
}

main() {
    local TARGETARCH="${TARGET_ARCH:-}"
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