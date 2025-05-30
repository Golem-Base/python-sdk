{
  pkgs,
  inputs,
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
        "golem_base_sdk"
        "LICENSE"
        "README.md"
      ]
    );
  };

  # Load a uv workspace from a workspace root.
  # Uv2nix treats all uv projects as workspace projects.
  workspace = inputs.uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = src;
  };

  # Create package overlay from workspace.
  overlay = workspace.mkPyprojectOverlay {
    # Prefer prebuilt binary wheels as a package source.
    sourcePreference = "wheel";
  };

  # Construct package set
  pythonSet =
    # Use base package set from pyproject.nix builders
    (pkgs.callPackage inputs.pyproject-nix.build.packages {
      # Use Python 3.12 from nixpkgs
      python = pkgs.python312;
    }).overrideScope
      (
        lib.composeManyExtensions [
          inputs.pyproject-build-systems.overlays.default
          overlay
        ]
      );

  virtualenv = pythonSet.mkVirtualEnv "golem-base-sdk-env" workspace.deps.default;
  virtualenvDev = pythonSet.mkVirtualEnv "golem-base-sdk-env" workspace.deps.all;

  self = pythonSet.golem-base-sdk.overrideAttrs (prevAttrs: {
    nativeCheckInputs = [
      pkgs.mypy
      pkgs.ruff
    ];

    doCheck = true;

    checkPhase = ''
      mypy golem_base_sdk
      ruff check --no-cache golem_base_sdk
    '';

    passthru =
      let
        wheel = self.override {
          pyprojectHook = pythonSet.pyprojectDistHook;
        };

        sdist =
          (self.override {
            pyprojectHook = pythonSet.pyprojectDistHook;
          }).overrideAttrs
            (old: {
              env.uvBuildType = "sdist";
            });
      in
      (prevAttrs.passthru or { })
      // {
        dist = pkgs.symlinkJoin {
          name = "golem-base-sdk";
          paths = [
            wheel
            sdist
          ];
        };

        inherit virtualenv virtualenvDev;
      };
  });

in
self
