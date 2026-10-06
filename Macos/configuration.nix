{ config, pkgs, ... }:

{
  nixpkgs.overlays = [
    (final: prev: {
      unity-test = prev.unity-test.overrideAttrs (oldAttrs: {
        doCheck = false;
        NIX_CFLAGS_COMPILE = (oldAttrs.NIX_CFLAGS_COMPILE or "") 
          + " -Wno-error=implicit-void-ptr-cast -Wno-error=implicit-function-declaration";
      });
      python313 = prev.python313.override {
        packageOverrides = pyFinal: pyPrev: {
          agate = pyPrev.agate.overridePythonAttrs (oldAttrs: {
            doCheck = false;
          });
        };
      };
    })
  ];
  system = {

    primaryUser = "bemly";
    # Used for backwards compatibility, please read the changelog before changing.
    # $ darwin-rebuild changelog
    stateVersion = 6;

    activationScripts = {
      # it's magic not-post function. LMAO
      # source: https://github.com/nix-darwin/nix-darwin/issues/333
      # postActivation.text = ''
      #   ${pkgs.skhd} -r
      # '';

      # only run once. install rosetta 2. (brew install after)
      # extraActivation.text = ''
      #   sudo softwareupdate --install-rosetta --agree-to-license
      # '';
    };

    defaults = {
      spaces.spans-displays = false;

      dock = {
        magnification = true;
        mru-spaces = false;
        autohide = true;
      };

      finder = {
        AppleShowAllExtensions = true;
        AppleShowAllFiles = true;
        CreateDesktop = false;
        QuitMenuItem = true;
      };

      NSGlobalDomain = {
        # auto hide mac original menu bar
        # you maybe need switch to Always option mannully
        #   in System Settings>Control Center>Auto hide&appear menu bar.
        _HIHideMenuBar = true;
        AppleKeyboardUIMode = 3;
        AppleShowAllExtensions = true;
        ApplePressAndHoldEnabled = true;
        InitialKeyRepeat = 10;
        NSAutomaticCapitalizationEnabled = false;
        NSAutomaticDashSubstitutionEnabled = false;
        NSAutomaticQuoteSubstitutionEnabled = false;
        NSAutomaticSpellingCorrectionEnabled = false;
        NSNavPanelExpandedStateForSaveMode = true;
        NSNavPanelExpandedStateForSaveMode2 = true;
        KeyRepeat = 1;
        AppleShowAllFiles = true;
        NSWindowResizeTime = 0.0;
      };
    };
  };

  fonts = {
    packages = with pkgs; [
      nerd-fonts.jetbrains-mono nerd-fonts.hack 
      sketchybar-app-font minecraftia monocraft 
    ];
  };

  # List packages installed in system profile. To search by name, run:
  # $ nix-env -qaP | grep wget
  nixpkgs.config.allowUnfree = true;
  
  environment.systemPackages = 
    let
      jetbrains = with pkgs.jetbrains; [
        clion goland rider ruby-mine rust-rover webstorm phpstorm mps gateway dataspell datagrip 
        pycharm idea
      ];
      editors = with pkgs; [
        micro obsidian navi helix sphinx ov direnv nix-direnv mkdocs khal pandoc
        imhex hexyl upx bed delta epr jadx cfr buku tokei scc gcalcli pueue #zed-editor
        vim neovim vimPlugins.yazi-nvim vimPlugins.nnn-vim jetbrains-toolbox
        vscode vscode-extensions.jnoortheen.nix-ide vscode-extensions.mkhl.direnv
      ];
      # modrinth-app not build
      minecraft = with pkgs; [
        hmcl packwiz ferium glfw3-minecraft gopacked 
        optifine bluemap regolith prismlauncher minutor jmc2obj lazymc 
        mchprs  mcstatus mcrcon mcdreforged gate fabric-installer
      ];
      version_control = with pkgs; [
        git git-lfs tea glab goreleaser soft-serve act bit gitleaks
        gh gh-i gh-f gh-gei gh-eco gh-dash gh-classroom gh-markdown-preview 
        gitui lazygit tig jj git-chglog pre-commit gitea dvc
      ];
      # pyinfra 4.2.7>= paramiko fastly not build by cargo
      cloud_tools = with pkgs; [
        cloudflared oci-cli rclone cloudlist aliyun-cli ibmcloud-cli scaleway-cli vultr-cli 
        opentofu terraform usacloud ansible yandex-cloud 
        azure-cli awscli2 flarectl heroku drive linode-cli 
        baidupcs-go
      ];
      # diffoscope => fuse-3 not support darwin
      disk_tools = with pkgs; [
        duf dust ncdu godu gdu duff dua smartmontools carapace carapace-bridge  
        zoxide  trash-cli chezmoi pdisk smartmontools create-dmg dmg2img
      ];
      network_tools = with pkgs; [
        iproute2mac ifstat-legacy ipmitool iperf3 wireguard-tools atool rsync wget speedtest-cli ddgr 
        gping nali trippy aria2 curlie gost mosquitto termshark xh termshark brook certbot httpx hurl 
        socat websocat doggo magic-wormhole benthos ipatool chisel tproxy grpcurl miniserve httpie croc
      ];
      ai_tools = with pkgs; [ chatblade chatgpt llm litellm ];
      # gimp3 not support darwin on 25.11
      media_tools = with pkgs; [ gimp2 exiftool flameshot vlc-bin mpv ffmpeg-full ];
      security_tools = with pkgs; [ nmap trivy grype dnstwist tfsec scorecard gopass lynis skate cfssl horcrux easyrsa rustscan ];
      analysis_tools = with pkgs; [ oha hey vegeta ffuf hyperfine ];
      proxy_tools = with pkgs; [ mihomo clash-rs metacubexd zashboard frp ];
      other_tools = with pkgs; [ coreutils gnugrep gnused gawk mtr gnupg kopia pywal sd asciigraph hadolint ];
      file_manager = with pkgs; [ nnn yazi fzf skim peco yaziPlugins.rsync yaziPlugins.git yaziPlugins.sudo ];
      language_zig_c_rust = with pkgs; [ vcpkg conan zig minizign arocc rustup rustc libuv zls ];
      #  python-qt qt-engine => CVE, python3Full is not existed maintainer(unstable)
      language_lua_python = with pkgs; [ luajit luajitPackages.luarocks python312 just ruff yapf pipx pylint uv rye ];
      language_js_wasm = with pkgs; [ nodenv deno bun typescript pm2 rhino wasmtime wasmer wasmedge wasm-tools zola hugo caddy ];
      language_go_php_fp = with pkgs; [ go php scala ocaml perl rakudo zef ];
      language_apple_ms = with pkgs; [ apple-sdk_15 swift jazzy catch2 darwin.top dotnet-sdk ];
      language_java_sdkman = with pkgs; [ flink gradle activemq ant groovy hadoop maven kotlin ];
      language_mqtt = with pkgs; [ qmqtt mqtt_cpp mqttui nanomq zigbee2mqtt ];
      language_csv = with pkgs; [ csview trdsql miller csvkit ];
      language_sql = with pkgs; [ litecli  sqlfluff lazysql usql sqlite sqlite-rsync mariadb postgresql influxdb2-cli mongodb-compass ];
      language_json_yaml = with pkgs; [ jq yq gojq jqp jless fx jc dasel gron dyff ytt ];
      compression_tools = with pkgs; [ p7zip unrar zstd ouch ];
      markdowns = with pkgs; [ mystmd mdtsql glow comrak xlsxsql ];
      containers = with pkgs; [ podman podman-tui podman-compose docker docker-compose lazydocker dry syft lima dive qemu utm ];
      k8s = with pkgs; [ minikube kubectx kube-score kind kube-capacity k3d k9s kube-linter ];
      cmd_shell = with pkgs; [ fish screen zellij gum starship murex nushell xonsh elvish shfmt powerline-go powershell zx sqsh ];
      cmd_terminal = with pkgs; [ kitty alacritty wezterm iterm2 warp-terminal tmux tmuxp ];
	  # thefuck not support py13, use pay-respects instead
      cmd_enhance = with pkgs; [ lsd pay-respects wtfutil bat qrencode grex joker mawk ];
      ssh_vnc = with pkgs; [ mosh assh passh sshpass xxh ssh-audit sesh ttyd gotty moonlight-qt scrcpy ];
      monitors = with pkgs; [ htop btop gotop procs zenith bottom-rs viddy sampler ctop mactop macchina watch macpm ];
      fetch_info = with pkgs; [ neofetch fastfetch pfetch-rs ipfetch cpufetch onefetch macchina ];
      window_manager = with pkgs; [ yabai skhd sketchybar autojump ranger switchaudio-osx cava blueutil ];
	  # arc-browser only 25.05, left out maintainer(unstable) browsers litebrowser chawan ladybird
      browsers = with pkgs; [ firefox  google-chrome ];
      # _64gram not support darwin now
      sms = with pkgs; [ discord paper-plane materialgram ayugram-desktop tg ];
      games = with pkgs; [ osu-lazer-bin ];
      toys = with pkgs; [ biliup-rs sl emojify emoji-picker invoice genact shtris etcd ];
    in
      jetbrains ++ editors ++ minecraft ++ version_control ++ cloud_tools ++ disk_tools ++ network_tools
        ++ ai_tools ++ media_tools ++ security_tools ++ analysis_tools ++ proxy_tools ++ other_tools ++ file_manager
        ++ language_zig_c_rust ++ language_lua_python ++ language_js_wasm ++ language_go_php_fp 
        ++ language_apple_ms ++ language_java_sdkman ++ language_mqtt ++ language_csv ++ language_sql ++ language_json_yaml 
        ++ compression_tools ++ markdowns ++ containers ++ k8s ++ cmd_shell ++ cmd_terminal ++ cmd_enhance 
        ++ ssh_vnc ++ monitors ++ browsers ++ sms ++ games ++ toys ++ window_manager ++ fetch_info;

  # HOMEBREW, i like this software ffi binding :)
  homebrew = {
    enable = true;
    taps = [ "LizardByte/homebrew" ];
    brews = [ "sunshine-beta" ];
    casks = [
      "visual-studio" # ide
      "qq" "wechat" # sms
      "bilibili" # video
      "steam" "minecraft" "itch" # games
      "zen" # browser
      "krita" # image editor
      "baidunetdisk" # netdisk
      # "mihomo-party" # proxy # no opensource
      "sf-symbols" "background-music"  # sketchybar tools
    ];
    
  };

  # Enable alternative shell support in nix-darwin.
  programs.fish.enable = true;

  services = {
    yabai = {
      enable = true;
      config = {
        mouse_follows_focus = false;
        focus_follows_mouse = false;
        window_origin_display = "default";
        window_placement = "second_child";
        window_topmost = false;
        window_shadow = true;
        window_opacity = true;
        active_window_opacity = 1.0;
        normal_window_opacity = 0.90;
        window_animation_easing = "ease_in_out_cubic";
        window_animation_duration = 0.2;
        insert_feedback_color = "0xffd75f5f";
        split_ratio = 0.50;
        auto_balance = false;
        mouse_modifier = "alt";
        mouse_action1 = "move";
        mouse_action2 = "resize";
        mouse_drop_action = "swap";
        layout = "bsp";
        top_padding = 70;
        bottom_padding = 15;
        left_padding = 15;
        right_padding = 15;
        window_gap = 15;
      };

      enableScriptingAddition = true;
      extraConfig = ''
        sudo yabai --load-sa
        yabai -m signal --add event=dock_did_restart action="sudo yabai --load-sa"
        yabai -m signal --add event=window_focused action="sketchybar --trigger window_focus"
        yabai -m signal --add event=window_created action="sketchybar --trigger windows_on_spaces"
        yabai -m signal --add event=window_destroyed action="sketchybar --trigger windows_on_spaces"
        yabai -m rule --add app="^System Preferences$" manage=off
        yabai -m rule --add app="^Archive Utility$" manage=off
        yabai -m rule --add app="^Logi Options+$" manage=off
        yabai -m rule --add app="^Alfred Preferences$" manage=off
        yabai -m rule --add app="^(.*?bilibili.*?|.*?哔哩哔哩.*?)$" manage=off layer=above
      '';
    };

    skhd = {
      enable = true;
      skhdConfig = ''
      '';
    };

    sketchybar = {
      enable = true;
      config = ''
        SKETCHBAR_BIN="sketchybar"
        BEMLY_HOME="/Users/bemly"
        PLUGIN_DIR="$BEMLY_HOME/.config/sketchybar/plugins"
        ITEM_DIR="$BEMLY_HOME/.config/sketchybar/items"

        LABEL_FONT_FAMILY="苹方-简"
        LABEL_FONT_STYLE="Medium"
        LABEL_FONT_SIZE="14"
        LABEL_COLOR=0xffdfe1ea                                     
        ICON_FONT_FAMILY="Hack Nerd Font"
        ICON_FONT_STYLE="Regular"
        ICON_FONT_SIZE="16"
        BAR_COLOR=0xee1a1c26
        LABEL_COLOR=0xffdfe1ea                                     
        BACKGROUND_COLOR=0xff252731
        BACKGROUND_HEIGHT=33
        BACKGROUND_CORNER_RADIUS=20
        PADDINGS=3

        $SKETCHBAR_BIN --bar height=50                                                     \
                            corner_radius=14                                              \
                            border_width=0                                                \
                            margin=95                                                     \
                            blur_radius=0                                                 \
                            position=top                                                  \
                            padding_left=4                                                \
                            padding_right=4                                               \
                            color=$BAR_COLOR                                              \
                            topmost=off                                                   \
                            sticky=on                                                     \
                            font_smoothing=off                                            \
                            y_offset=10                                                   \
                            notch_width=0                                                 \
                                                                                          \
                  --default drawing=on                                                    \
                            updates=when_shown                                            \
                            label.font.family="$LABEL_FONT_FAMILY"                        \
                            label.font.style=$LABEL_FONT_STYLE                            \
                            label.font.size=$LABEL_FONT_SIZE                              \
                            label.padding_left=$PADDINGS                                  \
                            label.padding_right=$PADDINGS                                 \
                            icon.font.family="$ICON_FONT_FAMILY"                          \
                            icon.font.style=$ICON_FONT_STYLE                              \
                            icon.font.size=$ICON_FONT_SIZE                                \
                            icon.padding_left=$PADDINGS                                   \
                            icon.padding_right=$PADDINGS                                  \
                            background.padding_right=$PADDINGS                            \
                            background.padding_left=$PADDINGS                             \

        $SKETCHBAR_BIN --add event window_focus
        $SKETCHBAR_BIN --add event title_change 

        . "$ITEM_DIR/menu.sh"
        . "$ITEM_DIR/system.sh"
        . "$ITEM_DIR/window_title.sh"
        
        . "$ITEM_DIR/time.sh"
        . "$ITEM_DIR/battery.sh"

        . "$ITEM_DIR/bluetooth.sh"
        . "$ITEM_DIR/vpn.sh"
        . "$ITEM_DIR/wifi.sh"

        $SKETCHBAR_BIN --update

        echo "sketchybar configuration loaded.."

      '';
      extraPackages = with pkgs; [
        jq fzf pay-respects autojump ranger lsd gh switchaudio-osx cava blueutil
      ];
    };
  };

  security.sudo.extraConfig = ''
    bemly ALL=(root) NOPASSWD: sha256:1eeda4bf3ea841f4b53e02d8278067d96326e20e8093a87e46626a716fe78f7b /run/current-system/sw/bin/yabai --load-sa
  '';

  # Home Manager
  imports = [ <home-manager/nix-darwin> ];
  
  users.users.bemly = {
    name = "bemly";
    home = "/Users/bemly";
  };

  home-manager.backupFileExtension = "backup";

  home-manager.users.bemly = { pkgs, ... }: {
    home.packages = with pkgs; [
      # java runtime: pick one of jdks
      # temurin-bin semeru-bin openjdk zulu graalvm
      graalvmPackages.graalvm-ce
      # mc-server: pick one of servers
      # purpur papermc minecraft-server
      purpur
    ];
    home.stateVersion = "25.11";

    programs = {
      home-manager.enable = true;

      gh-dash.enable = true;
      gh = {
        enable = true;
        extensions = with pkgs; [
          gh-i gh-f gh-gei gh-eco gh-dash gh-classroom gh-markdown-preview
        ];
        hosts."github.com".user = "Bemly";
        settings = {
          git_protocol = "https";
          prompt = "enabled";
          aliases.co = "pr checkout";
          editor = "micro";
        };
      };
      git = {
        enable = true;
        lfs.enable = true;
        settings.user = {
        	email = "bemly_@petalmail.com";
        	name = "Bemly";
        };
        signing = {
          key = "A173F8531FE6C066";
          signByDefault = true;
        };
      };
    };

    # if nix-darwin services.yabai.config not work, it's alternatives, like me :)
    # Post `darwin-rebuild switch` Command: `yabai --restart-service`
    home.file.".yabairc".text = ''
      #!/usr/bin/env sh

      sudo yabai --load-sa
      yabai -m signal --add event=dock_did_restart action="sudo yabai --load-sa"

      # global settings
      yabai -m config mouse_follows_focus          off
      yabai -m config focus_follows_mouse          off
      yabai -m config window_origin_display        default
      yabai -m config window_placement             second_child
      yabai -m config window_topmost               off
      yabai -m config window_shadow                on
      yabai -m config window_opacity               on
      yabai -m config active_window_opacity        1.0
      yabai -m config normal_window_opacity        0.90

      # 动画
      yabai -m config window_animation_easing      ease_in_out_cubic
      yabai -m config window_animation_duration    0.2

      yabai -m config insert_feedback_color        0xffd75f5f
      yabai -m config split_ratio                  0.50
      yabai -m config auto_balance                 off
      yabai -m config mouse_modifier               alt
      yabai -m config mouse_action1                move
      yabai -m config mouse_action2                resize
      yabai -m config mouse_drop_action            swap

      yabai -m config layout                       bsp
      yabai -m config top_padding                  70
      yabai -m config bottom_padding               15
      yabai -m config left_padding                 15
      yabai -m config right_padding                15
      yabai -m config window_gap                   15

      # 忽略的 app
      yabai -m rule --add app="^System Preferences$" manage=off
      yabai -m rule --add app="^Archive Utility$" manage=off
      yabai -m rule --add app="^Logi Options+$" manage=off
      yabai -m rule --add app="^Alfred Preferences$" manage=off
      
      # 浮动app
      # yabai -m rule --add app="^(.*?bilibili.*?|.*?哔哩哔哩.*?)$" manage=off layer=above

      # skbar 信号源
      yabai -m signal --add event=window_focused action="sketchybar --trigger window_focus"
      yabai -m signal --add event=window_created action="sketchybar --trigger windows_on_spaces"
      yabai -m signal --add event=window_destroyed action="sketchybar --trigger windows_on_spaces"

      # for i in {1..10}; do
      #   yabai -m space --create
      # done

      echo "yabai configuration loaded..."
    '';

    # if nix-darwin services.skhd.config not work, it's alternatives, like me :)
    # Post `darwin-rebuild switch` Command: `skhd -r`
    home.file.".skhdrc".text = ''
      # A list of all built-in modifier and literal keywords can
      # be found at https://github.com/koekeishiya/skhd/issues/1
      #
      # A hotkey is written according to the following rules:
      #
      #   hotkey       = <mode> '<' <action> | <action>
      #
      #   mode         = 'name of mode' | <mode> ',' <mode>
      #
      #   action       = <keysym> '[' <proc_map_lst> ']' | <keysym> '->' '[' <proc_map_lst> ']'
      #                  <keysym> ':' <command>          | <keysym> '->' ':' <command>
      #                  <keysym> ';' <mode>             | <keysym> '->' ';' <mode>
      #
      #   keysym       = <mod> '-' <key> | <key>
      #
      #   mod          = 'modifier keyword' | <mod> '+' <mod>
      #
      #   key          = <literal> | <keycode>
      #
      #   literal      = 'single letter or built-in keyword'
      #
      #   keycode      = 'apple keyboard kVK_<Key> values (0x3C)'
      #
      #   proc_map_lst = * <proc_map>
      #
      #   proc_map     = <string> ':' <command> | <string>     '~' |
      #                  '*'      ':' <command> | '*'          '~'
      #
      #   string       = '"' 'sequence of characters' '"'
      #
      #   command      = command is executed through '$SHELL -c' and
      #                  follows valid shell syntax. if the $SHELL environment
      #                  variable is not set, it will default to '/bin/bash'.
      #                  when bash is used, the ';' delimeter can be specified
      #                  to chain commands.
      #
      #                  to allow a command to extend into multiple lines,
      #                  prepend '\' at the end of the previous line.
      #
      #                  an EOL character signifies the end of the bind.
      #
      #   ->           = keypress is not consumed by skhd
      #
      #   *            = matches every application not specified in <proc_map_lst>
      #
      #   ~            = application is unbound and keypress is forwarded per usual, when specified in a <proc_map>
      #
      # A mode is declared according to the following rules:
      #
      #   mode_decl = '::' <name> '@' ':' <command> | '::' <name> ':' <command> |
      #               '::' <name> '@'               | '::' <name>
      #
      #   name      = desired name for this mode,
      #
      #   @         = capture keypresses regardless of being bound to an action
      #
      #   command   = command is executed through '$SHELL -c' and
      #               follows valid shell syntax. if the $SHELL environment
      #               variable is not set, it will default to '/bin/bash'.
      #               when bash is used, the ';' delimeter can be specified
      #               to chain commands.
      #
      #               to allow a command to extend into multiple lines,
      #               prepend '\' at the end of the previous line.
      #
      #               an EOL character signifies the end of the bind.

      # exclude shortcut hell software
      .blacklist [ "com.adobe.Photoshop" "com.logicpro.X" "com.yourcadsoftware.pro" ]


      # focus window
      # alt - h : yabai -m window --focus west

      # swap managed window
      # shift + alt - h : yabai -m window --swap north
      # shift + cmd + alt - n : yabai -m window --swap prev
      # cmd + alt - n : yabai -m window --swap next

      # move managed window
      # shift + cmd - h : yabai -m window --warp east
      cmd + alt - 0x1E : yabai -m window --warp east # kVK_ANSI_RightBracket
      cmd + alt - 0x21 : yabai -m window --warp west # kVK_ANSI_LeftBracket

      # balance size of windows
      # shift + alt - 0 : yabai -m space --balance
      cmd + alt - b : yabai -m space --balance

      # make floating window fill screen
      # shift + alt - up     : yabai -m window --grid 1:1:0:0:1:1

      # make floating window fill left-half of screen
      # shift + alt - left   : yabai -m window --grid 1:2:0:0:1:1

      # create desktop, move window and follow focus - uses jq for parsing json (brew install jq)
      # alt + cmd - n : yabai -m space --create && \
      #                   index="$(yabai -m query --spaces --display | jq 'map(select(."is-native-fullscreen" == false))[-1].index')" && \
      #                   yabai -m window --space "\$\{index\}" && \
      #                   yabai -m space --focus "\$\{index\}"
      cmd + alt - n : yabai -m space --create; sketchybar --trigger window_focus
      cmd + alt - m : yabai -m space --destroy; sketchybar --trigger window_focus
      # nix-darwin not support `\$\{\}`, so use alt + cmd - left/right to focus new create space manually :(

      # fast focus desktop
      # cmd + alt - x : yabai -m space --focus recent
      cmd + alt - x : yabai -m space --focus recent
      cmd + alt - 1 : yabai -m space --focus 1
      cmd + alt - 2 : yabai -m space --focus 2
      cmd + alt - 3 : yabai -m space --focus 3
      cmd + alt - 4 : yabai -m space --focus 4
      cmd + alt - 5 : yabai -m space --focus 5
      cmd + alt - 6 : yabai -m space --focus 6
      cmd + alt - 7 : yabai -m space --focus 7
      cmd + alt - 8 : yabai -m space --focus 8
      cmd + alt - 9 : yabai -m space --focus 9
      cmd + alt - 0 : yabai -m space --focus 0

      alt + cmd - left : yabai -m space --focus prev
      alt + cmd - right : yabai -m space --focus next

      # send window to desktop and follow focus
      # shift + cmd - z : yabai -m window --space next; yabai -m space --focus next
      # shift + cmd - 2 : yabai -m window --space  2; yabai -m space --focus 2
      # shift + cmd - 9 : yabai -m window --space  9; yabai -m space --focus 9

      # focus monitor
      # ctrl + alt - z  : yabai -m display --focus prev
      # ctrl + alt - 3  : yabai -m display --focus 3
      alt + cmd - up : yabai -m window --focus prev
      alt + cmd - down : yabai -m window --focus next

      # send window to monitor and follow focus
      # ctrl + cmd - c  : yabai -m window --display next; yabai -m display --focus next
      # ctrl + cmd - 1  : yabai -m window --display 1; yabai -m display --focus 1
      shift + alt - x : yabai -m window --space recent && sketchybar --trigger windows_on_spaces; yabai -m space --focus recent
      cmd - 1 : yabai -m window --space 1 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 1
      cmd - 2 : yabai -m window --space 2 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 2
      cmd - 3 : yabai -m window --space 3 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 3
      cmd - 4 : yabai -m window --space 4 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 4
      cmd - 5 : yabai -m window --space 5 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 5
      cmd - 6 : yabai -m window --space 6 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 6
      cmd - 7 : yabai -m window --space 7 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 7
      cmd - 8 : yabai -m window --space 8 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 8
      cmd - 9 : yabai -m window --space 9 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 9
      cmd - 0 : yabai -m window --space 0 && sketchybar --trigger windows_on_spaces; yabai -m space --focus 0
      cmd - up : yabai -m window --space prev && sketchybar --trigger windows_on_spaces; yabai -m space --focus prev
      cmd - down : yabai -m window --space next && sketchybar --trigger windows_on_spaces; yabai -m space --focus next

      # move floating window
      # shift + ctrl - a : yabai -m window --move rel:-20:0
      # shift + ctrl - s : yabai -m window --move rel:0:20

      # increase window size
      # shift + alt - a : yabai -m window --resize left:-20:0
      # shift + alt - w : yabai -m window --resize top:0:-20

      # decrease window size
      # shift + cmd - s : yabai -m window --resize bottom:0:-20
      # shift + cmd - w : yabai -m window --resize top:0:20

      # set insertion point in focused container
      # ctrl + alt - h : yabai -m window --insert west

      # toggle window zoom
      alt + cmd - d : yabai -m window --toggle zoom-parent
      alt + cmd - f : yabai -m window --toggle zoom-fullscreen; sketchybar --trigger window_focus

      # toggle window split type
      alt + cmd - x : yabai -m window --toggle split

      # float / unfloat window and center on screen
      alt + cmd - space : yabai -m window --toggle float --grid 4:4:1:1:2:2; sketchybar --trigger window_focus

      # toggle sticky(+float), picture-in-picture
      alt + cmd - p : yabai -m window --toggle sticky --toggle pip


      cmd - t : open /Applications/Nix\ Apps/Warp.app
      cmd - e : open ~
      cmd - q : yabai -m window --focus && yabai -m window --close
    '';
  };
}
