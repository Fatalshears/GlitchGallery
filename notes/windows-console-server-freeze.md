Here is the markdown document — save it wherever suits you (e.g. `plans/windows-console-server-freeze.md`):

```markdown
# Windows Console QuickEdit — Server Freeze on Multi-Client Access

## Summary

On Windows, any server process that **writes to the console while sharing a
PowerShell / cmd window** can be completely frozen by a user clicking in that
window. All connected clients stall until the user releases the mouse button.

---

## Symptoms

- Server works fine with one client; hangs intermittently with two or more.
- Selecting text in the server's console window (or simply clicking it) pauses
  all client responses.
- Releasing the selection (pressing Ctrl+C, clicking elsewhere) instantly
  unblocks all pending requests.
- No error messages in logs — the process is simply paused at an OS level.

---

## Root Cause

**Windows QuickEdit Mode** is enabled by default in every PowerShell and
cmd.exe window. When a user clicks in the window to select text, Windows
calls `ReadConsoleInput` internally and **pauses all writes to that console
handle** system-wide — across every process that shares the same console.

The freeze happens when ALL of these are true:

1. The server process shares the parent PowerShell console
   (`Start-Process -NoNewWindow`, `os.system(...)`, running in foreground, etc.)
2. The server writes log output to stdout/stderr synchronously
3. Those writes happen on a thread that is also responsible for handling
   client requests (e.g. the asyncio event loop, the main HTTP thread)

When condition 3 is true, a single blocked `write()` syscall suspends the
thread that drives all I/O multiplexing — zero requests are processed.

---

## Affected Stacks

This affects any server launched from a Windows console without `-NoNewWindow`
redirection or piping, including:

| Stack | Common scenario |
|---|---|
| Python / uvicorn / FastAPI | Launched from PowerShell with `-NoNewWindow` |
| Node.js / Express | `node server.js` from PowerShell |
| Go / net/http | `go run main.go` from cmd |
| .NET / Kestrel | `dotnet run` from PowerShell |
| Ruby / Puma | `rails server` from PowerShell |
| Java / Tomcat / Spring Boot | `mvn spring-boot:run` from cmd |
| Anything using `subprocess` | Child process inherits parent console handle |

---

## Fixes

### Fix 1 — Disable QuickEdit in the launcher script (PowerShell)

Call `SetConsoleMode` via Win32 P/Invoke before starting the server processes.
This is the most reliable fix: it prevents the freeze regardless of how the
server writes logs.

```powershell
# Disable QuickEdit mode — prevents mouse clicks from pausing console output.
# Safe to add to any start.ps1 / launcher script.
try {
    $qeSrc = @'
using System; using System.Runtime.InteropServices;
public static class QuickEditDisabler {
    const int  STD_INPUT_HANDLE   = -10;
    const uint ENABLE_QUICK_EDIT  = 0x0040;
    [DllImport("kernel32.dll")] static extern IntPtr GetStdHandle(int h);
    [DllImport("kernel32.dll")] static extern bool   GetConsoleMode(IntPtr h, out uint m);
    [DllImport("kernel32.dll")] static extern bool   SetConsoleMode(IntPtr h, uint m);
    public static void Disable() {
        IntPtr h = GetStdHandle(STD_INPUT_HANDLE);
        uint m; GetConsoleMode(h, out m);
        SetConsoleMode(h, m & ~ENABLE_QUICK_EDIT);
    }
}
'@
    Add-Type -TypeDefinition $qeSrc -Language CSharp
    [QuickEditDisabler]::Disable()
    Write-Host "Console QuickEdit disabled." -ForegroundColor Green
} catch {
    Write-Host "Could not disable QuickEdit: $($_.Exception.Message)" -ForegroundColor Yellow
}
```

Equivalent in **cmd.exe / batch** (reg key, requires restart):
```batch
reg add "HKCU\Console" /v QuickEdit /t REG_DWORD /d 0 /f
```

---

### Fix 2 — Never write logs on the event-loop / request-handling thread

Even with QuickEdit disabled, it is good practice to ensure log writes do not
block the thread that drives client I/O. Route all log output through an
async-safe queue that drains on a dedicated background thread.

#### Python (`logging` standard library)

```python
import logging
import logging.handlers
import queue
import sys

_log_queue    = queue.SimpleQueue()
_console_h    = logging.StreamHandler(sys.stderr)
_console_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s — %(message)s"))
_log_listener = logging.handlers.QueueListener(_log_queue, _console_h, respect_handler_level=True)
_log_listener.start()

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.handlers.QueueHandler(_log_queue)],
    force=True,
)
```

`QueueHandler` enqueues records instantly (non-blocking). `QueueListener` drains
the queue from a daemon thread. The event loop / request thread never blocks on
a console write.

#### Node.js (Winston example)

```js
const { createLogger, transports } = require('winston');
// winston's File/Console transports write in a background stream — safe by default.
// Avoid console.log() in hot paths; use a proper logger.
const logger = createLogger({ transports: [new transports.Console()] });
```

#### Go

```go
// Use a buffered writer or a logging library (zap, zerolog) that
// writes asynchronously. Never log.Println() on the goroutine serving requests.
import "go.uber.org/zap"
logger, _ := zap.NewProduction()  // zap is async-safe
```

---

### Fix 3 — Redirect stdout/stderr away from the console entirely

Start the server with output redirected to a file or pipe. The process no
longer holds a console handle and QuickEdit cannot affect it.

```powershell
# PowerShell: redirect both streams to a log file
Start-Process $Python `
    -ArgumentList @("-m", "uvicorn", "app.main:app") `
    -RedirectStandardOutput "logs\uvicorn.log" `
    -RedirectStandardError  "logs\uvicorn.err" `
    -NoNewWindow -PassThru
```

Downside: you can no longer see live output in the terminal.
Use `Get-Content logs\uvicorn.log -Wait` to tail the log.

---

## Diagnostic Checklist

If a Windows server freezes under concurrent clients and releasing mouse focus
fixes it, work through this list:

- [ ] Is the server process sharing the parent console? (`-NoNewWindow`, foreground run)
- [ ] Is QuickEdit mode enabled? (default: yes in PowerShell / cmd)
- [ ] Are log writes happening on the main request-handling thread?
- [ ] Is the process blocked on a `write()` / `WriteConsoleA` syscall? (use
      Process Explorer → Threads → right-click → Stack to confirm)

---

## References

- [SetConsoleMode — Win32 API (learn.microsoft.com)](https://learn.microsoft.com/en-us/windows/console/setconsolemode)
- [Python QueueHandler / QueueListener docs](https://docs.python.org/3/library/logging.handlers.html#queuehandler)
- Windows Internals — Console subsystem: `conhost.exe` manages the console
  buffer; QuickEdit sets `ENABLE_QUICK_EDIT_MODE` (bit 6) in the input mode
  flags, blocking `WriteFile` calls to the output handle while selection is active.
