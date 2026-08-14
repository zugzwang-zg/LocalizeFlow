# Packaging hard-gate validation

Validation date: 2026-08-14  
Schema: `data/products/packaging_facts.json` v1.0.0

## Scope

- Five synthetic SKUs, two markets, and three content types: 30 deterministic enhanced outputs.
- Pre-generation availability gate and post-generation/post-edit text gate.
- Container type, material, capacity, dispenser, closure, inner lid, transparency, outer container, and kit component fields where evidence exists.
- Missing fields use `unknown`; they are never inferred.

## Result

- 30/30 frozen enhanced outputs passed the packaging hard gate.
- Verified `60 mL aluminum tube` claims for `MV-HAND-001` now pass against `MV-HAND-001-F030`.
- Regression cases for wrong material, wrong container, unknown-field claims, wrong capacity, and mixed-SKU packaging are blocked.
- The same checker runs after manual edits; an edit from `aluminum tube` to `glass jar` is blocked.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_packaging_checker.py tests/test_demo_service.py -q
```

The fixtures are synthetic evaluation materials. A pass means consistency with the frozen project facts, not platform or legal approval.
