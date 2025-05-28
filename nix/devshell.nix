{
  pkgs,
  perSystem,
  inputs,
  ...
}:

let
  inherit (pkgs) lib;

  workspace = inputs.uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./..; };

  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel"; # or sourcePreference = "sdist";
  };

  pythonSet =
    (pkgs.callPackage inputs.pyproject-nix.build.packages {
      python = pkgs.python312;
    }).overrideScope
      (
        lib.composeManyExtensions [
          inputs.pyproject-build-systems.overlays.default
          overlay
        ]
      );

  virtualenv = pythonSet.mkVirtualEnv "python-sdk-dev-env" workspace.deps.all;
in

perSystem.devshell.mkShell {
  packages = [
    virtualenv
    pkgs.uv
  ];

  env = [
    {
      # Don't create venv using uv
      name = "UV_NO_SYNC";
      value = "1";
    }
    {
      # Force uv to use Python interpreter from venv
      name = "UV_PYTHON";
      value = "${virtualenv}/bin/python";
    }
    {
      # Prevent uv from downloading managed Python's
      name = "UV_PYTHON_DOWNLOADS";
      value = "never";
    }
  ];

  devshell.startup.uv2nix.text =
    # bash
    ''
      # Undo dependency propagation by nixpkgs.
      unset PYTHONPATH
      # Get repository root using git. This is expanded at runtime by the editable `.pth` machinery.
      export REPO_ROOT=$(git rev-parse --show-toplevel)
    '';
}
