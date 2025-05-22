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
  };

  outputs =
    inputs:
    inputs.blueprint {
      inherit inputs;
      prefix = "nix";
    };
}
