{
  description = "A Nix-flake-based python development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";
  };

  outputs =
    { self, nixpkgs, ... }:
    let
      # system should match the system you are running on
      system = "x86_64-linux";
      # system = "x86_64-darwin";
    in
    {
      devShells."${system}".default =
        let
          pkgs = import nixpkgs {
            inherit system;
          };
        in
        pkgs.mkShell {
          # create an environment with nodejs-18_x, pnpm, and yarn
          packages = with pkgs; [
            uv
          ];

          shellHook = ''
            echo "node `node --version`"
          '';
        };
    };
}
