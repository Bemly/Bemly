
# dotfiles-EOS

![](screenshot/2.avif)
![](screenshot/1.avif)

 ## 中文

  本仓库收录的是本喵日常使用的炒鸡好用的Linux工具集合，主要存放我的一些配置文件用来备份。

  从 Manjaro + i3wm (非官方维护) 换下来，主要是 **Arch 邪教** 好像对 mos 的私有源颇有微词

  说实话中国镜像基本没有，所以就来投奔 默认使用官方源 的 EndeavourOS 拉

  正好顺带换个支持 XWayland 层兼容的 Hyprland 混成器 玩玩

  Hyprland 和 EndeavourOS 适合小白，比 archinstall 还无脑，墙烈安利

  顺带一体用了 Arch 才知道，arch 社区维护的包是真的多，直接无脑一行 pacman -Syy 就完事了

  在 Arch 上面基本不怎么考虑 flatpak 了（ 其他系统上的深度 flatpak 用户 :3 ）

  ### 窗口管理器

  Hyprland Hyprshot Hyprpaper Waypaper 一体，包含截图、壁纸一体了，个人不是很喜欢任务栏就没要waybar

  ### 字体

  sarasa - 舒服的开源汉字字体 更纱

  iosevka-term - 宽度很窄的字体，一行可以放更多，适合我这样的代码异端(?)

  ### 软件包管理器

  flatpak -  跨类Unix平台的软件包管理器，不用说，豪用、必用

  paru - 现代的 Arch Pacman 包管理工具，Rust编写

  ### Shell 终端
  
  besh - 自己用Rust瞎写的，正在完善利用Libc库包的unsafe shell ( 自己写的，哭着也要用下去

  fish - 好吧，上面那个基本没怎么碰过，fish主力 名字好听，尝鲜用

  fisher - fish 插件管理器

  tide - fish 美化

  pwsh - PowerShell 不得不尝

  ### 虚拟机/容器

  podman - 红帽的容器平台，Docker 容器国内最近被制裁了，换个口味

  qemu-KVM - Linux常用的虚拟化软件

  bottles - 快捷wine环境部署

  a-anime-game-launcher - 启动！Proton 兼容层，DXVK 转义 统统启动

  xdroid - 国产Android容器

  ### Terminal 终端

  kitty - Hyprland官方推荐，透明和亚克力效果对Hyprpaper这些的兼容性很好，就用了

  wezterm - Rust编写的 GPU 友好终端，不过纯 X11 环境下运行才正常，Wayland 对 N卡 支持太差，目前已知的就是光标不动，刷新会降到 0.2 FPS，非常难受

  ### 浏览器

  Ladybird - 开源自由浏览器，能用

  servo - mozilla 提出的由 Rust 开发的下一代 Gecko 浏览器引擎, 维护缓慢

  firefox

  ### 输入法

  fcitx - 不用ibus，对wayland兼容问题较多，主要是想尝一下百度输入法 for linux

  baidu-qimpanel - 基于fcitx的百度输入法，支持云输入，第三方维护（已过时但能跑）

  rime + rime-ice - 雾凇词库，候选热词不多，但也能用

  ### 任务管理器

  btop++ - 炒好看的TUI任务管理器

  mangohud - 对标微星小飞机的占用叠加层，OpenGL需要加上--dlsym参数叠加

  system-monitoring-center - 类似windows，但远胜过windows的任务管理器

  ### 引导

  systemd-boot - 很快昂，装的时候忘记美化没要GRUB，现在看上去挺简洁的(

  ### 图片查看器/资源管理器/播放器/小玩具

  viu - 支持kitty wezterm这些pts的图像输出 图片查看器

  nnn/xplr - TUI 的资源管理器

  btrfs duf - 可视化占用百分比

  baka-mplayer - 一个非常9 智慧的播放器

  mpv vlc - 两套非常经典的视频播放器组合拳

  neofetch/screenfetch - 灵魂(?

  nmcil/nmtui - 非常直观好用的代替iw的 网络管理器

  bat - 有行数的cat

  ### 编辑器

  neovim - 纯键盘的天下，搭配上主题非常好看，个人不是很能上手vim，当玩具摆放了

  helix - Rust 构建的 下一代 VIM 编辑器，玩具

  code - vsc 轻量级编辑器，平时修改一些小东西非常适合

  jetbrains-ide - 全家桶，开箱即用，jvm 跨平台

  zed - 新鲜的IDE，目前刚开放Linux版本，支持MACOS和类Unix，直接爽玩

  ### 聊天

  matrix linuxqq

  paperplane - rust重写的电报第三方客户端

  ### 办公

  wps-office - qt写的，跨平台，ui好看也兼容文档，完美的 msoffice 平替

  obs-studio - 串流还是录屏都好，搭配 pipewire，但是pw好像对wayland兼容不太好，流容易卡住

  lceda-pro gimp gtk krita postman wireshark 

  ### 游戏启动器

  minecraft-launcher - Hyprland上面运行有bug, electron写的

  hmcl-bin - 老牌启动器，支持neoforge、quilt等新兴模组加载器

  ymcl - 基于 pyqt 的跨平台 云母 风格启动器 Microsoft Fluent Design

  multimc - 模组调试、开发常用这个玩，日志高亮比较全

  ### 音乐

  netease-music-tui music-box - 两个用网易云音乐的TUI播放器

  osu-lazer - 音乐播放器 确信

  ### 剪贴板

  ? 还没用 先熬下

  ### 小插曲

   无聊随便写写，之后搬进博客

   入坑类Unix尝鲜顺序：

   1. Phoenix OS

   2. Deepin V15 (最好的一代 DDE)

   3. Centos 7

   4. Ubuntu 20.04/Alpine OS

   5. Openfyde

   6. Zorin OS 16 Pro

   7. Pop! os 22.04 LTS

   8. Manjaro

  ### 代办

  一键安装的 shell 还在写 ( 文件夹已经创建好了 逃 )

 ## English


This repository contains a collection of Linux tools that I use daily, mainly for storing some of my configuration files for backup.

I switched from Manjaro + i3wm (unofficial maintenance), mainly because the **Arch cult** seems to have some complaints about the private source of mos

To be honest, there are basically no Chinese mirrors, so I came to EndeavourOS, which uses the official source by default

It just so happens that I can switch to the Hyprland mixer that supports XWayland layer compatibility to play with

Hyprland and EndeavourOS are suitable for novices, and are more brainless than archinstall. I recommend them to everyone

I used Arch all-in-one and realized that there are really many packages maintained by the arch community. Just a brainless line of pacman -Syy is enough

I basically don’t consider flatpak on Arch (deep flatpak users on other systems :3)

### Window manager

Hyprland Hyprshot Hyprpaper Waypaper all-in-one, including screenshots and wallpapers, I don’t like the taskbar very much, so I didn’t use waybar

### Font

sarasa - Comfortable open source Chinese font Gengsha

iosevka-term - A very narrow font, which can hold more text in one line, suitable for code heretics like me (?)

### Package manager

flatpak - A package manager across Unix platforms, needless to say, it is a must-have

paru - A modern Arch Pacman package management tool, written in Rust

### Shell terminal

besh - I wrote it myself in Rust, and am currently improving the unsafe shell that uses the Libc library package (I wrote it myself, and I have to use it even if I cry

fish - Well, I haven't touched the one above, fish is the main one. The name sounds good, so I'll use it for trial

fisher - fish plugin manager

tide - fish beautification

pwsh - PowerShell must try

### Virtual machine/container

podman - Red Hat's container platform, Docker container has been sanctioned in China recently, so let's try it

qemu-KVM - Common virtualization software for Linux

bottles - Quick wine environment deployment

a-anime-game-launcher - Start! Proton compatibility layer, DXVK escape, all started

xdroid - Domestic Android container

### Terminal

kitty - Hyprland official recommendation, transparent and acrylic effects are very compatible with Hyprpaper, so I used it

wezterm - GPU-friendly terminal written in Rust, but it runs normally in a pure X11 environment. Wayland has poor support for N cards. What is known so far is that the cursor does not move and the refresh will drop to 0.2 FPS, which is very uncomfortable

### Browser

Ladybird - Open source free browser, usable

servo - The next generation Gecko browser engine developed by Rust proposed by mozilla, with slow maintenance

firefox

### Input method

fcitx - Don't use ibus, there are many compatibility issues with wayland, mainly want to try Baidu input method for linux

baidu-qimpanel - Baidu input method based on fcitx, supports cloud input, third-party maintenance (outdated but can run)

rime + rime-ice - Rime vocabulary, not many candidate hot words, but can be used

### Task manager

btop++ - A good-looking TUI task manager

mangohud - Comparing the occupancy overlay of MSI's small aircraft, OpenGL needs to add the --dlsym parameter overlay

system-monitoring-center - Similar to windows, but far better than windows' task manager

### Boot

systemd-boot - Very fast, I forgot to beautify and didn't ask for GRUB when installing, now it looks quite simple (

### PictureViewer/ResManager/player/toy

viu - Supports image output of kitty wezterm and other pts Picture viewer

nnn/xplr - TUI resource manager

btrfs duf - Visualize occupancy percentage

baka-mplayer - A very 9 smart player

mpv vlc - A combination of two very classic video players

neofetch/screenfetch - Soul(?

nmcil/nmtui - A very intuitive and easy-to-use network manager to replace iw

bat - cat with line numbers

### Editor

neovim - A pure keyboard world, with a very nice theme, I am not very good at vim, just put it on display as a toy

helix - A next-generation VIM editor built with Rust, a toy

code - a vsc lightweight editor, very suitable for modifying some small things

jetbrains-ide - A whole family of buckets, ready to use, jvm cross-platform

### Chat

matrix linuxqq

paperplane - A third-party telegram client rewritten by rust

### Office

wps-office - Written in qt, cross-platform, beautiful ui and compatible with documents, a perfect msoffice alternative

obs-studio - Good for streaming or screen recording, with pipewire, but pw seems to be not very compatible with wayland, and the stream is easy to get stuck

lceda-pro gimp gtk krita postman wireshark

### Game launcher

minecraft-launcher - There are bugs when running on Hyprland, written by electron

hmcl-bin - An old-fashioned launcher that supports emerging module loaders such as neoforge and quilt

ymcl - A cross-platform mica-style launcher based on pyqt Microsoft Fluent Design

multimc - This is often used for module debugging and development, and the log highlighting is relatively complete

### Music

netease-music-tui music-box - Two TUI players using NetEase Cloud Music

osu-lazer - Music player Confirmed

### Clipboard

? Not used yet, wait for it first
