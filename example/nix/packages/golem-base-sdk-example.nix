{
  pkgs,
  pname,
  perSystem,
  ...
}:

let
  inherit (pkgs) lib;

  types-pyxdg =
    let
      pname = "types-pyxdg";
      version = "0.28.0.20240106";
    in
    pkgs.python3Packages.buildPythonPackage {
      inherit pname version;
      format = "pyproject";

      src = pkgs.fetchPypi {
        inherit pname version;
        hash = "sha256-UF/GOG2MCl0KkUzrK3bo4tvQsRAhK1s5Xb6xyUg+24g=";
      };

      nativeBuildInputs = [ pkgs.python3Packages.setuptools ];
    };

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
        "golem_base_sdk_example"
        "README.md"
      ]
    );
  };

  nativeBuildInputs = [
    pkgs.python3Packages.flit-core
  ];

  buildInputs = [
    types-pyxdg
  ];

  propagatedBuildInputs = [
    pkgs.python3Packages.pyxdg
    perSystem.golem-base-sdk.golem-base-sdk
  ];

  nativeCheckInputs = [
    pkgs.mypy
    pkgs.pylint
    pkgs.ruff
  ];

  checkPhase = ''
    mypy ${src}/golem_base_sdk_example
    ruff check --no-cache ${src}/golem_base_sdk_example
    PYLINTHOME="$TMPDIR" pylint ${src}/golem_base_sdk_example
  '';

  meta = with lib; {
    homepage = "";
    description = "";
    license = licenses.gpl3Only;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
