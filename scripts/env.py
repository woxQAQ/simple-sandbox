#!/usr/local/bin python3
import os
import shutil
import stat


def copy_and_link(src: str, dst: str):
    file_stat = os.stat(src)
    file_mode = file_stat.st_mode
    if stat.S_ISLNK(file_mode):
        shutil.copy2(src=src, dst=dst, follow_symlinks=False)
    elif stat.S_ISBLK(file_mode) or stat.S_ISCHR(file_mode):
        shutil.copy2(src=src, dst=dst)
        os.chmod(dst, 0o444)
    else:
        try:
            os.link(src=src, dst=dst)
        except OSError:
            shutil.copy2(src=src, dst=dst)
            os.chmod(dst, 0o444)


def process_dir(src: str, dst: str):
    src = os.path.normpath(src)
    dst = os.path.normpath(dst)
    if not os.path.exists(src):
        print(f"source file not exists {src}")
        exit(1)

    if os.path.isfile(src):
        dest_file = os.path.join(dst, os.path.basename(src))
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        copy_and_link(src, dest_file)
    elif os.path.isdir(src):
        dest_dir = os.path.join(dst, os.path.basename(src))
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

        for root, dirs, files in os.walk(src):
            rel_path = os.path.relpath(root, src)
            if rel_path == ".":
                rel_path = ""
            dest_root = os.path.join(dest_dir, rel_path)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_root, file)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                copy_and_link(src_file, dest_file)
    else:
        print(f"{src} is neither a file nor a dir")
        exit(1)


def main():
    TARGETARCH = os.getenv("TARGET_ARCH")
    python_lib = [
        "/usr/local/lib/python3.11",
    ]
    if TARGETARCH == "amd64" or TARGETARCH == "":
        python_lib.append("/usr/lib/x86_64-linux-gnu")
    else:
        python_lib.append("/usr/lib/aarch64-linux-gnu")

    network_lib = [
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/nsswitch.conf",
        "/etc/resolv.conf",
        "/etc/hosts",
    ]

    for lib in python_lib:
        process_dir(lib, "/var/sandbox/python")

    for lib in network_lib:
        process_dir(lib, "/var/sandbox/python")
        process_dir(lib, "/var/sandbox/nodejs")

    python_so = "/app/build/lib/libseccomp_injector_python.so"
    nodejs_so = "/app/build/lib/libseccomp_injector_nodejs.so"
    process_dir(python_so, "/var/sandbox/python")
    process_dir(nodejs_so, "/var/sandbox/nodejs")

    print("complete copy all lib to /var/sandbox")


if __name__ == "__main__":
    main()
