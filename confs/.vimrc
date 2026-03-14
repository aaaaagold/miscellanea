
" 設定編碼順序(fileencodings)
set fencs=ucs-bom,utf-8,latin1
" 設定預設編碼(fileencoding)
set fenc=utf8
" enable 256 colors in vim (this must put before setting the colorscheme)
set t_Co=256
" tell vim that my background is dark, brighten the color of words
set bg=dark
" 開啟關鍵字上色功能
" syntax on
" 顯示當前的行號列號
set nu
" when scrolling, keep cursor 4 lines away from screen border
set scrolloff=4
" 定義tab 的空格數 (ts)
set tabstop=4
" 自動縮排所使用的空格數 (sw)
set shiftwidth=4
" 自動縮排
set ai
" 在狀態欄顯示正在輸入的命令
set showcmd
" 游標線, set cul == set cursorline
set cursorline
" 狀態列
set laststatus=2
" vim 裡打指令，按tab 會列出待選列表
set wildmenu
" 顯示 編輯模式 在左下角的狀態列
set ruler
" No annoying sound on errors
set noerrorbells
set novisualbell
set t_vb=
" After this time(ms) you can use a movement key again
set tm=333

"設定paste mode 的切換
function! PasteSwitch()
	if &paste
		set statusline=\ no\ paste
		set nopaste
	else
		set statusline=\ paste
		set paste
	endif
endfunction
noremap <leader>p :call PasteSwitch()<CR>

