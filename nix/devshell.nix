{ pkgs, perSystem, ... }:

perSystem.devshell.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.python-lsp-server
      ps.pylsp-mypy
      ps.mypy

      ps.web3
      ps.rlp

      # Tools for building and uploading wheels
      ps.build
      ps.twine
      ps.pdoc
    ]))
  ];
}
