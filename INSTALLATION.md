# Installation

## Plugin Installation

Amalgam Conductor is intended to be installed as an official-style plugin:

```sh
agy plugin install https://github.com/Baelfyre/amalgam-conductor
```

> **Note:** The current development remote is still `Baelfyre/Amalgamatic-Orchestra` until the repository is officially renamed. You may need to use `https://github.com/Baelfyre/Amalgamatic-Orchestra` for the time being.

## Clone or download manually

If you prefer not to use the plugin manager, you can still clone the repository:

```sh
git clone https://github.com/Baelfyre/Amalgamatic-Orchestra.git amalgam-conductor
cd amalgam-conductor
```

## Install selected skills locally

Copy only the folders you need from `skills/` into the local skill or instruction location supported by your tool. For Codex-compatible environments, install Amalgam Conductor plus selected specialists in the configured local Codex skills directory.

Keep the repository copy separate from unrelated source repositories. If you deliberately use repo-local instructions, copy or reference only the required skill text and follow [LOCAL_ONLY_GUIDE.md](LOCAL_ONLY_GUIDE.md).

## Verify

Run the structure validator, then try the test prompts in [README.md](README.md). Confirm that normal QA routes to Acme Overseer, normal security/privacy review routes to Cipher Meister, and Hidden Dagger remains gated.
