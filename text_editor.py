import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog


class TextEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Python Text Editor")
        self.geometry("900x650")
        self.minsize(520, 360)

        self.current_file: Path | None = None
        self.is_dirty = False

        self._build_ui()
        self._bind_shortcuts()
        self._update_title()
        self._update_status()

    def _build_ui(self):
        editor_frame = tk.Frame(self)
        editor_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            editor_frame,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1,
            font=("Courier New", 12),
            padx=12,
            pady=12,
            relief="flat",
        )
        self.text.pack(fill="both", expand=True, side="left")
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", lambda _event: self._update_status())
        self.text.bind("<ButtonRelease>", lambda _event: self._update_status())

        scrollbar = tk.Scrollbar(editor_frame, command=self.text.yview)
        scrollbar.pack(fill="y", side="right")
        self.text.configure(yscrollcommand=scrollbar.set)

        self.status = tk.StringVar()
        status_bar = tk.Label(
            self,
            textvariable=self.status,
            anchor="w",
            padx=8,
            pady=4,
            bg="#f0f0f0",
        )
        status_bar.pack(fill="x", side="bottom")

        self._build_menu()

    def _build_menu(self):
        menu_bar = tk.Menu(self)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(
            label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.quit_editor)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=False)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Cut", accelerator="Ctrl+X", command=lambda: self._event("<<Cut>>")
        )
        edit_menu.add_command(
            label="Copy", accelerator="Ctrl+C", command=lambda: self._event("<<Copy>>")
        )
        edit_menu.add_command(
            label="Paste", accelerator="Ctrl+V", command=lambda: self._event("<<Paste>>")
        )
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self.find_text)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        self.config(menu=menu_bar)

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda _event: self.new_file())
        self.bind("<Control-o>", lambda _event: self.open_file())
        self.bind("<Control-s>", lambda _event: self.save_file())
        self.bind("<Control-Shift-S>", lambda _event: self.save_as())
        self.bind("<Control-Shift-s>", lambda _event: self.save_as())
        self.bind("<Control-q>", lambda _event: self.quit_editor())
        self.bind("<Control-f>", lambda _event: self.find_text())
        self.protocol("WM_DELETE_WINDOW", self.quit_editor)

    def _on_modified(self, _event=None):
        if self.text.edit_modified():
            self.is_dirty = True
            self._update_title()
            self._update_status()
            self.text.edit_modified(False)

    def _update_title(self):
        filename = self.current_file.name if self.current_file else "Untitled"
        dirty_mark = "*" if self.is_dirty else ""
        self.title(f"{dirty_mark}{filename} - Python Text Editor")

    def _update_status(self):
        line, column = self.text.index("insert").split(".")
        content = self.text.get("1.0", "end-1c")
        words = len(content.split())
        chars = len(content)
        file_label = str(self.current_file) if self.current_file else "Unsaved file"
        self.status.set(
            f"{file_label}   |   Line {line}, Column {int(column) + 1}   |   "
            f"{words} words, {chars} chars"
        )

    def _event(self, event_name):
        self.text.event_generate(event_name)
        self._update_status()

    def _undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            return

    def _redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            return

    def _confirm_discard_changes(self):
        if not self.is_dirty:
            return True

        answer = messagebox.askyesnocancel(
            "Unsaved changes",
            "Save changes before continuing?",
        )
        if answer is None:
            return False
        if answer:
            return self.save_file()
        return True

    def new_file(self):
        if not self._confirm_discard_changes():
            return

        self.text.delete("1.0", "end")
        self.current_file = None
        self.is_dirty = False
        self.text.edit_reset()
        self._update_title()
        self._update_status()

    def open_file(self):
        if not self._confirm_discard_changes():
            return

        filename = filedialog.askopenfilename(
            title="Open file",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ],
        )
        if not filename:
            return

        path = Path(filename)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")
        except OSError as exc:
            messagebox.showerror("Open failed", str(exc))
            return

        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.current_file = path
        self.is_dirty = False
        self.text.edit_reset()
        self.text.edit_modified(False)
        self._update_title()
        self._update_status()

    def save_file(self):
        if self.current_file is None:
            return self.save_as()
        return self._write_file(self.current_file)

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save file",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ],
        )
        if not filename:
            return False

        path = Path(filename)
        return self._write_file(path)

    def _write_file(self, path):
        try:
            path.write_text(self.text.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save failed", str(exc))
            return False

        self.current_file = path
        self.is_dirty = False
        self.text.edit_modified(False)
        self._update_title()
        self._update_status()
        return True

    def find_text(self):
        query = simpledialog.askstring("Find", "Find text:")
        if not query:
            return

        self.text.tag_remove("search_match", "1.0", "end")
        start = "1.0"
        first_match = None

        while True:
            position = self.text.search(query, start, stopindex="end", nocase=True)
            if not position:
                break

            end = f"{position}+{len(query)}c"
            self.text.tag_add("search_match", position, end)
            first_match = first_match or position
            start = end

        self.text.tag_config("search_match", background="#fff176", foreground="#111111")
        if first_match:
            self.text.see(first_match)
            self.text.mark_set("insert", first_match)
            self._update_status()
        else:
            messagebox.showinfo("Find", f"No matches for '{query}'.")

    def quit_editor(self):
        if self._confirm_discard_changes():
            self.destroy()


if __name__ == "__main__":
    editor = TextEditor()
    editor.mainloop()
