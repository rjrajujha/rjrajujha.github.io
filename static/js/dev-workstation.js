(function () {
  var PROMPT = "raju@dev% ";

  var SNIPPETS = [
    {
      lang: "Python",
      file: "apps/api/routes.py",
      code: [
        "@router.post(\"/events\", status_code=201)",
        "async def ingest_event(payload: EventPayload, service: EventService = Depends()):",
        "    try:",
        "        record = await service.persist(payload)",
        "    except ValidationError as exc:",
        "        raise HTTPException(422, detail=exc.errors) from exc",
        "    await service.enqueue_side_effects(record.id)",
        "    return {\"id\": record.id, \"status\": \"accepted\"}",
      ].join("\n"),
      terminal: {
        command: "python manage.py runserver",
        output: [
          "Watching for file changes with StatReloader",
          "Performing system checks...",
          "System check identified no issues (0 silenced).",
          "Starting development server at http://127.0.0.1:8000/",
          "Quit the server with CONTROL-C.",
        ],
      },
    },
    {
      lang: "JavaScript",
      file: "src/api/client.js",
      code: [
        "export async function fetchProfile(userId, { signal } = {}) {",
        "  const response = await fetch(`/api/users/${userId}`, { signal });",
        "  if (!response.ok) {",
        "    const body = await response.json().catch(() => ({}));",
        "    throw new ApiError(response.status, body.message ?? \"Request failed\");",
        "  }",
        "  return response.json();",
        "}",
      ].join("\n"),
      terminal: {
        command: "npm run dev",
        output: [
          "> portfolio@1.0.0 dev",
          "> vite",
          "VITE v5.4.0  ready in 412 ms",
          "  ➜  Local:   http://localhost:5173/",
        ],
      },
    },
    {
      lang: "Java",
      file: "OrderService.java",
      code: [
        "@Service",
        "public class OrderService {",
        "    public OrderDto createOrder(CreateOrderRequest request) {",
        "        validateInventory(request.getLines());",
        "        var order = orderRepository.save(mapper.toEntity(request));",
        "        eventPublisher.publish(new OrderCreatedEvent(order.getId()));",
        "        return mapper.toDto(order);",
        "    }",
        "}",
      ].join("\n"),
      terminal: {
        command: "mvn spring-boot:run",
        output: [
          "[INFO] Scanning for projects...",
          "[INFO] --- spring-boot:3.2.0:run (default-cli) @ order-service ---",
          "[INFO] Started OrderServiceApplication in 2.841 seconds",
        ],
      },
    },
    {
      lang: "C++",
      file: "src/cache/lru_cache.cpp",
      code: [
        "std::optional<std::string> LruCache::get(std::string_view key) {",
        "    auto it = index_.find(std::string(key));",
        "    if (it == index_.end()) return std::nullopt;",
        "    nodes_.splice(nodes_.begin(), nodes_, it->second);",
        "    return it->second->value;",
        "}",
      ].join("\n"),
      terminal: {
        command: "cmake --build build && ./build/cache_benchmark",
        output: [
          "[ 50%] Building CXX object CMakeFiles/cache_benchmark.dir/src/cache/lru_cache.cpp.o",
          "[100%] Linking CXX executable cache_benchmark",
          "[100%] Built target cache_benchmark",
          "benchmark: 1.2M ops/sec (hit ratio 94%)",
        ],
      },
    },
  ];

  var LANG_COLORS = {
    Python: "text-emerald-300",
    JavaScript: "text-amber-200",
    Java: "text-rose-300",
    Docker: "text-sky-300",
    "C++": "text-sky-300",
  };

  var CODE_TYPING_MIN_MS = 4000;
  var CODE_TYPING_MAX_MS = 5000;
  var TERM_TYPING_MIN_MS = 2200;
  var TERM_TYPING_MAX_MS = 3200;
  var TERMINAL_START_DELAY_MS = 400;

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function initWorkstation(section) {
    var codeRoot = section.querySelector("[data-dev-code-editor]");
    var termRoot = section.querySelector("[data-dev-terminal]");
    if (!codeRoot || !termRoot) {
      return;
    }

    var codeEl = codeRoot.querySelector("[data-dev-code-output]");
    var codeCaret = codeRoot.querySelector("[data-dev-caret]");
    var codeScreen = codeRoot.querySelector(".dev-code-screen");
    var fileEl = codeRoot.querySelector("[data-dev-filename]");
    var langEl = codeRoot.querySelector("[data-dev-lang]");
    var termOutput = termRoot.querySelector("[data-dev-terminal-output]");
    var termCaret = termRoot.querySelector("[data-dev-caret]");

    if (!codeEl || !fileEl || !langEl || !termOutput) {
      return;
    }

    var hasPlayed = false;
    var timers = [];

    function clearTimers() {
      timers.forEach(function (id) {
        window.clearTimeout(id);
      });
      timers = [];
    }

    function schedule(fn, delay) {
      var id = window.setTimeout(fn, delay);
      timers.push(id);
      return id;
    }

    function pickSnippet() {
      return SNIPPETS[Math.floor(Math.random() * SNIPPETS.length)];
    }

    function setCodeHeight(snippet) {
      if (!codeScreen) {
        return;
      }
      var lines = snippet.code.split("\n").length;
      var rem = Math.max(10, lines * 1.55 + 2);
      codeScreen.style.minHeight = rem + "rem";
    }

    function setCodeMeta(snippet) {
      fileEl.textContent = snippet.file;
      langEl.textContent = snippet.lang;
      langEl.className =
        "shrink-0 rounded-full bg-slate-800 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wide sm:px-2 sm:text-[10px] " +
        (LANG_COLORS[snippet.lang] || "text-slate-300");
    }

    function resetTerminalIdle() {
      termOutput.textContent = PROMPT;
      if (termCaret) {
        termCaret.style.display = "none";
      }
    }

    function renderTerminalHtml(terminal, commandText) {
      var html = '<span class="text-emerald-400">' + escapeHtml(PROMPT + commandText) + "</span>";
      if (terminal.output && terminal.output.length) {
        terminal.output.forEach(function (line, index) {
          var tone = index === terminal.output.length - 1 ? "text-slate-300" : "text-slate-500";
          html += "\n<span class=\"" + tone + "\">" + escapeHtml(line) + "</span>";
        });
      }
      html += '\n<span class="text-emerald-400">' + escapeHtml(PROMPT) + "</span>";
      return html;
    }

    function finishTerminal(terminal) {
      termOutput.innerHTML = renderTerminalHtml(terminal, terminal.command);
      if (termCaret) {
        termCaret.style.display = "inline-block";
      }
    }

    function playTerminalTyping(terminal) {
      var commandText = terminal.command;
      var typingTarget = PROMPT + commandText;
      termOutput.textContent = PROMPT;
      if (termCaret) {
        termCaret.style.display = "inline-block";
      }

      var targetMs =
        TERM_TYPING_MIN_MS + Math.floor(Math.random() * (TERM_TYPING_MAX_MS - TERM_TYPING_MIN_MS + 1));
      var index = PROMPT.length;
      var start = performance.now();

      function step(now) {
        var elapsed = now - start;
        var progress = Math.min(1, elapsed / targetMs);
        var nextIndex = Math.max(index, Math.floor(PROMPT.length + progress * commandText.length));
        if (nextIndex > index) {
          termOutput.textContent = typingTarget.slice(0, nextIndex);
          index = nextIndex;
        }
        if (index >= typingTarget.length) {
          finishTerminal(terminal);
          return;
        }
        schedule(function () {
          step(performance.now());
        }, 16);
      }

      schedule(function () {
        step(performance.now());
      }, 120);
    }

    function startTerminal(snippet) {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        finishTerminal(snippet.terminal);
        return;
      }
      playTerminalTyping(snippet.terminal);
    }

    function finishCode(snippet) {
      codeEl.textContent = snippet.code;
      if (codeCaret) {
        codeCaret.style.display = "none";
      }
      schedule(function () {
        startTerminal(snippet);
      }, TERMINAL_START_DELAY_MS);
    }

    function playCodeTyping(snippet) {
      setCodeMeta(snippet);
      setCodeHeight(snippet);
      resetTerminalIdle();
      codeEl.textContent = "";
      if (codeCaret) {
        codeCaret.style.display = "inline-block";
      }

      var text = snippet.code;
      var targetMs =
        CODE_TYPING_MIN_MS + Math.floor(Math.random() * (CODE_TYPING_MAX_MS - CODE_TYPING_MIN_MS + 1));
      var index = 0;
      var start = performance.now();

      function step(now) {
        var elapsed = now - start;
        var progress = Math.min(1, elapsed / targetMs);
        var nextIndex = Math.max(index, Math.floor(progress * text.length));
        if (nextIndex > index) {
          codeEl.textContent = text.slice(0, nextIndex);
          index = nextIndex;
        }
        if (index >= text.length) {
          finishCode(snippet);
          return;
        }
        schedule(function () {
          step(performance.now());
        }, 16);
      }

      schedule(function () {
        step(performance.now());
      }, 280);
    }

    function showStaticSequence(snippet) {
      setCodeMeta(snippet);
      setCodeHeight(snippet);
      codeEl.textContent = snippet.code;
      if (codeCaret) {
        codeCaret.style.display = "none";
      }
      schedule(function () {
        finishTerminal(snippet.terminal);
      }, TERMINAL_START_DELAY_MS);
    }

    function startOnce() {
      if (hasPlayed) {
        return;
      }
      hasPlayed = true;
      var snippet = pickSnippet();
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        showStaticSequence(snippet);
        return;
      }
      playCodeTyping(snippet);
    }

    if (typeof IntersectionObserver !== "undefined") {
      var observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              startOnce();
              observer.disconnect();
            }
          });
        },
        { threshold: 0.15 }
      );
      observer.observe(section);
    } else {
      startOnce();
    }

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        clearTimers();
      }
    });
  }

  document.querySelectorAll("[data-dev-workstation]").forEach(initWorkstation);
})();
