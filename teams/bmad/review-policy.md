# Optional evidence-based BMad build review

Apply only when the user requests this review policy. Ordinary Plex setup/refresh
does not change BMad customization. BMad and its project runtime must already work.

1. Read the active installed `bmad-build/customize.toml` and project
   `_bmad/custom/bmad-build.toml` and `bmad-build.user.toml`, if present. Confirm
   keyed review-layer overrides by `id` are supported and `blind-hunter` exists in
   both `workflow.review_layers` and `workflow.oneshot_review_layers`. Unsupported
   versions are blockers; do not modify plugin caches or upstream files.
2. Preview the two recipes from `<plugin-root>/teams/bmad/bmad-build.toml`.
   They remove the finding quota while preserving independent review. Other layers,
   route selection and human gates stay under the installed workflow's control.
3. If no shared project override exists, copy the asset to
   `_bmad/custom/bmad-build.toml`. Otherwise back up that file outside runtime
   discovery, then replace only the matching `blind-hunter` instruction fields (or
   add the tables if absent), retaining other fields and unrelated settings. Do not
   blindly append duplicate tables.
   Preserve personal `.user.toml` settings; if they override these recipes, report
   the conflict rather than silently changing the user's policy.
4. Follow the installed build skill's rendering command once. Inspect its printed
   snapshot: the full route must retain its other layers, the oneshot route must
   retain its own layer set, and both blind-hunter recipes must allow zero findings.
   Report actual effective recipes; a successful TOML parse alone is insufficient.

Keep the shared override in project version control if desired. Plugin updates do
not refresh it automatically: compare the asset and installed BMad schema on a
requested policy update. To undo, restore the backup or remove only these two
overrides, then render a new snapshot; do not edit an immutable existing snapshot.
