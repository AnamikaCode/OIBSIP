"""
Random Password Generator - Advanced Tier
GUI application (tkinter) with:
  - Spinbox for length + checkboxes for character type selection
  - Cryptographically secure generation via the `secrets` module
  - Strength indicator (Weak / Medium / Strong)
  - Guaranteed inclusion of at least one char from each selected type
  - "Copy to Clipboard" via pyperclip, auto-copy on generation
  - Option to exclude ambiguous characters (0, O, l, 1, I, etc.)
  - In-session history of the last 5 generated passwords (never saved to disk)
"""

import string
import secrets
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

MIN_LENGTH = 6
MAX_LENGTH = 64
AMBIGUOUS_CHARS = "0Ol1I|`'\""

STRENGTH_COLORS = {
    "Weak": "#e74c3c",
    "Medium": "#f39c12",
    "Strong": "#2ecc71",
}


# --------------------------------------------------------------------------
# Core generation logic
# --------------------------------------------------------------------------
def build_pools(use_upper, use_lower, use_digits, use_symbols, exclude_ambiguous):
    pools = {}
    if use_upper:
        pools["upper"] = string.ascii_uppercase
    if use_lower:
        pools["lower"] = string.ascii_lowercase
    if use_digits:
        pools["digits"] = string.digits
    if use_symbols:
        pools["symbols"] = string.punctuation

    if exclude_ambiguous:
        for key in pools:
            pools[key] = "".join(c for c in pools[key] if c not in AMBIGUOUS_CHARS)
            if not pools[key]:
                # Guard against a pool becoming empty after exclusion
                raise ValueError(
                    "Excluding ambiguous characters removed an entire character set. "
                    "Try unchecking 'Exclude ambiguous characters' or selecting another type."
                )
    return pools


def generate_password(length, pools):
    """Cryptographically secure generation, guaranteeing 1+ char per selected type."""
    if not pools:
        raise ValueError("Select at least one character type.")

    # One guaranteed character from each selected pool
    required = [secrets.choice(chars) for chars in pools.values()]

    full_pool = "".join(pools.values())
    remaining = length - len(required)
    if remaining < 0:
        raise ValueError("Length too short for the number of selected character types.")

    password_chars = required + [secrets.choice(full_pool) for _ in range(remaining)]

    # Secure shuffle (Fisher-Yates using secrets.randbelow)
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)


def evaluate_strength(password, type_count):
    """Simple heuristic: length + character-type diversity -> Weak/Medium/Strong."""
    length = len(password)

    if length < 8 or type_count <= 1:
        return "Weak"
    elif length < 12 or type_count == 2:
        return "Medium"
    else:
        return "Strong"


# --------------------------------------------------------------------------
# GUI Application
# --------------------------------------------------------------------------
class PasswordGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Generator")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(bg="#f5f6fa")

        self.history = []  # last 5 passwords, in-memory only

        self._build_widgets()

    # ---------------- UI construction ----------------
    def _build_widgets(self):
        title = tk.Label(self, text="Password Generator", font=("Segoe UI", 18, "bold"),
                          bg="#f5f6fa")
        title.pack(pady=(15, 10))

        # Length control
        length_frame = tk.Frame(self, bg="#f5f6fa")
        length_frame.pack(pady=5)
        tk.Label(length_frame, text="Length:", bg="#f5f6fa").grid(row=0, column=0, padx=5)
        self.length_var = tk.IntVar(value=16)
        self.length_spin = tk.Spinbox(length_frame, from_=MIN_LENGTH, to=MAX_LENGTH,
                                       textvariable=self.length_var, width=6)
        self.length_spin.grid(row=0, column=1, padx=5)

        # Character type checkboxes
        types_frame = tk.LabelFrame(self, text="Character Types", bg="#f5f6fa", padx=10, pady=10)
        types_frame.pack(pady=10, padx=20, fill="x")

        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.exclude_ambiguous = tk.BooleanVar(value=False)

        tk.Checkbutton(types_frame, text="Uppercase (A-Z)", variable=self.use_upper,
                        bg="#f5f6fa").pack(anchor="w")
        tk.Checkbutton(types_frame, text="Lowercase (a-z)", variable=self.use_lower,
                        bg="#f5f6fa").pack(anchor="w")
        tk.Checkbutton(types_frame, text="Numbers (0-9)", variable=self.use_digits,
                        bg="#f5f6fa").pack(anchor="w")
        tk.Checkbutton(types_frame, text="Symbols (!@#$...)", variable=self.use_symbols,
                        bg="#f5f6fa").pack(anchor="w")
        tk.Checkbutton(types_frame, text="Exclude ambiguous characters (0, O, l, 1, I)",
                        variable=self.exclude_ambiguous, bg="#f5f6fa").pack(anchor="w")

        # Generate button
        gen_btn = tk.Button(self, text="Generate Password", command=self.on_generate,
                             bg="#4a69bd", fg="white", font=("Segoe UI", 11, "bold"),
                             width=20, cursor="hand2")
        gen_btn.pack(pady=15)

        # Result display
        result_frame = tk.Frame(self, bg="#dfe4ea")
        result_frame.pack(pady=5, padx=20, fill="x")

        self.password_var = tk.StringVar(value="")
        self.password_entry = tk.Entry(result_frame, textvariable=self.password_var,
                                        font=("Consolas", 13), justify="center",
                                        state="readonly", readonlybackground="#dfe4ea",
                                        bd=0)
        self.password_entry.pack(fill="x", padx=10, pady=10)

        copy_btn = tk.Button(self, text="Copy to Clipboard", command=self.on_copy,
                              bg="#6a89cc", fg="white", cursor="hand2")
        copy_btn.pack(pady=5)

        # Strength indicator
        strength_frame = tk.Frame(self, bg="#f5f6fa")
        strength_frame.pack(pady=10)
        tk.Label(strength_frame, text="Strength:", bg="#f5f6fa").grid(row=0, column=0, padx=5)
        self.strength_label = tk.Label(strength_frame, text="—", width=10,
                                        bg="#dfe4ea", font=("Segoe UI", 10, "bold"))
        self.strength_label.grid(row=0, column=1, padx=5)

        # History
        hist_frame = tk.LabelFrame(self, text="History (last 5, this session only)",
                                    bg="#f5f6fa", padx=10, pady=10)
        hist_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.history_listbox = tk.Listbox(hist_frame, font=("Consolas", 10), height=5)
        self.history_listbox.pack(fill="both", expand=True)

    # ---------------- Actions ----------------
    def on_generate(self):
        length = self.length_var.get()

        if length < MIN_LENGTH:
            messagebox.showerror("Invalid Length", f"Length must be at least {MIN_LENGTH}.")
            return

        selected_count = sum([
            self.use_upper.get(), self.use_lower.get(),
            self.use_digits.get(), self.use_symbols.get()
        ])
        if selected_count < 2:
            messagebox.showerror("Invalid Selection",
                                  "Please select at least 2 character types.")
            return

        try:
            pools = build_pools(
                self.use_upper.get(), self.use_lower.get(),
                self.use_digits.get(), self.use_symbols.get(),
                self.exclude_ambiguous.get()
            )
            password = generate_password(length, pools)
        except ValueError as e:
            messagebox.showerror("Generation Error", str(e))
            return

        self.password_var.set(password)

        strength = evaluate_strength(password, selected_count)
        self.strength_label.configure(text=strength, bg=STRENGTH_COLORS[strength], fg="white")

        self._add_to_history(password)
        self._copy_to_clipboard(password, silent=True)

    def on_copy(self):
        password = self.password_var.get()
        if not password:
            messagebox.showinfo("Nothing to Copy", "Generate a password first.")
            return
        self._copy_to_clipboard(password, silent=False)

    def _copy_to_clipboard(self, password, silent):
        if not CLIPBOARD_AVAILABLE:
            if not silent:
                messagebox.showwarning(
                    "Clipboard Unavailable",
                    "pyperclip is not installed. Run: pip install pyperclip"
                )
            return
        try:
            pyperclip.copy(password)
            if not silent:
                messagebox.showinfo("Copied", "Password copied to clipboard.")
        except Exception as e:
            if not silent:
                messagebox.showerror("Clipboard Error", f"Could not copy to clipboard:\n{e}")

    def _add_to_history(self, password):
        self.history.insert(0, password)
        self.history = self.history[:5]  # keep only last 5, in memory, never saved to disk

        self.history_listbox.delete(0, tk.END)
        for pw in self.history:
            self.history_listbox.insert(tk.END, pw)


if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()

#Random Password Generator
