{
  pkgs,
  inputs,
  perSystem,
  ...
}:

let
  inherit (pkgs) lib;

  src = lib.fileset.toSource {
    root = ../..;
    fileset = lib.fileset.unions (
      map (lib.path.append ../..) [
        "uv.lock"
        "pyproject.toml"
        "golem_base_sdk_example"
      ]
    );
  };

  workspace = inputs.uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = src;
  };

  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };

  pyprojectOverrides = final: prev: {
    golem-base-sdk = prev.golem-base-sdk.overrideAttrs (prevAttrs: {
      # TODO: this was in the doc but doesn't seem needed?
      #buildInputs =
      #  (prevAttrs.buildInputs or [ ]) ++ perSystem.golem-base-sdk.golem-base-sdk.dist.buildInputs;
      src = perSystem.golem-base-sdk.golem-base-sdk.dist;
    });
  };

  pythonSet =
    (pkgs.callPackage inputs.pyproject-nix.build.packages {
      python = pkgs.python312;
    }).overrideScope
      (
        lib.composeManyExtensions [
          inputs.pyproject-build-systems.overlays.default
          overlay
          pyprojectOverrides
        ]
      );

  inherit (pkgs.callPackages inputs.pyproject-nix.build.util { }) mkApplication;
in

mkApplication {
  venv = pythonSet.mkVirtualEnv "application-env" workspace.deps.default;
  package = pythonSet.golem-base-sdk-example.overrideAttrs {
    nativeCheckInputs = [
      pkgs.mypy
      pkgs.ruff
    ];

    doCheck = true;

    checkPhase = ''
      mypy golem_base_sdk_example
      ruff check --no-cache golem_base_sdk_example
    '';
  };
}
