
How to install
==================
The entire guide will be installed under /var/root permissions

warning: $HOME ('/Users/***') is not owned by you, falling back to the one defined in the 'passwd' file ('/var/root')

Prerequisites
------------------
a fresh macOS Sequoia without Nix/Nix-like installed on Mac for Apple silcon chip

Install Lix
------------------
1. Use Lix-installer: `curl --proto '=https' --tlsv1.2 -sSf -L https://install.lix.systems/lix | sh -s -- install`
2. Check Lix version
  ```bash
  $ nix --version
  nix (Lix, like Nix) 2.93.3
  ```

Install Nix-darwin
------------------
1. refer to [nix-darwin](https://github.com/nix-darwin/nix-darwin?tab=readme-ov-file#getting-started) project > Getting started > Channels
2. add `nix-darwin` channel: `sudo nix-channel --add https://github.com/nix-darwin/nix-darwin/archive/master.tar.gz darwin`
3. add `nixpkgs` channel: `sudo nix-channel --add http://nixos.org/channels/nixpkgs-unstable nixpkgs`
4. add `home-manager` channel: `sudo nix-channel --add https://github.com/nix-community/home-manager/archive/master.tar.gz home-manager`
5. update 3 channels: `sudo nix-channel --update`
6. copy `configuration.nix` to `/etc/nix-darwin/configuration.nix`
7. install `nix-darwin`:
  ```bash
  sudo nix-build '<darwin>' -A darwin-rebuild
  sudo ./result/bin/darwin-rebuild switch -I darwin-config=/etc/nix-darwin/configuration.nix
  ```
8. first build `nix-darwin`: `sudo darwin-rebuild switch`.
9. update 3 channels again: `sudo nix-channel --update`

How to Update
==================
```bash
sudo nix-channel --update
sudo darwin-rebuild switch
```

How to Upgrade
==================
1. upgrade lix: `sudo upgrade-nix`
2. modify config with root: `micro /etc/nix-darwin/configuration.nix`
3. rebuild `nix-darwin`: `sudo darwin-rebuild switch`
