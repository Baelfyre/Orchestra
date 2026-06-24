<div align="center">
  <img src="assets/logo/orchestra-of-amalgamation.png" alt="Amalgamatic Orchestra" width="280" />
  <h1>Amalgam Conductor Ecosystem</h1>
  <p><strong>The routing, implementation, and communication layer for AI workflow automation.</strong></p>
</div>

---

## 🎯 Purpose

Amalgam Conductor coordinates AI-assisted software engineering. Instead of a single messy prompt, tasks are routed through a highly disciplined trifecta of orchestration, implementation, and communication, backed by domain specialists.

## 🏗️ The Ecosystem Trinity

The core engine relies on three distinct layers working together to prevent token bloat and over-engineering:

1. **[Amalgam Conductor](skills/amalgam-conductor/SKILL.md) (Orchestrator)** 
   - Defines the task boundary. Decides *what* gets built and *who* builds it.
   - Prevents sequencing errors, unauthorized actions, and overlapping reviews.
2. **[Ponytail](https://github.com/Baelfyre/ponytail) (Implementation Engine)**
   - The lazy senior developer. Writes the absolute minimum code required.
   - Uses native features and standard libraries before adding dependencies. No architecture redesigns.
3. **[Caveman](https://github.com/Baelfyre/caveman) (Global Protocol)**
   - The communication standard. Strips out conversational filler and formatting bloat.
   - Outputs only what matters: actionable code, skipped steps, and required context.

---

## 🧩 The Specialists

When Amalgam Conductor identifies a cross-domain feature, it routes the task to the appropriate specialist.

| Specialist | Use Case | Avoid When |
| :---: | :--- | :--- |
| <img src="assets/icons/amalgam-conductor.png" width="60" /><br>**Amalgam Conductor** | Routing, overlap control, token efficiency | A single obvious specialist suffices |
| <img src="assets/icons/clockwork-meister.png" width="60" /><br>**Clockwork Meister** | OOP/Layered architecture, system design, refactoring | Modifying UI or writing docs |
| <img src="assets/icons/cloak-meister.png" width="60" /><br>**Cloak Meister** | UI/UX, layout, components, accessibility | DB or system-diagram ownership |
| <img src="assets/icons/meister-chronicler.png" width="60" /><br>**Meister Chronicler**| DB schema, migrations, SQL, constraints | UI review |
| <img src="assets/icons/scribe-meister.png" width="60" /><br>**Scribe Meister** | Documentation, READMEs, technical writing | Inventing technical facts |
| <img src="assets/icons/meister-weaver.png" width="60" /><br>**Meister Weaver** | UML, ERD visuals, workflow diagrams | DB semantics without source |
| <img src="assets/icons/acme-overseer.png" width="60" /><br>**Acme Overseer** | QA, tests, release readiness, regression | Destructive pressure testing |
| <img src="assets/icons/cipher-meister.png" width="60" /><br>**Cipher Meister** | Security/privacy evidence, auth, secrets | Offensive testing |
| <img src="assets/icons/hidden-dagger.png" width="60" /><br>**Hidden Dagger** | Approved destructive/resilience testing | Unauthorized testing |

See [SKILL_INDEX.md](SKILL_INDEX.md) for the full skill index and expected output formats.

---

## 🚦 Recommended Workflow

1. **Single-Domain Tasks**: Route directly to the executing specialist (e.g., `Ponytail` for code, `Cloak Meister` for UI).
2. **Cross-Domain Features**: Start with `Amalgam Conductor`. It will sequence the required specialists in execution order.
3. **Communication**: All output defaults to the `Caveman` protocol. 
4. **Implementation**: Code generation defaults to `Ponytail` logic (shortest path, stdlib first).

---

## 🚀 Installation

Install the ecosystem directly into your supported AI environment:

```sh
agy plugin install https://github.com/Baelfyre/amalgam-conductor
agy plugin install https://github.com/Baelfyre/ponytail
agy plugin install https://github.com/Baelfyre/caveman
```

For manual setup, copy the respective `skills/` folders into your AI's instruction directory. See [INSTALLATION.md](INSTALLATION.md) for details.

---

## 🛡️ Git Safety & Compatibility

- **Markdown-first**: Instructions are portable across tools (Codex, VS Code, Antigravity, Claude Code).
- **Safety**: Keep experimental AI instruction files isolated. Use `.git/info/exclude` to prevent committing them to your production repositories unless explicitly intended.

**Manifest consistency check:**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-manifest.ps1
```

---

## ⚠️ DISCLAIMER

Please read the [DISCLAIMER.md](DISCLAIMER.md) before using this ecosystem in real-world applications or production environments.
