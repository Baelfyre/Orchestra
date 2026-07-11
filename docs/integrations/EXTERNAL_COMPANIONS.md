# External Companions

Orchestra is designed to integrate seamlessly with external workflow companions, particularly **Ponytail** and **Caveman**. However, it is important to understand that these tools are strictly **optional external integrations**, not bundled dependencies or governed components of the Orchestra repository itself.

## Separation of Ownership

### What Orchestra Owns
* **Governance**: The Steward, The Governor, and Arbiter.
* **Orchestration**: Conductor and the routing logic.
* **Specialist Design**: The domain-specific skills (Clockwork, Cloak, Scribe, Weaver, Chronicler, Overseer, Cipher, Dagger).
* **Validation**: Centralized structure, manifest verification, and optional repository safety guardrails.
* **State Locking**: Concurrency protection within the workspace.

### What Ponytail Owns
* **Implementation Execution**: Code navigation, syntax edits, refactoring execution, and diff generation.
* **Minimal Safe Edits**: Determining the smallest code-level change to satisfy a specialist's design.
* *Note: Ponytail relies entirely on the design parameters and boundaries passed to it by Orchestra's specialists. It does not enforce its own governance rules.*

### What Caveman Owns
* **Output Compression**: Converting verbose AI chat outputs into compact, token-efficient formats.
* **Communication Protocol**: Enforcing the default terse response style across the workflow.
* *Note: Caveman alters the tone and length of the output. It does not evaluate safety or compliance.*

## What Is Not Guaranteed

* **Component Updates**: Ponytail and Caveman are maintained in their respective external repositories. Orchestra does not guarantee that breaking changes in those external tools will automatically be supported without user configuration.
* **Full Enforcement**: If you bypass Conductor and invoke Ponytail directly, Orchestra's governance and validation layers are bypassed.
* **Security Scanning**: Ponytail edits code freely; it is the responsibility of Orchestra's guardrails (if enabled) or CI pipeline to detect safety issues, not Ponytail.

## Using Orchestra Without Companions

You are not required to use Ponytail or Caveman. 

* **Without Ponytail**: When a specialist (like Clockwork or Cipher) provides a design or fix plan, you can implement the changes yourself, or use a different code-generation agent provided by your IDE.
* **Without Caveman**: If you omit Caveman from your workflows, Orchestra and its specialists will simply output longer, conversational responses.

To run purely without companions, simply invoke `/conductor` (or your host's equivalent trigger) without chaining other tools in your prompts.

## Vetting Companion Compatibility

Before integrating an external companion into your Orchestra workflow:
1. **Check the Repository**: Review the companion's latest release notes and README.
2. **Run a Safe Prototype**: Test the companion within an `Ideation` or `Prototype` mode task to ensure it understands Conductor's routing instructions.
3. **Verify Handoff**: Ensure that the companion properly respects Arbiter's continuity checks and does not blindly overwrite files without validation.
