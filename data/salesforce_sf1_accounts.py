"""Generate fictional Salesforce Accounts for the SF1 data-quality exercise.

The output intentionally contains complete, partial, and inconsistent records.
All names, account numbers, websites, phone numbers, and addresses are invented.
"""

import csv
from pathlib import Path


OUT = Path(__file__).with_name("salesforce_sf1_accounts.csv")
PILOT = Path(__file__).with_name("salesforce_sf1_accounts_pilot.csv")
REMAINDER = Path(__file__).with_name("salesforce_sf1_accounts_remainder.csv")
RETRY = Path(__file__).with_name("salesforce_sf1_accounts_retry.csv")
PENDING = Path(__file__).with_name("salesforce_sf1_accounts_pending.csv")
FIELDS = [
    "Account Name", "Account Number", "Phone", "Fax", "Website", "Account Site",
    "Employees", "Annual Revenue", "Billing Street", "Billing City",
    "Billing State/Province", "Billing Zip/Postal Code", "Billing Country",
    "Shipping Street", "Shipping City", "Shipping State/Province",
    "Shipping Zip/Postal Code", "Shipping Country", "Description",
]

COMPLETE = [
    ("Harborlight Freight", "freight", "Seattle", "WA", "98101"),
    ("Cedar Vale Manufacturing", "manufacturing", "Portland", "OR", "97201"),
    ("Northstar Clinic Systems", "health technology", "Denver", "CO", "80201"),
    ("Lakeshore Retail Group", "retail", "Chicago", "IL", "60601"),
    ("Stonebridge Facilities", "facilities", "Austin", "TX", "73301"),
    ("Juniper Ridge Foods", "food distribution", "Boise", "ID", "83701"),
    ("Bluehaven Utilities", "utilities", "Phoenix", "AZ", "85001"),
    ("Elmcrest Education", "education", "Boston", "MA", "02108"),
    ("Pine Harbor Media", "media", "San Francisco", "CA", "94102"),
    ("Summitfield Engineering", "engineering", "Raleigh", "NC", "27601"),
]
STATE_NAMES = {
    "WA": "Washington", "OR": "Oregon", "CO": "Colorado",
    "IL": "Illinois", "TX": "Texas", "ID": "Idaho", "AZ": "Arizona",
    "MA": "Massachusetts", "CA": "California", "NC": "North Carolina",
}

PARTIAL = [
    "Marlow Office Supplies", "Wattle Creek Farms", "Fairview Repairs",
    "Highland Packaging", "Orchid Bay Travel", "Terrace Dental Group",
    "Willowmere Catering", "Beacon Street Fitness", "Redwood Training",
    "Mosaic Event Services",
]

MIXED = [
    "Bayline  Services", "copperleaf it", "NORTH QUAY STORAGE",
    "Westbrook Co.", "westbrook company", "Acacia & Sons",
    "Meridian Health  Tech", "brightpath logistics", "SouthPier-Print",
    "OAKGLEN SUPPORT",
]

BALANCED = [
    "Kestrel Electrical", "Ironbark Civil Works", "Maplebrook Pharmacy",
    "Cloudline Bookkeeping", "Sunward Equipment Hire", "Greystone Legal Support",
    "Driftwood Furniture", "Parkland Security", "Eucalypt Design Studio",
    "Amberpoint Labs", "Bridgewater Cleaning", "Dunewell Hardware",
    "Foxglove Childcare", "Northgate Veterinary", "Clearwater Landscaping",
    "Hillcrest Mobility", "Silver Fern Hospitality", "Riverton Plumbing",
    "Eastbank Community Arts",
]

assert sum(map(len, (COMPLETE, PARTIAL, MIXED, BALANCED))) == 49


def row(name, **values):
    item = {field: "" for field in FIELDS}
    item["Account Name"] = name
    item.update(values)
    return item


records = []
for i, (name, sector, city, state, postcode) in enumerate(COMPLETE, 1):
    slug = name.lower().replace(" ", "-")
    records.append(row(
        name,
        **{
            "Account Number": f"SF1-C-{i:03d}",
            "Phone": f"+1 202-555-{1000+i:04d}",
            "Fax": f"+1 202-555-{1100+i:04d}",
            "Website": f"https://{slug}.example.com",
            "Account Site": f"{city} operations",
            "Employees": str(35 + i * 11),
            "Annual Revenue": str(750000 + i * 175000),
            "Billing Street": f"{100+i} Example Avenue",
            "Billing City": city,
            "Billing State/Province": STATE_NAMES[state],
            "Billing Zip/Postal Code": postcode,
            "Billing Country": "United States",
            "Shipping Street": f"{200+i} Sample Road",
            "Shipping City": city,
            "Shipping State/Province": STATE_NAMES[state],
            "Shipping Zip/Postal Code": postcode,
            "Shipping Country": "United States",
            "Description": f"Fictional {sector} company. Main office and shipping location are recorded. Account details are deliberately complete for search testing.",
        },
    ))

for i, name in enumerate(PARTIAL, 1):
    details = {}
    if i % 2 == 0:
        details["Phone"] = f"+1 202-555-{1200+i:04d}"
    if i % 3 == 0:
        details["Billing City"] = ["Brisbane", "Perth", "Adelaide"][i % 3]
    if i % 4 == 0:
        details["Description"] = "Fictional company. Intake record is incomplete; business details are awaiting confirmation."
    records.append(row(name, **details))

for i, name in enumerate(MIXED, 1):
    details = {
        "Account Number": f"legacy {i:02d}" if i % 2 else f"MIX-{i:03d}",
        "Description": [
            "Fictional company. Old CRM note says the warehouse is in Brisbane; address has not been checked.",
            "Fictional company. Service team uses an abbreviated trading name in some tickets.",
            "Fictional company. Contact details were copied from an older intake form and need review.",
        ][i % 3],
    }
    if i % 2:
        details["Phone"] = f"202 555 {1300+i:04d}"
    if i % 3 == 0:
        details["Fax"] = f"+1 202-555-{1400+i:04d}"
    if i % 4 == 0:
        details["Website"] = f"https://mixed-{i}.example.com"
    if i % 5 == 0:
        details["Billing City"] = "brisbane"
    records.append(row(name, **details))

for i, name in enumerate(BALANCED, 1):
    details = {
        "Account Number": f"SF1-B-{i:03d}",
        "Website": f"https://business-{i:02d}.example.com",
        "Description": "Fictional company. Routine customer profile for account and case retrieval practice.",
    }
    if i % 2:
        details["Phone"] = f"+1 202-555-{1500+i:04d}"
        details["Billing City"] = ["Seattle", "Austin", "Denver"][i % 3]
        details["Billing Country"] = "United States"
    if i % 3 == 0:
        details["Fax"] = f"+1 202-555-{1600+i:04d}"
        details["Employees"] = str(20 + 7 * i)
    if i % 4 == 0:
        details["Annual Revenue"] = str(400000 + 65000 * i)
        details["Account Site"] = "Operations office"
    records.append(row(name, **details))

assert len(records) == 49
assert len({record["Account Name"].casefold() for record in records}) == 49
for destination, subset in (
    (OUT, records),
    (PILOT, [records[0], records[10], records[20]]),
    (RETRY, [records[0]]),
    (PENDING, [record for index, record in enumerate(records) if index not in (10, 20)]),
    (REMAINDER, [record for index, record in enumerate(records) if index not in (0, 10, 20)]),
):
    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(subset)

print(f"Wrote {len(records)} fictional accounts to {OUT}")
