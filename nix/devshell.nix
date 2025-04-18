{ pkgs, perSystem, ... }:

perSystem.devshell.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.web3
      ps.rlp

      # Tools for building and uploading wheels
      ps.build
      ps.twine
    ]))
  ];
}
