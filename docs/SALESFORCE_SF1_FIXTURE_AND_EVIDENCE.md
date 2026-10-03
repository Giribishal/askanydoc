# Salesforce SF1 fictional fixture and evidence

Checkpoint: 2026-10-03, Australia/Brisbane. This records observed Developer Edition UI state; it contains no credentials or tokens. The fictional fixture now covers Accounts, Contacts, Cases, Opportunities, Notes, Tasks, an Event, and a Lead. SF1 remains open for the case-closure workflow; runtime Hosted MCP proof belongs to SF2.

## Accounts

Fifty fictional Accounts were verified from the import results and individual record views: Rivergum Logistics was created first; pilot job `750bm000018x4NR` created 2 of 3 rows; second job `750bm000018wDEK` created 46 of 46 submitted rows; `westbrook company`, absent from that job's submitted request, was created manually. The pilot's failed state-picklist row was corrected and included in the second job. Salesforce sample Accounts also exist, so an All Accounts list total is not the fixture count. The reusable 49-row source (excluding Rivergum) is `projects/askanydoc/data/salesforce_sf1_accounts.py` and `salesforce_sf1_accounts.csv`: 10 complete, 10 partial, 10 irregular/mixed, and 19 balanced profiles.

The six Accounts inspected or enriched individually are:

| Account | Salesforce record ID | Verified extra detail |
| --- | --- | --- |
| Amberpoint Labs | `001bm000031SRLVAA4` | Expanded profile; note `Service onboarding context`; corrected Contact Avery Chen; Case `00001026`; follow-up task `Review Amberpoint portal issue`. |
| Rivergum Logistics | `001bm000031S8dFAAS` | Expanded business/contact-channel, address, industry and service fields; note `Warehouse support context`; three linked Cases below; Contacts Maya Patel and Jordan Lee; proposal-stage Opportunity. |
| westbrook company | `001bm000031S94gAAC` | Legacy lowercase name, sparse fields and phone formatting deliberately retained; note `Verify legacy contact details`, task `Confirm Westbrook legacy details`, and a Closed Won Opportunity. This is distinct from the imported `Westbrook Co.` Account. |
| Acacia & Sons | `001bm000031SRLHAA4` | Partial imported fields retained; note `Warehouse address unverified` explains why location and phone remain blank; Contact Sam Torres and an escalated Case. |
| Bayline Services | `001bm000031SNqqAAG` | Legacy phone/account format and other missing fields retained; note `Ticket-name matching context` documents an alias without treating text similarity as account proof; Contact Priya Shah and a Web-origin Case. |
| Bluehaven Utilities | `001bm000031SRL1AAO` | Fuller imported profile plus Customer - Direct, Private, Utilities, Medium priority, Silver SLA, active, two locations; note `Service account context`; Contact Elena Brooks, Case, Opportunity, and Event. |

These are representative uses of fields, notes, Contacts, Cases and task timelines, not a claim that every Salesforce feature or every optional field was populated on all six. No emails were sent, and no sharing or permission settings were changed.

## Rivergum cases

| Fixture | Number | Record ID | Subject | Status | Priority | Origin |
| --- | --- | --- | --- | --- | --- | --- |
| SF1-C01 | `00001027` | `500bm00003BZO62AAH` | Warehouse VPN intermittently disconnects | New | High | Phone |
| SF1-C02 | `00001028` | `500bm00003Bbq5hAAB` | Backup restore evidence requested | Working | Medium | Email |
| SF1-C03 | `00001029` | `500bm00003BcMR3AAN` | Printer queue fix verified; closure pending | Working | Low | Web |

The Account's Related tab showed Cases (3) with these record numbers and links. C01 records an unconfirmed cause and next log review; C02 explicitly says restore evidence is not attached and makes no compliance claim. C03 records a successful synthetic test print. Its creation form and later Status edit offered New, Working and Escalated only, and the inspected record action menu offered no Close action. The case was corrected from `New` to `Working` and its subject changed to say closure is pending. **It is not verified as Closed.** Do not claim a closed/resolved Salesforce case until the supported closure workflow is identified and tested.

## Expanded linked CRM examples — 2026-10-03

The signed-in UI showed save confirmations for five new fictional Contacts: Maya Patel and Jordan Lee (Rivergum), Elena Brooks (Bluehaven, record `003bm000021ehxoAAA`), Priya Shah (Bayline), and Sam Torres (Acacia). Avery Chen already existed under Amberpoint (`003bm000021frl7AAA`). Maya and Elena have fictional `example.com` addresses and phone numbers; Jordan has no phone, Priya has no email, and Sam has neither phone nor email. These deliberate gaps support missing-data questions. Elena was also visible on Bluehaven's Account Related tab. All names and contact channels are synthetic; no contact notification email was selected.

Three more linked Cases were saved and appeared in the Cases Recently Viewed list, bringing the fixture to seven Cases including Amberpoint and Rivergum:

| Number | Account / Contact | Subject | Observed status / priority / origin | Useful distinction |
| --- | --- | --- | --- | --- |
| `00001030` | Bluehaven Utilities / Elena Brooks | Remote sensor readings delayed at two sites | New / Medium / Email | Electronic, Performance; root cause unconfirmed; internal triage comment. |
| `00001031` | Bayline Services / Priya Shah | Invoice contact details need confirmation | Working / Medium / Web | Web name/company populated, email absent; verify billing contact before editing. |
| `00001032` | Acacia & Sons / Sam Torres | Site access outage affecting dispatch handoff | Escalated / High / Phone | Urgent impact still unverified; internal triage comment. |

Four Account-linked Opportunities were saved; the Opportunities Recently Viewed list showed all four names, Account links, stages, and dates:

| Opportunity | Account | Stage / close date | Amount | Record ID and other fields |
| --- | --- | --- | --- | --- |
| Grid sensor maintenance rollout | Bluehaven Utilities | Qualification / 15 Dec 2026 | USD 175,000 | `006bm00000YSjoDAAT`; Existing Customer - Upgrade, Partner Referral, planning estimate. |
| Warehouse connectivity upgrade | Rivergum Logistics | Proposal/Price Quote / 30 Nov 2026 | USD 42,000 | `006bm00000YSjppAAD`; Existing Customer - Upgrade; no signed order. |
| Portal replacement proposal | Amberpoint Labs | Closed Lost / 30 Sep 2026 | USD 65,000 | `006bm00000YSjufAAD`; Existing Customer - Replacement; incumbent retained. |
| Regional router replacement order | westbrook company | Closed Won / 25 Sep 2026 | USD 18,500 | `006bm00000YSkQvAAL`; Existing Customer - Replacement; order `WB26104`, tracking `FXT26092510`, delivery In progress. Won sale does not imply delivery completed. |

Bluehaven's Account timeline displayed the saved internal Event `Bluehaven sensor rollout review` (`00Ubm000007lnUHEAY`), scheduled 9 Oct 2026, 2–3 pm, linked to Elena. A separate unconverted Lead, Noah Ibrahim at fictional Fenwick Transit Systems (`00Qbm00000sq85dEAA`), was saved with status Open - Not Contacted, source Web, rating Cold, Transportation industry, and Sydney/NSW region. The Lead is not an Account or a Contact in the 50-company fixture. No outbound email, campaign send, file attachment, product catalogue entry, permission change, or integration setup was made.

This is a representative fixture for later read-only MCP schema discovery, SOQL/SOSL search, filters, and relationship traversal. The [official SObject Reads documentation](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/sobject-reads.html) describes those tool capabilities, but actual object/field visibility must be tested under the connected Salesforce identity in SF2. This fixture does not imply that every Salesforce object or optional field is populated or exposed.

## Read-only org checks

Observed in this signed-in org's Setup on 2026-10-03:

| Page | Field | Observed value |
| --- | --- | --- |
| Company Information | Organization Edition | Developer Edition |
| Company Information | Salesforce user licenses | 4 total, 2 used, 2 remaining |
| Company Information | API Requests, Last 24 Hours | 4 used, 15,000 max |
| Company Information | API Request Limit per Month entitlement | 450,000 allowance shown; usage not shown in the visible row |
| Storage Usage | Data Storage | 5.0 MB limit, 470 KB used (9%) |
| Storage Usage | File Storage | 20.0 MB limit, 17 KB used (0% rounded) |
| External Client App Manager | Page availability | Accessible; empty state; New External Client App button visible. No app was created. |

An `MCP` Quick Find search did not surface a separate MCP-specific Setup page in the observed tree. This neither proves nor disproves runtime Hosted MCP entitlement. The official documentation and a bounded SF2 runtime test still need to establish the actual server/tools and authorization. No paid plan, trial upgrade, billing form, or entitlement activation was performed here; the org itself reports Developer Edition, but billing status was not independently audited.

## Evidence and remaining gate

- `sf1-all-accounts-visible.png`, `sf1-westbrook-created.png`: Account-list and manually saved record evidence.
- `sf1-amberpoint-case.png`, `sf1-amberpoint-task.png`: linked Case and activity evidence.
- `sf1-bluehaven-enriched.png`, `sf1-rivergum-case-1029.png`: enrichment and final printer-case state.
- `sf1-external-client-app-manager.png`: accessible but empty External Client App Manager.
- `SF1_OPPORTUNITIES_2026-10-03.png`: four Account-linked Opportunity stages in the Salesforce list.
- `SF1_CASES_2026-10-03.png`: seven fixture Cases and their actual statuses in the Salesforce list.
- The signed-in org domain is `orgfarm-cc062a4e4e-dev-ed.develop.lightning.force.com`. The Service app and Account/Case objects were observed. No MCP runtime connection or AskAnyDoc integration has been made.
- Next: assess a supported Case closure workflow without changing org-wide support settings, then perform the separately scoped SF2 read-only Hosted MCP runtime test. The Setup page's availability alone is not runtime proof.
