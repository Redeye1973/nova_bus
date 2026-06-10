# N1 — Monitor ziet alleen gemounte paden (gedocumenteerd, fix uitgesteld)

**Status:** gedocumenteerd in fase 8, bewust **niet** gefixt (cosmetisch, geen blokker).
**Herkomst:** fase 7 sabotage-ronde 3a (`L:\ZZZZZ ZZ 31-05-2026\nova_betrouwbaar\fase7\SABOTAGE_RAPPORT.md`, N1).

## Probleem

De Monitor (agent 11, poort 8111) draait in Docker en verifieert per sweep een
steekproef van file-proofs (bestaat + sha256). Hij kan alleen paden lezen die in de
container gemount zijn (`/nova_status`, `/nova_shared`, `/nova_state`, `/config`,
game-output-mounts). Een file-proof dat naar een **niet-gemount pad** wijst
(bv. `C:\...` of een willekeurig L:-pad) leest de Monitor als `file_not_found` —
hij kan daar een **hash-mutatie niet van afwezigheid onderscheiden**.

## Waarom dit nu acceptabel is

- Game-assets (de proofs die ertoe doen) staan onder de gemounte
  `L:\ZZZ ZZ NOVA GAME OUTPUT\...` — dáár werkt de hash-check aantoonbaar
  (fase 7, ronde 3a: hash_mismatch correct geflagd binnen sweeps).
- Sinds fase 8 FIX 3 worden proofs bij `/part-update` óók host-side geverifieerd
  (versheid + taak-binding + bestaan/hash via agent 41, die als host-proces alle
  paden kan lezen). De container-blindheid is daarmee geen primaire verdediging meer.

## Fix-voorstel (later)

1. Host-side periodieke her-verificatie van file-proofs (klein script of taak in
   agent 41/Dale die dezelfde steekproef doet als de Monitor maar met host-zicht), of
2. de relevante roots expliciet read-only mounten in de Monitor-container en
   `NOVA_PATH_MAP` uitbreiden, zodat container-paden 1-op-1 vertaald worden.

Beide opties zijn klein; optie 1 raakt geen compose/containers en heeft de voorkeur.
