{
  pkgs,
  pname,
  ...
}:

let
  inherit (pkgs) lib;
in

pkgs.python3Packages.buildPythonPackage rec {
  inherit pname;
  version = "0.0.1";

  format = "pyproject";

  src = lib.fileset.toSource {
    root = ../..;
    fileset = lib.fileset.unions (
      map (lib.path.append ../..) [
        "pyproject.toml"
        "golem_base_sdk"
        "LICENSE"
        "README.md"
      ]
    );
  };

  nativeBuildInputs = [
    pkgs.python3Packages.flit-core
  ];

  buildInputs = [
    pkgs.python3Packages.pyunormalize
  ];

  propagatedBuildInputs = [
    pkgs.python3Packages.web3
    pkgs.python3Packages.rlp
  ];

  nativeCheckInputs = [
    pkgs.mypy
    pkgs.pylint
    pkgs.ruff
  ];

  checkPhase = ''
    cat <<EOF >./mypy.conf
      [mypy]

      [mypy-rlp.*]
      follow_untyped_imports = True
    EOF
    mypy --check-untyped-defs --config-file ./mypy.conf ${src}/golem_base_sdk
    ruff check --no-cache ${src}/golem_base_sdk
    PYLINTHOME="$TMPDIR" pylint ${src}/golem_base_sdk
  '';

  meta = with lib; {
    homepage = "";
    description = "";
    license = licenses.gpl3Only;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
