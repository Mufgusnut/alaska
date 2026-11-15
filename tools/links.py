"""Stamp the auto-linker's LINKS list into every page.

Usage:  python tools/links.py          (run from the repo root, after tools/nav.py)

The last <script> on each page turns names of hotels, restaurants, sights, ships and ports
into links. Eurodam and comparison pages keep their list (with "Koningsdam" pointing at the
Koningsdam section); pages under koningsdam/ get the Vancouver / Koningsdam list below.
Safe to re-run.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HAL = "https://www.hollandamerica.com/en/us/"
DINE = HAL + "onboard-experiences/dining/"
BARS = HAL + "onboard-experiences/bars-and-lounges/"
ENT = HAL + "onboard-experiences/entertainment/"
ACT = HAL + "onboard-experiences/activities/"

BLOCK = re.compile(r"(const LINKS = \[)(.*?)(\r?\n  \];)", re.S)

# Dropped from the Koningsdam list: Seattle places and the Eurodam port pages it replaces.
DROP_PREFIXES = ("https://www.edgewaterhotel.com", "https://www.fourseasons.com/seattle", "https://www.fairmont.com/seattle",
                 "https://innatthemarket.com", "https://mayflowerpark.com", "https://hotelandra.com", "https://www.palladianhotel.com",
                 "https://www.mediterranean-inn.com", "https://canlis.com", "https://www.thepinkdoor.net", "https://www.mattsinthemarket.com",
                 "https://www.elliottsoysterhouse.com", "https://sushikashiba.com", "https://www.ivars.com", "https://www.pikeplacechowder.com",
                 "https://www.pikeplacefish.com", "https://www.goldfinchtavern.com", "https://www.cafecampagne.com",
                 "https://www.pikeplacemarket.org", "https://waterfrontparkseattle.org", "https://www.seattleaquarium.org",
                 "https://seattlegreatwheel.com", "https://www.argosycruises.com", "https://www.spaceneedle.com",
                 "https://www.chihulygardenandglass.com", "https://www.seattle.gov", "https://www.soundtransit.org",
                 "https://www.portseattle.org")
DROP_NAMES = {"Juneau", "Glacier Bay", "Ketchikan", "Victoria", "Eurodam", "Morimoto by Sea"}

K_LINKS = [
    # Ports in the Koningsdam section
    ["Juneau", "/koningsdam/juneau/"], ["Skagway", "/koningsdam/skagway/"],
    ["Glacier Bay", "/koningsdam/glacier-bay/"], ["Ketchikan", "/koningsdam/ketchikan/"],
    ["Eurodam", "/"], ["Koningsdam", HAL + "cruise-ships/koningsdam"],
    # Vancouver hotels
    ["Pan Pacific Vancouver", "https://www.panpacific.com/en/hotels-and-resorts/pp-vancouver.html"],
    ["Pan Pacific", "https://www.panpacific.com/en/hotels-and-resorts/pp-vancouver.html"],
    ["Fairmont Waterfront", "https://www.fairmont.com/en/hotels/vancouver/fairmont-waterfront.html"],
    ["Fairmont Pacific Rim", "https://www.fairmont.com/en/hotels/vancouver/fairmont-pacific-rim.html"],
    ["Fairmont Hotel Vancouver", "https://www.fairmont.com/en/hotels/vancouver/fairmont-hotel-vancouver.html"],
    ["Rosewood Hotel Georgia", "https://www.rosewoodhotels.com/en/hotel-georgia-vancouver"],
    ["Wedgewood Hotel", "https://www.wedgewoodhotel.com/"],
    ["EXchange Hotel", "https://www.exchangehotelvan.com/"],
    ["Pinnacle Hotel Harbourfront", "https://www.pinnacleharbourfronthotel.com/"],
    ["Days Inn by Wyndham Vancouver Downtown", "https://www.daysinnvancouver.com/"],
    ["Coast Coal Harbour", "https://www.coasthotels.com/coast-coal-harbour-vancouver-hotel-by-apa"],
    ["Fairmont Vancouver Airport", "https://www.fairmont.com/en/hotels/vancouver/fairmont-vancouver-airport.html"],
    # Vancouver restaurants
    ["Five Sails", "https://www.fivesails.ca/"], ["Miku", "https://mikurestaurant.com/"],
    ["Botanist", "https://www.botanistrestaurant.com/"], ["Blue Water Cafe", "https://www.bluewatercafe.net/"],
    ["Teahouse in Stanley Park", "https://www.vancouverdine.com/teahouse"],
    ["Cardero's", "https://www.vancouverdine.com/carderos"],
    ["Cactus Club Cafe", "https://www.cactusclubcafe.com/location/coal-harbour/"],
    # Vancouver sights & transport
    ["Canada Place", "https://www.canadaplace.ca/"], ["FlyOver", "https://www.flyovercanada.com/"],
    ["Vancouver Lookout", "https://vancouverlookout.com/"],
    ["Stanley Park", "https://vancouver.ca/parks-recreation-culture/stanley-park.aspx"],
    ["Vancouver Aquarium", "https://www.vanaqua.org/"], ["Granville Island", "https://granvilleisland.com/"],
    ["Aquabus", "https://theaquabus.com/"], ["Gastown", "https://gastown.org/"],
    ["Capilano Suspension Bridge Park", "https://www.capbridge.com/"],
    ["Dr. Sun Yat-Sen Classical Chinese Garden", "https://vancouverchinesegarden.com/"],
    ["Canada Line", "https://www.translink.ca/schedules-and-maps/skytrain"],
    ["Air Canada", "https://www.aircanada.com/"],
    # Koningsdam on board
    ["Sel de Mer", DINE + "sel-de-mer"], ["Canaletto", DINE + "canaletto"],
    ["Morimoto by Sea", DINE + "morimoto-by-sea"],
    ["Grand Dutch Café", DINE + "grand-dutch-cafe"], ["Grand Dutch Cafe", DINE + "grand-dutch-cafe"],
    ["Club Orange", DINE + "club-orange"], ["Lido Market", DINE + "lido-market"],
    ["Crow's Nest", BARS + "crows-nest"], ["Ocean Bar", BARS + "ocean-bar"],
    ["World Stage", ENT + "world-stage"], ["B.B. King's Blues Club", ENT + "bb-kings-blues-club"],
    ["Greenhouse Spa", ACT + "greenhouse-spa-salon"],
    # Skagway & the Yukon
    ["Red Onion Saloon", "https://www.redonion1898.com/"], ["Days of '98 Show", "https://thedaysof98show.com"],
    ["Skagway Museum", "https://www.skagway.org/museum"],
]


def parse(body):
    lines = [ln for ln in body.splitlines() if not ln.strip().startswith("//")]
    return json.loads("[" + "\n".join(lines).rstrip().rstrip(",") + "]")


def render(pairs, nl):
    rows = ["    " + json.dumps(p, ensure_ascii=False) for p in pairs]
    return nl + ("," + nl).join(rows)


def main():
    home = (ROOT / "index.html").read_bytes().decode("utf-8")
    base = parse(BLOCK.search(home).group(2))
    eurodam = [[n, "/koningsdam/" if n == "Koningsdam" else u] for n, u in base]
    kept = [[n, u] for n, u in base if n not in DROP_NAMES and not u.startswith(DROP_PREFIXES)]
    have = {n for n, _ in K_LINKS}
    koningsdam = K_LINKS + [p for p in kept if p[0] not in have]
    bad = 0
    for path in sorted(ROOT.rglob("index.html")):
        folder = path.parent.relative_to(ROOT).as_posix()
        src = path.read_bytes().decode("utf-8")
        if "const LINKS = [" not in src:
            print("no auto-linker:", folder)
            continue
        nl = "\r\n" if "\r\n" in src else "\n"
        pairs = koningsdam if folder.startswith("koningsdam") else eurodam
        out, n = BLOCK.subn(lambda m: m.group(1) + render(pairs, nl) + m.group(3), src, count=1)
        if not n:
            print("FAILED:", folder)
            bad += 1
            continue
        if out != src:
            path.write_bytes(out.encode("utf-8"))
        print(f"ok  /{'' if folder == '.' else folder + '/'}  ({len(pairs)} links)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
