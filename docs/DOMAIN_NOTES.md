# Domain Notes: DABstep payments analytics

Written in our own words from `manual.md` (v2.1) and `payments-readme.md` (DABstep dataset,
revision `cebda164`, CC BY 4.0), plus checks run against the context files on 2026-10-12.
Sections marked **Observed** come from inspecting the data, not from the docs. Where the docs and
the data disagree, the data wins and the gap is noted, because those gaps are where agents fail.

## 1. The world being modelled

A payments processor handles card payments for merchants. Each payment is authorised, then
captured and settled. The processor charges the merchant a **fee per transaction**, set by a
rule table (`fees.json`). Many questions boil down to: *which rule applies to this transaction,
and what does it cost?*

Files:

| File | What it holds |
|---|---|
| `payments.csv` | 138,236 synthetic transactions, all in **2023**, for **5 merchants** |
| `merchant_data.json` | 30 merchants: capture delay, acquirer banks, MCC, account type |
| `fees.json` | 1,000 fee rules (`ID` 1–1000) |
| `merchant_category_codes.csv` | MCC → description (has a junk unnamed index column) |
| `acquirer_countries.csv` | acquirer bank → country code (also has an index column) |
| `manual.md` | the business rules; most of it is generic advice, the key part is §5 |

## 2. Transactions (`payments.csv`)

- One row per payment; `psp_reference` is the ID.
- **Time** is split into `year`, `day_of_year`, `hour_of_day`, `minute_of_hour`. There is no date
  column. Months must be derived from `day_of_year` (2023 is not a leap year, so day 32 = Feb 1,
  day 60 = Mar 1, etc.).
- **Amount**: `eur_amount`, already in euros.
- **Countries**: `ip_country` (where the shopper was), `issuing_country` (where the card was
  issued), `acquirer_country` (where the acquiring bank is).
- **Flags**: `is_credit` (credit vs debit), `has_fraudulent_dispute` (the issuer reported fraud),
  `is_refused_by_adyen`.
- `shopper_interaction`: `Ecommerce` or `POS` (in store).
- `aci`: one letter A–G (see §5).
- **Observed:** card schemes are `GlobalCard`, `NexPay`, `SwiftCharge`, `TransactPlus`, not
  the "MasterCard, Visa, Amex, Other" the readme lists. Acquirer countries are `NL, US, IT, FR,
  GB`, not the readme's list. Trust the data.

## 3. Merchants (`merchant_data.json`)

Each merchant has:
- `account_type`: one letter. R = enterprise retail, D = enterprise digital, H = enterprise
  hospitality, F = platform franchise, S = platform SaaS, O = other.
- `merchant_category_code` (MCC): a 4-digit industry code from the card networks.
- `capture_delay`: how many days until capture. **Observed:** values are `"1"`, `"2"`, `"7"`,
  `"immediate"`, `"manual"`. Fee rules use *buckets* instead (`<3`, `3-5`, `>5`, `immediate`,
  `manual`), so a merchant's number must be mapped to a bucket before matching (1, 2 → `<3`;
  7 → `>5`).
- `acquirer`: a list of acquiring banks; their countries are in `acquirer_countries.csv`.

Only 5 of the 30 merchants have transactions in `payments.csv`.

## 4. The fee formula

For one transaction:

    fee = fixed_amount + rate * eur_amount / 10000

`fixed_amount` is euros per transaction; `rate` is an integer in units of 1/10,000 (basis points
times 100, effectively). A rule with `rate = 19` adds 0.19% of the amount.

## 5. Matching a fee rule

A rule applies to a transaction when **every** field of the rule matches. Each field draws its
value from either the transaction or the merchant:

| Rule field | Compared with | Source |
|---|---|---|
| `card_scheme` | scheme name, exact | transaction |
| `account_type` | merchant's type is in the list | merchant |
| `merchant_category_code` | merchant's MCC is in the list | merchant |
| `capture_delay` | merchant's delay, bucketed | merchant |
| `monthly_volume` | merchant's total € volume in that calendar month | computed |
| `monthly_fraud_level` | merchant's fraud ratio in that calendar month | computed |
| `is_credit` | credit vs debit | transaction |
| `aci` | transaction ACI is in the list | transaction |
| `intracountry` | issuing country == acquirer country | transaction |

**"Applies to all" values.** The manual says a `null` field matches every value. **Observed:**
scalar fields use `null`, but list fields (`account_type`, `merchant_category_code`, `aci`) use an
**empty list `[]`** for "all", and never `null`. 720 of 1,000 rules have `account_type: []`. Code
that only checks `is None` will silently wrongly exclude most rules.

**`intracountry`** is stored as `1.0` / `0.0` / `null` (floats, not booleans). Domestic means the
issuer country equals the *acquirer* country. The shopper's IP country is irrelevant here.

**Monthly volume and fraud** are always computed over **natural calendar months** (1st to last
day), never rolling windows. Buckets: volume `<100k`, `100k-1m`, `1m-5m`, `>5m` (euros); fraud
`<7.2%`, `7.2%-7.7%`, `7.7%-8.3%`, `>8.3%`.

**Fraud rate definition** (manual §7): fraudulent **volume** ÷ total **volume**, i.e. sum of
`eur_amount` where `has_fraudulent_dispute` is true over the sum of all `eur_amount`. Not a count
of transactions. Questions sometimes ask for a count-based rate explicitly; read the wording.

General price direction stated by the manual (useful as a sanity check, not a rule):
- faster capture costs more;
- higher fraud costs more;
- higher volume costs less;
- credit costs more than debit;
- international costs more than domestic.

## 6. ACI (Authorization Characteristics Indicator)

How the transaction reached the acquirer:

| ACI | Meaning |
|---|---|
| A | card present, not authenticated |
| B | card present, authenticated |
| C | tokenised card on a mobile device |
| D | card not present, card on file |
| E | card not present, recurring bill |
| F | card not present, 3-D Secure |
| G | card not present, no 3-D Secure |

**Observed** frequencies: D 49,642 · F 29,266 · G 25,463 · E 21,468 · C 5,807 · A 3,837 ·
B 2,753.

A common question type: "to which ACI should fraudulent transactions be moved to pay the lowest
fees?" Answer it by re-pricing those transactions under each candidate ACI and comparing totals.

## 7. MCC

Four-digit code. The manual says the first two digits are the category and the last two the
subcategory. Note: the manual's own examples are wrong (it calls 5451 "Automated Fuel
Dispensers" and 5812 "Automotive Parts"). Always look descriptions up in
`merchant_category_codes.csv`, never in the manual's prose.

## 8. Fraud, fines and the rest of the manual

- §6 (PIN attempts: 3 tries, then a temporary block) and §7.4 (PCI DSS non-compliance: €5,000 to
  €100,000 per month) are the only concrete numbers outside §5.
- The manual defines **no "high-fraud fine"** threshold. A dev task asks whether a merchant is "in
  danger of a high-fraud rate fine"; its answer is `Not Applicable`. Lesson: when the documents
  don't define something, the right answer is `Not Applicable`, not a guess.
- §5.1.x (local acquiring, choosing an ACI, volume pricing, avoiding downgrades) is generic
  advice; it explains *why* the fee table is shaped as it is but adds no rules.

## 9. Traps checklist (for prompts, C1 field cards and C2 validators)

1. List fields use `[]` for "all"; scalar fields use `null`.
2. `intracountry` compares issuer vs **acquirer** country, as 1.0 / 0.0.
3. Merchant capture delay is in days; rules use buckets.
4. Months come from `day_of_year` in non-leap 2023.
5. Fraud rate is by volume, unless the question says otherwise.
6. Scheme and country names in the readme are wrong; read them from the data.
7. Two CSVs carry an unnamed index column.
8. Undefined concept → `Not Applicable`.
9. Follow each task's `guidelines` for format (decimals, list separators, units) exactly; the
   scorer is quasi-exact match.
