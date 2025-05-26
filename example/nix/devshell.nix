{ pkgs, perSystem, ... }:

perSystem.devshell.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.anyio
      ps.pyxdg
      perSystem.golem-base-sdk.golem-base-sdk
    ]))
  ];
}
