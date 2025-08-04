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
    zsh
    allure
  ];
  shellHook = # sh
    ''
      # 设置zsh作为默认shell
      export SHELL="${pkgs.zsh}/bin/zsh"

      echo "bootstraping uv-managed virtualenv ..."
      if [ ! -d "${venvDir}" ]; then
        uv venv "${venvDir}"
      fi

      source "${venvDir}/bin/activate"
      echo "sync uv dependencies"
      uv sync --dev
      uv sync
      echo "virtualenv activate at ${venvDir}"
      exec zsh
    '';
}
