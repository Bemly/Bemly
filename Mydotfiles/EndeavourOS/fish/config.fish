set -gx PATH $PATH /usr/local/bin
alias ll 'ls -al --color'
alias grep 'grep --color=auto'
alias cat 'bat'


set -gx XMODIFIERS @im=fcitx
set -gx GTK_IM_MODULE 'fcitx'
set -gx QT_IM_MODULE 'fcitx'

if status is-interactive
    # Commands to run in interactive sessions can go here
end
