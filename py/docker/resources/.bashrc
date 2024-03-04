#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# Don't put duplicate lines or lines starting with a space in the history
HISTCONTROL=ignoreboth

# Append to the history file, don't overwrite it
shopt -s histappend

HISTSIZE=1000000
HISTFILESIZE=1000000

# Check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS
shopt -s checkwinsize

force_color_prompt=yes

PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

export TERM=alacritty

set -o vi

# Set a fancy prompt (non-color, unless we know we want color)
case "$TERM" in
	xterm-color|*-256color) color_prompt=yes;;

	xterm*|xterm-256color|rxvt*|Eterm|alacritty*|aterm|kterm|gnome*)
		PROMPT_COMMAND=${PROMPT_COMMAND:+$PROMPT_COMMAND; }'printf "\033]0;%s@%s:%s\007" "${USER}" "${HOSTNAME%%.*}" "${PWD/#$HOME/\~}"';;
esac

alias ls='ls --color=auto'
alias grep='grep --color=auto'
