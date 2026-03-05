
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class Node:
    def __init__(self, d): self.data = d; self.next = None

class Queue:                                  
    def __init__(self): self.head = self.tail = None; self.n = 0
    def enqueue(self, d):
        node = Node(d)
        if self.tail: self.tail.next = node
        self.tail = node
        if not self.head: self.head = node
        self.n += 1
    def dequeue(self):
        if not self.head: raise IndexError("Queue empty")
        d = self.head.data; self.head = self.head.next
        if not self.head: self.tail = None
        self.n -= 1; return d
    def to_list(self):
        r, c = [], self.head
        while c: r.append(c.data); c = c.next
        return r
    def is_empty(self): return self.n == 0

class Stack:                                  
    def __init__(self): self.top = None; self.n = 0
    def push(self, d):
        node = Node(d); node.next = self.top; self.top = node; self.n += 1
    def pop(self):
        if not self.top: raise IndexError("Stack empty")
        d = self.top.data; self.top = self.top.next; self.n -= 1; return d
    def is_empty(self): return self.n == 0

class FixedArray:                              
    def __init__(self, cap): self.cap = cap; self.d = [None]*cap; self.h = self.n = 0
    def insert(self, item):
        i = (self.h + self.n) % self.cap
        if self.n < self.cap: self.d[i] = item; self.n += 1
        else: self.d[self.h] = item; self.h = (self.h+1) % self.cap
    def all(self): return [self.d[(self.h+i) % self.cap] for i in range(self.n)]


class Account:
    def __init__(self, aid, owner, bal=0):
        self.id = aid; self.owner = owner; self._bal = bal
    def deposit(self, x):
        if x <= 0: raise ValueError("Monto inválido")
        self._bal += x
    def withdraw(self, x):
        if x <= 0: raise ValueError("Monto inválido")
        if x > self._bal: raise ValueError(f"Saldo insuficiente — disponible ${self._bal:,.0f}")
        self._bal -= x
    def balance(self): return self._bal

class Tx:
    _n = 1000
    def __init__(self, kind, amt, src=None, tgt=None):
        Tx._n += 1
        self.id = f"TXN-{Tx._n}"; self.kind = kind; self.amt = amt
        self.src = src; self.tgt = tgt; self.status = "PENDING"
        self.err = ""; self.time = datetime.now().strftime("%H:%M:%S")
    def __str__(self):
        return f"{self.id} | {self.kind:<10} | ${self.amt:>9,.0f} | {self.status:<12} | {self.time}"


class Engine:
    AUDIT_CAP = 8
    def __init__(self):
        self.queue = Queue(); self.audit = FixedArray(self.AUDIT_CAP)
        self.accounts = {}; self.done = []; self._cb = None
    def on_change(self, fn): self._cb = fn
    def _notify(self):
        if self._cb: self._cb()
    def add_account(self, aid, owner, bal=0):
        self.accounts[aid] = Account(aid, owner, bal)
    def submit(self, kind, amt, src=None, tgt=None):
        self.queue.enqueue(Tx(kind, amt, src, tgt)); self._notify()
    def process_next(self):
        if self.queue.is_empty(): return None
        tx = self.queue.dequeue(); self._run(tx); self._notify(); return tx
    def process_all(self):
        while not self.queue.is_empty(): self._run(self.queue.dequeue())
        self._notify()
    def _run(self, tx):
        steps = self._steps(tx)
        if not steps: tx.status = "FAILED"; self.audit.insert(tx); return
        stack = Stack()
        for _, action, undo in steps:
            try: action(); stack.push(undo)
            except Exception as e:
                tx.err = str(e)
                while not stack.is_empty():
                    try: stack.pop()()
                    except: pass
                tx.status = "ROLLED BACK"; self.audit.insert(tx); return
        tx.status = "COMPLETED"; self.done.append(tx)
    def _steps(self, tx):
        a = self.accounts
        try:
            if tx.kind == "DEPOSIT":
                ac = a[tx.src]
                return [("", lambda: ac.deposit(tx.amt), lambda: ac.withdraw(tx.amt))]
            if tx.kind == "WITHDRAW":
                ac = a[tx.src]
                return [("", lambda: ac.withdraw(tx.amt), lambda: ac.deposit(tx.amt))]
            if tx.kind == "TRANSFER":
                s, t = a[tx.src], a[tx.tgt]
                return [("", lambda: s.withdraw(tx.amt), lambda: s.deposit(tx.amt)),
                        ("", lambda: t.deposit(tx.amt),  lambda: t.withdraw(tx.amt))]
        except KeyError as e: tx.err = f"Cuenta no encontrada: {e}"
        return None

BG,PNL,BRD = "#2B2B2B","#3C3C3C","#555"
AC,TX,DIM   = "#64FFDA","#E0E0E0","#AAAAAA"
GR,RD,OR,PU,BL = "#4CAF50","#F44336","#FF9800","#9C27B0","#2196F3"

class App(tk.Tk):
    def __init__(self, eng):
        super().__init__(); self.eng = eng; eng.on_change(self._refresh)
        self.title("🏦 Motor de Transacciones Bancarias")
        self.geometry("1050x680"); self.configure(bg=BG); self._build(); self._refresh()

    def _lbx(self, p, h, fg=None):
        lb = tk.Listbox(p, font=("Courier New",8), bg=BG, fg=fg or TX,
                        selectbackground=PU, relief="flat", height=h, activestyle="none")
        lb.pack(fill="x", padx=8, pady=4); return lb
    def _fill(self, lb, items):
        lb.delete(0, tk.END)
        for i in items: lb.insert(tk.END, f"  {i}")
    def _btn(self, p, t, cmd, c=None, **kw):
        return tk.Button(p, text=t, command=cmd, font=("Courier New",9,"bold"),
                         bg=c or PU, fg="white", activebackground=AC,
                         activeforeground=BG, relief="flat", cursor="hand2",
                         padx=8, pady=4, **kw)
    def _var_entry(self, p, lbl, row, val=""):
        tk.Label(p, text=lbl, font=("Courier New",9), bg=PNL, fg=DIM).grid(row=row, column=0, sticky="w", pady=2)
        v = tk.StringVar(value=val)
        tk.Entry(p, textvariable=v, font=("Courier New",10), bg=BG, fg=TX,
                 insertbackground=AC, relief="flat", width=13,
                 highlightbackground=BRD, highlightthickness=1).grid(row=row, column=1, sticky="ew", padx=(6,0))
        return v

    def _build(self):
        h = tk.Frame(self, bg=PNL, height=48); h.pack(fill="x", padx=12, pady=(10,6)); h.pack_propagate(False)
        tk.Label(h, text="🏦  Motor de Transacciones Bancarias", font=("Courier New",14,"bold"), bg=PNL, fg=AC).pack(side="left", padx=14)
        body = tk.Frame(self, bg=BG); body.pack(fill="both", expand=True, padx=12, pady=(0,10))
        L = tk.Frame(body, bg=BG, width=330); L.pack(side="left", fill="y", padx=(0,8)); L.pack_propagate(False)
        R = tk.Frame(body, bg=BG); R.pack(side="left", fill="both", expand=True)

        # accounts
        ap = tk.Frame(L, bg=PNL, highlightbackground=BRD, highlightthickness=1); ap.pack(fill="x", pady=(0,8))
        tk.Label(ap, text="▸ CUENTAS", font=("Courier New",10,"bold"), bg=PNL, fg=AC).pack(anchor="w", padx=10, pady=(6,2))
        tk.Frame(ap, bg=BRD, height=1).pack(fill="x", padx=6)
        ai = tk.Frame(ap, bg=PNL); ai.pack(fill="x", padx=10, pady=6)
        self._av = tk.StringVar()
        self._cb = ttk.Combobox(ai, textvariable=self._av, font=("Courier New",9), state="readonly"); self._cb.pack(fill="x")
        self._cb.bind("<<ComboboxSelected>>", lambda _: self._show_bal())
        self._bl = tk.Label(ai, text="Saldo: ---", font=("Courier New",12,"bold"), bg=PNL, fg=AC); self._bl.pack(anchor="w", pady=(4,0))

        # ops notebook
        op = tk.Frame(L, bg=PNL, highlightbackground=BRD, highlightthickness=1); op.pack(fill="x", pady=(0,8))
        tk.Label(op, text="▸ OPERACIONES", font=("Courier New",10,"bold"), bg=PNL, fg=AC).pack(anchor="w", padx=10, pady=(6,2))
        tk.Frame(op, bg=BRD, height=1).pack(fill="x", padx=6)
        nb = ttk.Notebook(tk.Frame(op, bg=PNL)); nb.master.pack(padx=10, pady=6); nb.pack(fill="both")
        ttk.Style().configure("TNotebook", background=PNL)
        for title, color, attrs in [("Depósito", GR, "_d"), ("Retiro", OR, "_w"), ("Transferencia", PU, "_t")]:
            f = tk.Frame(nb, bg=PNL); nb.add(f, text=f"  {title}  "); f.columnconfigure(1, weight=1)
            if attrs == "_t":
                setattr(self, "_t_src", self._var_entry(f, "De:", 0, "CC001"))
                setattr(self, "_t_tgt", self._var_entry(f, "A:",  1, "CC002"))
                setattr(self, "_t_amt", self._var_entry(f, "Monto $:", 2, "100000"))
                self._btn(f, f"Enviar {title} ▶", self._do_transfer, color).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6,0))
            else:
                setattr(self, f"{attrs}_acc", self._var_entry(f, "Cuenta:", 0, "CC001"))
                setattr(self, f"{attrs}_amt", self._var_entry(f, "Monto $:", 1, "500000" if attrs=="_d" else "200000"))
                cmd = self._do_deposit if attrs == "_d" else self._do_withdraw
                self._btn(f, f"Enviar {title} ▶", cmd, color).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6,0))

        # controls
        cp = tk.Frame(L, bg=PNL, highlightbackground=BRD, highlightthickness=1); cp.pack(fill="x")
        tk.Label(cp, text="▸ CONTROL SERVIDOR", font=("Courier New",10,"bold"), bg=PNL, fg=AC).pack(anchor="w", padx=10, pady=(6,2))
        tk.Frame(cp, bg=BRD, height=1).pack(fill="x", padx=6)
        ci = tk.Frame(cp, bg=PNL); ci.pack(fill="x", padx=10, pady=6)
        cr = tk.Frame(ci, bg=PNL); cr.pack(fill="x")
        self._btn(cr,"⏭ Procesar 1",   self._proc1, BL).pack(side="left", expand=True, fill="x", padx=(0,4))
        self._btn(cr,"⏩ Procesar Todo",self._procA, GR).pack(side="left", expand=True, fill="x")
        self._busy = tk.BooleanVar()
        tk.Checkbutton(ci, text="  Servidor lento (acumular cola)", variable=self._busy,
                       font=("Courier New",8), bg=PNL, fg=DIM, selectcolor=BG, activebackground=PNL).pack(anchor="w", pady=(6,0))

        # right panels
        for title, fg, attr, rows in [
            ("▸ COLA  [Queue — FIFO]", AC, "_qlb", 5),
            (f"▸ AUDITORÍA DE FALLOS  [FixedArray — cap {Engine.AUDIT_CAP}]", RD, "_alb", 4),
            ("▸ COMPLETADAS", GR, "_dlb", 9)]:
            pf = tk.Frame(R, bg=PNL, highlightbackground=BRD, highlightthickness=1)
            pf.pack(fill="both" if attr=="_dlb" else "x", expand=attr=="_dlb", pady=(0,8))
            hf = tk.Frame(pf, bg=PNL); hf.pack(fill="x", padx=10, pady=(6,2))
            tk.Label(hf, text=title, font=("Courier New",10,"bold"), bg=PNL, fg=fg).pack(side="left")
            cnt = tk.Label(hf, text="", font=("Courier New",9), bg=PNL, fg=DIM); cnt.pack(side="right")
            setattr(self, attr+"_cnt", cnt)
            tk.Frame(pf, bg=BRD, height=1).pack(fill="x", padx=6)
            setattr(self, attr, self._lbx(pf, rows, fg))

    def _show_bal(self):
        k = self._av.get()
        if k in self.eng.accounts:
            self._bl.config(text=f"Saldo: ${self.eng.accounts[k].balance():,.0f}")

    def _go(self, *a):
        self.eng.submit(*a)
        if not self._busy.get(): self.eng.process_all()

    def _do_deposit(self):
        try: self._go("DEPOSIT", float(self._d_amt.get()), self._d_acc.get().strip().upper())
        except ValueError as e: messagebox.showerror("Error", str(e))

    def _do_withdraw(self):
        try: self._go("WITHDRAW", float(self._w_amt.get()), self._w_acc.get().strip().upper())
        except ValueError as e: messagebox.showerror("Error", str(e))

    def _do_transfer(self):
        try: self._go("TRANSFER", float(self._t_amt.get()), self._t_src.get().strip().upper(), self._t_tgt.get().strip().upper())
        except ValueError as e: messagebox.showerror("Error", str(e))

    def _proc1(self):
        if not self.eng.process_next(): messagebox.showinfo("Cola vacía", "No hay transacciones pendientes.")
    def _procA(self): self.eng.process_all()

    def _refresh(self):
        ids = list(self.eng.accounts.keys())
        self._cb["values"] = ids
        if not self._av.get() and ids: self._av.set(ids[0])
        self._show_bal()
        q = self.eng.queue.to_list()
        self._qlb_cnt.config(text=f"{len(q)} pendientes"); self._fill(self._qlb, q)
        f = self.eng.audit.all()
        self._alb_cnt.config(text=f"{len(f)}/{Engine.AUDIT_CAP}")
        self._fill(self._alb, [f"{t}  ← {t.err}" if t.err else str(t) for t in reversed(f)])
        d = self.eng.done
        self._dlb_cnt.config(text=f"{len(d)} total"); self._fill(self._dlb, list(reversed(d)))

if __name__ == "__main__":
    e = Engine()
    e.add_account("CC001", "Valentina Rios",    4_500_000)
    e.add_account("CC002", "Sebastian Morales", 2_800_000)
    e.add_account("CC003", "Daniela Ospina",    6_100_000)
    App(e).mainloop()
