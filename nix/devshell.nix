{ pkgs, perSystem, ... }:

perSystem.devshell.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.web3
      ps.rlp
      ps.pyxdg

      # Tools for building and uploading wheels
      ps.build
      ps.twine
    ]))
  ];
}
