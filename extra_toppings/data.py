"""Static content: districts, goods, people, rivals, events, raid layouts."""

# ── Contraband ────────────────────────────────────────────────────
# Everything moves in pizza boxes under coded menu names.
GOODS = {
    "oregano": {
        "label": "Extra Oregano",
        "base": 45,          # baseline street price per unit
        "volatility": 0.35,  # daily noise range
        "bulk": 2,           # cargo slots per unit
    },
    "mushrooms": {
        "label": "Special Mushrooms",
        "base": 130,
        "volatility": 0.5,
        "bulk": 1,
    },
    "hot_honey": {
        "label": "Hot Honey",
        "base": 260,
        "volatility": 0.6,
        "bulk": 1,
    },
    "truffle": {
        "label": "White Truffle Powder",
        "base": 950,
        "volatility": 0.8,
        "bulk": 1,
    },
}

# ── Districts ─────────────────────────────────────────────────────
# traffic: legit customer base. underground: covert demand multiplier.
# patrol: baseline enforcement pressure. rival: who claims it.
DISTRICTS = {
    "old_harbor": {
        "label": "Old Harbor",
        "traffic": 0.9,
        "underground": 1.1,
        "patrol": 0.9,
        "rival": "vinnie",
        "flavor": "docks, warehouses, people who don't ask questions",
        "good_bias": {"oregano": 1.2, "truffle": 0.7},
    },
    "university": {
        "label": "University Hill",
        "traffic": 1.3,
        "underground": 1.4,
        "patrol": 1.0,
        "rival": None,
        "flavor": "students, all-nighters, cash-poor and hungry",
        "good_bias": {"oregano": 1.4, "mushrooms": 1.3, "truffle": 0.5},
    },
    "little_sicily": {
        "label": "Little Sicily",
        "traffic": 1.1,
        "underground": 0.6,
        "patrol": 0.8,
        "rival": "sal",
        "flavor": "family tables, church festivals, long memories",
        "good_bias": {"truffle": 1.1, "hot_honey": 0.8},
    },
    "meadows": {
        "label": "The Meadows",
        "traffic": 1.0,
        "underground": 1.5,
        "patrol": 1.2,
        "rival": "vinnie",
        "flavor": "clubs, concert halls, money that comes out after dark",
        "good_bias": {"hot_honey": 1.5, "truffle": 1.4, "oregano": 0.8},
    },
}

HOME_DISTRICT = "old_harbor"  # your shop sits at the edge of Old Harbor

# ── Employees ─────────────────────────────────────────────────────
# Stats 1-10. Trait shapes events. wage is per day, paid in clean cash.
EMPLOYEE_POOL = [
    {
        "name": "Rosa Delgado", "role": "driver",
        "food": 3, "driving": 9, "nerve": 7, "loyalty": 8,
        "trait": "principled", "wage": 90,
        "bio": "Twenty years of deliveries, zero accidents. Doesn't like surprises.",
    },
    {
        "name": "Tony 'Two-Slices' Marino", "role": "cook",
        "food": 8, "driving": 4, "nerve": 5, "loyalty": 6,
        "trait": "greedy", "wage": 100,
        "bio": "Best dough hands in the city. Counts other people's money out loud.",
    },
    {
        "name": "Beatrice 'Bee' Okafor", "role": "counter",
        "food": 5, "driving": 3, "nerve": 4, "loyalty": 7,
        "trait": "observant", "wage": 80,
        "bio": "Ran books for a shipping firm. Notices when numbers don't add up.",
    },
    {
        "name": "Marcus Webb", "role": "driver",
        "food": 2, "driving": 6, "nerve": 8, "loyalty": 4,
        "trait": "reckless", "wage": 60,
        "bio": "Dropped out of University Hill. Drives like he still owes tuition.",
    },
    {
        "name": "Lena Kowalski", "role": "counter",
        "food": 4, "driving": 5, "nerve": 6, "loyalty": 6,
        "trait": "connected", "wage": 85,
        "bio": "Knows a guy in every district. Her rumors are usually right.",
    },
    {
        "name": "Sammy Fetch", "role": "driver",
        "food": 3, "driving": 7, "nerve": 5, "loyalty": 5,
        "trait": "indebted", "wage": 55,
        "bio": "Owes Carmine money too. Works cheap, sweats a lot.",
    },
    {
        "name": "Angelo Ricci", "role": "muscle",
        "food": 2, "driving": 5, "nerve": 9, "loyalty": 7,
        "trait": "known_to_police", "wage": 110,
        "bio": "Did four years upstate and never said a name. Cops remember his face.",
    },
    {
        "name": "Priya Nair", "role": "cook",
        "food": 9, "driving": 2, "nerve": 3, "loyalty": 5,
        "trait": "ambitious", "wage": 105,
        "bio": "Trained in a two-star kitchen. Thinks this place is beneath her. It is.",
    },
]

TRAIT_NOTES = {
    "principled": "won't carry product until read in, and maybe not then",
    "greedy": "skims when loyalty slips; can be bought, by anyone",
    "observant": "spots trouble early — including yours",
    "reckless": "fast routes, hot heat",
    "connected": "improves market rumors",
    "indebted": "cheap and desperate; desperate people talk",
    "known_to_police": "adds heat just by existing; unshakeable nerve",
    "ambitious": "great work, demands raises, remembers slights",
}

# ── Rivals ────────────────────────────────────────────────────────
RIVALS = {
    "sal": {
        "label": "Sal Moretti — Moretti's Trattoria",
        "short": "Sal",
        "home": "little_sicily",
        "aggression": 0.25,   # how readily they escalate
        "violence": 0.1,      # taste for the rough stuff
        "strength": 60,       # organization health
        "style": "Runs a genuinely great restaurant. Fights with prices, poaching "
                 "and quiet words to the right officials. Almost never with fists.",
    },
    "vinnie": {
        "label": "Vinnie 'The Oven' Barzetti — Vinnie's Pies",
        "short": "Vinnie",
        "home": "meadows",
        "aggression": 0.55,
        "violence": 0.7,
        "strength": 70,
        "style": "The pizza is a crime in itself. The business survives on fear, "
                 "extortion and a warehouse full of things that fell off trucks.",
    },
}

# ── City events ───────────────────────────────────────────────────
# Effects apply for `days`. price/traffic/underground are multipliers,
# patrol is additive heat pressure.
EVENTS = [
    {
        "id": "concert",
        "news": "STADIUM SELLS OUT: two-night festival in The Meadows.",
        "district": "meadows", "days": 2,
        "traffic": 1.6, "underground": 1.7, "price": {"hot_honey": 1.5, "truffle": 1.3},
    },
    {
        "id": "port_seizure",
        "news": "CUSTOMS TOUTS RECORD PORT SEIZURE; streets whisper of shortages.",
        "district": None, "days": 3,
        "price": {"truffle": 1.9, "hot_honey": 1.4}, "patrol": 5,
    },
    {
        "id": "crackdown",
        "news": "UNIVERSITY ANNOUNCES CAMPUS SAFETY CRACKDOWN.",
        "district": "university", "days": 3,
        "underground": 0.5, "patrol": 15, "spillover": "meadows",
    },
    {
        "id": "heat_wave",
        "news": "HEAT WAVE: third day above 100°. Nobody wants a hot oven nearby.",
        "district": None, "days": 2,
        "traffic": 0.7, "underground": 1.3,
    },
    {
        "id": "festival",
        "news": "SAINT ROSALIA FESTIVAL fills Little Sicily all weekend.",
        "district": "little_sicily", "days": 2,
        "traffic": 1.7, "patrol": 8,
    },
    {
        "id": "warehouse_robbery",
        "news": "MASKED CREW EMPTIES WAREHOUSE; stolen goods flood the market.",
        "district": None, "days": 2,
        "price": {"oregano": 0.6, "mushrooms": 0.6},
    },
    {
        "id": "payday",
        "news": "DOCKWORKERS SETTLE CONTRACT; back pay lands this week.",
        "district": "old_harbor", "days": 2,
        "traffic": 1.3, "underground": 1.4,
    },
    {
        "id": "food_critic",
        "news": "THE LEDGER'S FOOD CRITIC is touring neighborhood pizzerias.",
        "district": None, "days": 1, "critic": True,
    },
]

# ── Raid system ───────────────────────────────────────────────────
# One layout grammar shared by every tactical location: an ordered room
# path from entry to prize. Rooms carry guard odds and noise risk.
RAID_LAYOUTS = {
    "rival_warehouse": {
        "label": "warehouse",
        "rooms": [
            {"name": "loading dock", "guard": 0.5, "noise": 0.3},
            {"name": "storage floor", "guard": 0.6, "noise": 0.4},
            {"name": "the cage", "guard": 0.7, "noise": 0.5},
            {"name": "back office", "guard": 0.4, "noise": 0.3},
        ],
    },
    "rival_shop": {
        "label": "pizzeria",
        "rooms": [
            {"name": "alley door", "guard": 0.3, "noise": 0.3},
            {"name": "kitchen", "guard": 0.5, "noise": 0.5},
            {"name": "office", "guard": 0.5, "noise": 0.4},
        ],
    },
    "your_shop": {
        "label": "your pizzeria",
        "rooms": [
            {"name": "front door", "guard": 0.0, "noise": 0.4},
            {"name": "kitchen", "guard": 0.0, "noise": 0.5},
            {"name": "office safe", "guard": 0.0, "noise": 0.4},
        ],
    },
}

# The three raid objectives of the vertical slice.
RAID_OBJECTIVES = {
    "steal_stock": {
        "label": "Empty their stockroom",
        "layout": "rival_warehouse",
        "desc": "Take product and cause a shortage they'll feel for days.",
    },
    "ledger": {
        "label": "Photograph the ledger",
        "layout": "rival_shop",
        "desc": "Quiet job. Their books become your leverage — or the law's.",
    },
    "sabotage": {
        "label": "Wreck the ovens",
        "layout": "rival_shop",
        "desc": "No ovens, no pizza, no cover for their routes.",
    },
}

# ── Economy knobs ─────────────────────────────────────────────────
START_CLEAN = 2000
START_DIRTY = 250          # what was left in Enzo's shoe box
START_STASH = {"oregano": 8}  # ...along with eight vacuum-sealed 'spice' bags
START_DEBT = 15000
DEBT_RATE = 0.04          # Carmine's daily interest
DEBT_DUE_DAY = 30
RENT_PER_DAY = 80
WAREHOUSE_RENT = 60
INGREDIENT_COST = {"cheap": 3, "standard": 5, "gourmet": 8}
TICKET_PRICE = {"cheap": 11, "standard": 16, "gourmet": 24}
VEHICLE_CARGO = 24        # cargo slots in the delivery wagon
SHOP_STASH_CAP = 40       # bulk units hideable in the shop
WAREHOUSE_CAP = 200
LAUNDER_FACTOR = 1.25     # dirty $ washable per legit $ of sales

UPGRADES = {
    "walk_in": {
        "label": "Walk-in refrigerator", "cost": 1800,
        "desc": "Doubles shop stash space. Twice as much to lose in a search.",
    },
    "second_oven": {
        "label": "Second deck oven", "cost": 2200,
        "desc": "Raises kitchen capacity by half.",
    },
    "guard": {
        "label": "Night security", "cost": 1200,
        "desc": "Deters raids. A fortified family pizzeria raises eyebrows (+heat).",
    },
    "books": {
        "label": "Creative accounting", "cost": 1500,
        "desc": "Raises the believable-revenue ceiling for laundering.",
    },
    "late_license": {
        "label": "Late-night license", "cost": 900,
        "desc": "Legal 2 a.m. close: more sales, more cover, more complaints.",
    },
}
