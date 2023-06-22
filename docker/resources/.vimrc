filetype plugin indent on		" auto-indenting depending on file type
set nocompatible				" disable compatibility with vi

if exists('+termguicolors')
	let &t_8f="\<Esc>[38;2;%lu;%lu;%lum"
	let &t_8b="\<Esc>[48;2;%lu;%lu;%lum"
	set termguicolors
endif

set term=xterm-256color

syntax on
set number						" line numbers
set backspace=indent,eol,start	" backspace always working in insert mode
set showcmd						" show current partial command
set noswapfile
set nobackup					" disable backup file creation
set nowritebackup
set encoding=utf-8
set autowrite					" automatically save before :next, :make, etc
set autoread					" automatically reread changed files
set laststatus=2
set hidden						" hide buffers instead of closing them

set splitright					" split vertical windows to the right
set splitbelow					" split horizontal windows below

set ruler						" always show the cursor position
au FocusLost * :wa				" save all buffers on focus out
set ttyfast

set mouse=v						" middle-click paste
set mouse=a						" enable mouse click
set ttymouse=sgr

set hlsearch					" highlight search
set incsearch					" incremental search
set ignorecase					" search case insensitive...
set smartcase					" except when the it contains upper case characters
set conceallevel=2

set nocursorcolumn
set nocursorline
set norelativenumber

set wrap
set textwidth=80
set formatoptions=qrn1

set tabstop=4
set softtabstop=4				" multiple spaces as tabstops
set smarttab
set shiftwidth=4
set autoindent
set smartindent
set showmatch

set nrformats-=octal
set shiftround

set notimeout                   " time out on key code but not on mappings
set ttimeout
set ttimeoutlen=10

set complete=.,w,b,u,t          " better completion
" set completeopt=longest,menuone
set completeopt=menu,menuone,preview,noselect,noinsert

set wildmenu
set wildmode=longest,list		" bash-like tab completion

" remap split navigation
nnoremap <C-J> <C-W><C-J>
nnoremap <C-K> <C-W><C-K>
nnoremap <C-L> <C-W><C-L>
nnoremap <C-H> <C-W><C-H>

" Remap gk and gj to j and k
nnoremap j gj
nnoremap k gk

" Disable arrow keys
noremap <Down> <Nop>
noremap <Left> <Nop>
noremap <Right> <Nop>
noremap <Up> <Nop>

" Disable ctrl-b
noremap <C-B> <Nop>

let mapleader = ","

" Remove search highlight
nnoremap <leader><space> :nohlsearch<CR>

" Buffer prev/next
nnoremap <C-x> :bnext<CR>
nnoremap <C-z> :bprev<CR>

let g:polyglot_disabled = ['markdown']

call plug#begin(expand('~/.vim/plugged'))
	Plug 'arcticicestudio/nord-vim'
    Plug 'vim-airline/vim-airline'
	Plug 'sheerun/vim-polyglot'
	Plug 'junegunn/fzf.vim'
	Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
	Plug 'tpope/vim-vinegar'
	Plug 'dense-analysis/ale'
	Plug 'tpope/vim-commentary'
	Plug 'tpope/vim-surround'
	Plug 'tpope/vim-fugitive'
	Plug 'ntpeters/vim-better-whitespace'
	Plug 'lervag/wiki.vim'
	Plug 'lervag/vimtex'
	Plug 'mg979/vim-visual-multi', {'branch': 'master'}
call plug#end()

colorscheme nord
set cursorline

" ==================== vim-polyglot ====================

let g:csv_no_conceal = 1

" ==================== netrw ====================

let g:netrw_banner = 0
let g:netrw_liststyle = 3
let g:netrw_browse_split = 4
let g:netrw_winsize = 20
let g:netrw_altv = 1

nnoremap <leader>n :20Lexplore<CR>

" ==================== airline ====================

if !exists('g:airline_symbols')
  let g:airline_symbols = {}
  let g:airline_symbols.notexists = '?'
endif

let g:airline_powerline_fonts=0
let g:airline#extensions#whitespace#enabled=0
let g:airline_symbols.maxlinenr=''

" ==================== ale ====================

let g:ale_sign_error = '●'
let g:ale_sign_warning = '.'

let g:ale_linters = {
\	'java': [],
\	'python': ['pylsp'],
\	'c': ['clangd'],
\	'cpp': ['clangd'],
\	'latex': ['chktex'],
\   'bash': ['shellcheck']
\ }

let g:ale_python_pylsp_config={'pylsp': {
  \ 'plugins': {
  \   'ruff': {'enabled': v:true, 'lineLength': 100},
  \   'yapf': {'enabled': v:true},
  \ },
  \ }}

let g:ale_tex_chktex_options = '-n8 -n24'
let g:ale_virtualtext_cursor = 'disabled'
let g:ale_python_pyls_use_global = 1

let g:ale_completion_enabled = 1
let g:ale_completion_delay = 50

nnoremap <leader>gf :ALEGoToDefinition<CR>
nnoremap <leader>gr :ALEFindReferences -quickfix <bar> :copen<CR>
nnoremap <leader>rn :ALERename<CR>

nnoremap <leader>l :ALEToggle<CR>

" ==================== fzf ====================

nnoremap <C-p> :Files<CR>
nnoremap <leader>b :Buffers<CR>
nnoremap <leader>rr :Rg<CR>

" ==================== wiki.vim  ====================

let g:wiki_root = '~/resources/wiki'
let g:wiki_global_load = 0
let g:wiki_filetypes = ['md']
let g:wiki_link_extension = '.md'
let g:wiki_link_target_type = 'md'

" ==================== vimtex ====================

let g:tex_flavor='latex'
let g:vimtex_view_general_viewer='zathura'
let g:vimtex_quickfix_mode=0
let g:vimtex_syntax_conceal_disable=1

" ==================== vim-visual-multi ====================

let g:VM_mouse_mappings = 1

" ==================== vim-markdown ====================

let g:markdown_fenced_languages = ['python', 'bash=sh', 'java', 'p4']
let g:markdown_minlines = 500
let g:vim_markdown_conceal_code_blocks = 1
let g:vim_markdown_math = 1
