{
  pkgs ? import <nixpkgs> { },
}:
let
  venvDir = "./.venv";
in
pkgs.mkShell {
  name = "uv-dev";
  buildInputs = with pkgs; [
    uv
    python311
  ];
  shellHook = # sh
    ''
      echo "bootstraping uv-managed virtualenv ..."
      if [ ! -d "${venvDir}" ]; then
        uv venv "${venvDir}"
      fi

      source "${venvDir}/bin/activate"
      echo "virtualenv activate at ${venvDir}"
    '';
}
