. "$HOME/.atuin/bin/env"

# --- 基础历史设置 ---
HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
setopt share_history hist_ignore_dups hist_ignore_space
setopt prompt_subst

# --- 补全系统（需在其他补全插件之前初始化） ---
autoload -Uz compinit && compinit

# --- fzf-tab（必须在 compinit 之后、其他会改变补全行为的插件之前） ---
source /usr/local/opt/fzf-tab/share/fzf-tab/fzf-tab.zsh

# --- zsh-autosuggestions ---
source /usr/local/share/zsh-autosuggestions/zsh-autosuggestions.zsh

# --- zsh-completions（brew 安装后其补全已在 fpath 中，compinit 会加载） ---
fpath=(/usr/local/share/zsh-completions $fpath)
autoload -Uz compinit && compinit -i

# --- zoxide（cd 增强） ---
eval "$(zoxide init zsh)"

# --- atuin（历史记录管理） ---
eval "$($HOME/.atuin/bin/atuin init zsh)"

# --- starship 提示符（CHT 蓝白移植版，见 ../starship/starship.toml） ---
eval "$(starship init zsh)"

# --- zsh-syntax-highlighting 必须放在所有插件最后一行 ---
source /usr/local/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# --- fastfetch 开屏（仅交互式顶层 shell，避免干扰 agent） ---
if [[ $- == *i* && $SHLVL -eq 1 && $TERM != dumb && -z "$FASTFETCH_DISABLED" ]]; then
  command -v fastfetch >/dev/null 2>&1 && fastfetch
fi


# Added by CodeBuddy CN - shell command
export PATH="$HOME/.codebuddy/bin:$PATH"

. "$HOME/.local/bin/env"
