# Uncharted collection and playtime sorting — 2026-10-19

1. Diagnose using read-only FTP and existing private captures. Preserve original
   state, identifiers, imports and console binaries. No payload test is needed.
2. Verify collection membership from the installed application's param.sfo and
   checksummed npbind.dat, with two equal bounded reads. Record only application/
   set IDs and evidence hashes in Git; keep publisher binaries private.
3. Add an explicitly verified collection catalog and group existing owned rows
   within the same console profile. Keep original trophy-set/trophy identities,
   viewer-relative secret privacy, hiding and one copy of each activity. Missing
   component state is not inferred from publisher definitions.
4. Show the collection's imported component trophies on its card/dialog. Add
   descending recorded-hours and recorded-session sorts in all interface languages,
   using the same eligible sessions and shared totals as the displayed counts.
   User additionally requested subgroups: expandable games open individual
   trophy/session views. Preserve a separate collection-level time bucket;
   only exact component application sessions can supply a game's own time.
5. Add API ownership/privacy/replay/multiple-set and browser sorting/grouping
   regressions. Build/run the local stack; document exact results and deployment
   requirements. The separate hosted service still needs the user's rebuild.

Confirmed source: `/system_data/priv/appmeta/CUSA02344/param.sfo` identifies
CUSA02344, EP9000-CUSA02344_00-UNCHARTEDTRILOGY, APP_VER 01.02. Its 1,300-byte
npbind.dat has version 1, three 384-byte entries, a valid trailing SHA1 and the
sets NPWR09798_00, NPWR09799_00 and NPWR09801_00. Both files match second reads.
Initially only NPWR09798_00 had observed per-profile state. User then launched
Uncharted 2/3; FTP now also lists their profile images and supplied screenshots
show the imported 53/59-trophy lists. This establishes collection
membership, not equivalence with component CUSA03280 or component playtime.

Use a reviewed catalog for this server-only repair so already imported records
are corrected without console execution or a new credential-bearing protocol.
Other applications/regions are not inferred. A future generic binding-upload
protocol must validate its own metadata and be independently console-tested.
