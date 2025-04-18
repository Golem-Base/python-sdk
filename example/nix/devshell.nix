{ pkgs, perSystem, ... }:

perSystem.devshell.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.web3
      ps.rlp
      ps.pyxdg
    ]))
  ];
}
