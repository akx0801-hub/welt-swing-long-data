# Mapping Evidence Acquisition v0.42

v0.42 records real, URL-backed primary and provider research for the 239 v0.39 mapping cases. Identity fields are frozen; this stage creates candidates only and never applies mappings or downloads prices.

Research is resumable through `Research_Status` (`NOT_STARTED`, `RESEARCHED`, `PARTIAL`, `BLOCKED`) and the output checkpoint. HIGH requires primary and provider URLs, a proposed symbol, and no unresolved identity/share-class ambiguity. The validator enforces the 239-row split, frozen identity, decision/confidence vocabularies, and candidate collision review.

Workflow is manual-dispatch only and validates committed evidence; web research happens before commits in the controlled Cloud Browser.
