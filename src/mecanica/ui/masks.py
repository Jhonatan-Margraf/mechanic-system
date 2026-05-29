"""Input masks for CPF and phone number fields.

Root cause of the "digits appear in wrong order" bug:
    tkinter's StringVar write-trace fires BEFORE the cursor moves to the new
    position after a key press. If we read the cursor position at that moment,
    we get the pre-keystroke position and end up placing the cursor before the
    newly typed digit — so the next keystroke inserts text there instead of
    after it.

Fix: schedule the actual mask application with after(0, ...) so it runs after
the current event loop iteration, at which point the cursor is already correct.
A _pending guard acts as a per-field debounce so rapid keystrokes don't
schedule multiple concurrent applications.
"""

import re

# Guards against re-entrant calls triggered by var.set() inside the mask
_mascara_ativa: dict = {}

# Debounce: tracks fields that already have a pending after(0) scheduled
_pending: dict = {}


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _fmt_cpf(digits: str) -> str:
    d = digits[:11]
    if len(d) > 9:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) > 6:
        return f"{d[:3]}.{d[3:6]}.{d[6:]}"
    if len(d) > 3:
        return f"{d[:3]}.{d[3:]}"
    return d


def _fmt_telefone(digits: str) -> str:
    d = digits[:11]
    if len(d) > 6:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) > 2:
        return f"({d[:2]}) {d[2:]}"
    return d


# ---------------------------------------------------------------------------
# Cursor restoration
# ---------------------------------------------------------------------------

def _restaurar_cursor(entry, fmt: str, digits_before: int) -> None:
    """Place the cursor after the `digits_before`-th digit in the formatted string."""
    count = 0
    for i, ch in enumerate(fmt):
        if count == digits_before:
            try:
                entry._entry.icursor(i)
            except Exception:
                pass
            return
        if ch.isdigit():
            count += 1
    # digits_before >= total digits → cursor goes to end
    try:
        entry._entry.icursor(len(fmt))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Generic mask applicator
# ---------------------------------------------------------------------------

def _make_mask(formatter):
    """
    Return a pair (apply_fn, _run_fn) for the given formatter.

    apply_fn  — bind to trace_add("write", ...)
    Uses after(0, ...) so the cursor position is already correct when we read it.
    """

    def apply_fn(var, entry=None, *args):
        vid = id(var)
        if _mascara_ativa.get(vid):
            return

        # If a mask application is already scheduled for this field, skip —
        # the pending one will pick up the latest var value when it runs.
        if _pending.get(vid):
            return

        if entry is None:
            # No widget reference: apply inline (no cursor to manage)
            _mascara_ativa[vid] = True
            try:
                raw = re.sub(r"\D", "", var.get())
                fmt = formatter(raw)
                if var.get() != fmt:
                    var.set(fmt)
            finally:
                _mascara_ativa[vid] = False
            return

        _pending[vid] = True

        def _run():
            _pending.pop(vid, None)
            _mascara_ativa[vid] = True
            try:
                # Cursor is now in the correct post-keystroke position
                cursor_pos = None
                try:
                    cursor_pos = entry._entry.index("insert")
                except Exception:
                    pass

                current = var.get()
                raw = re.sub(r"\D", "", current)
                fmt = formatter(raw)

                if current == fmt:
                    return

                digits_before = None
                if cursor_pos is not None:
                    digits_before = len(re.sub(r"\D", "", current[:cursor_pos]))

                var.set(fmt)  # triggers trace again, blocked by _mascara_ativa

                if digits_before is not None:
                    _restaurar_cursor(entry, fmt, digits_before)
            finally:
                _mascara_ativa[vid] = False

        try:
            entry.after(0, _run)
        except Exception:
            # Fallback if after() is unavailable (e.g. widget not yet displayed)
            _pending.pop(vid, None)
            _mascara_ativa[vid] = True
            try:
                raw = re.sub(r"\D", "", var.get())
                fmt = formatter(raw)
                if var.get() != fmt:
                    var.set(fmt)
            finally:
                _mascara_ativa[vid] = False

    return apply_fn


def _fmt_ano(digits: str) -> str:
    return digits[:4]


aplicar_mascara_cpf      = _make_mask(_fmt_cpf)
aplicar_mascara_telefone = _make_mask(_fmt_telefone)
aplicar_mascara_ano      = _make_mask(_fmt_ano)
