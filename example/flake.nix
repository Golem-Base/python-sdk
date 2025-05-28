{
  inputs = {
    golem-base-sdk.url = "git+file:..";

    devshell = {
      url = "github:numtide/devshell";
      inputs = {
        nixpkgs.follows = "golem-base-sdk/nixpkgs";
      };
    };

    blueprint = {
      url = "github:numtide/blueprint";
      inputs = {
        nixpkgs.follows = "golem-base-sdk/nixpkgs";
      };
    };

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "golem-base-sdk/nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        nixpkgs.follows = "golem-base-sdk/nixpkgs";
      };
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "golem-base-sdk/nixpkgs";
      };
    };
  };

  outputs =
    inputs:
    inputs.blueprint {
      inherit inputs;
      prefix = "nix";
    };
}
