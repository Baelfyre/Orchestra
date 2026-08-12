# CI, Browser, Device, and Performance Matrix Guide

## CI Matrix Design

Derive dimensions from supported contracts and risk: operating system, runtime, architecture, dependency/provider version, database, locale, browser engine, device class, feature flag, or deployment mode. Use pairwise or risk-based selection when a full Cartesian matrix adds cost without unique evidence.

For every cell record trigger, exact revision, environment image/tool versions, dependencies, shard, cache key, command, timeout, retry policy, artifacts, required/advisory status, and skipped/cancelled visibility. A missing or cancelled required cell is not green evidence.

Retries must preserve the first failure and attempt count. Caches are performance aids, not evidence sources; validate cache keys and provide an uncached diagnostic path.

## Browser and Device Coverage

Map supported browser engines and versions, viewport classes, input modes, pixel density, reduced-motion/contrast settings, network capability, and assistive-technology needs to product support and usage risk. Emulation does not replace real-device evidence when hardware, browser chrome, keyboard, touch, media, camera, GPU, or performance behavior is material.

Combine Cloak's static accessibility/UI contract with rendered evidence for focus, keyboard, pointer/touch, scroll, responsive layout, overlays, console errors, and supported themes. One browser or viewport cannot establish matrix parity.

## Performance Acceptance

Define workload model, dataset, environment, warm-up, steady window, repetitions, concurrency, caching state, percentile latency, throughput, error rate, resource limits, baseline tolerance, and abort conditions before execution.

Report distributions and confidence-affecting noise, not averages alone. Distinguish statistical change from practical regression and confirm the load generator is not saturated. Performance evidence is valid only for the tested envelope and does not authorize production load. Dagger owns explicitly authorized pressure scenarios; Clockwork and Chronicler interpret architecture/persistence causes; Overseer owns acceptance gates.
