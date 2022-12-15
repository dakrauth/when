import re
import sys
from dateutil.tz import gettz, tzoffset


ALIASES = {
    "ACDT": [("Australia/Adelaide", "Australian Central Daylight Time")],
    "ACST": [("Australia/Adelaide", "Australian Central Standard Time")],
    "ACT": [(28800, "ASEAN Common Time"), (-18000, "Acre Time")],
    "ACWST": [(31500, "Australian Central Western Standard Time")],
    "ADT": [
        ("Atlantic/Bermuda", "Atlantic Daylight Time"),
        ("Asia/Baku", "Azerbaijan Standard Time"),
        ("Atlantic/Azores", "Azores Standard Time"),
    ],
    "AEDT": [("Australia/Sydney", "Australian Eastern Daylight Time")],
    "AEST": [("Australia/Sydney", "Australian Eastern Standard Time")],
    "AET": [(36000, "Australian Eastern Time")],
    "AFT": [(16200, "Afghanistan Time")],
    "AKDT": [("US/Alaska", "Alaskan Daylight Time")],
    "AKST": [("US/Alaska", "Alaskan Standard Time")],
    "ALMT": [(21600, "Alma-Ata Time")],
    "AMST": [(-10800, "Amazon Summer Time")],
    "AMT": [(-14400, "Amazon Time"), (14400, "Armenia Time")],
    "ANAT": [(43200, "Anadyr Time")],
    "AQTT": [(18000, "Aqtobe Time")],
    "ART": [(-10800, "Argentina Time")],
    "AST": [
        ("Atlantic/Bermuda", "Atlantic Standard Time"),
        ("Asia/Kabul", "Afghanistan Standard Time"),
        ("Asia/Riyadh", "Arabia Standard Time"),
        ("America/Buenos_Aires", "Argentina Standard Time"),
    ],
    "AWST": [("Australia/West", "Australian Western Standard Time")],
    "AZOST": [(0, "Azores Summer Time")],
    "AZOT": [(-3600, "Azores Standard Time")],
    "AZT": [(14400, "Azerbaijan Time")],
    "BIOT": [(21600, "British Indian Ocean Time")],
    "BIT": [(-43200, "Baker Island Time")],
    "BNT": [(28800, "Brunei Time")],
    "BOT": [(-14400, "Bolivia Time")],
    "BRST": [(-7200, "Brasília Summer Time")],
    "BRT": [(-10800, "Brasília Time")],
    "BST": [
        ("GB", "British Summer Time"),
        ("America/Bahia", "Bahia Standard Time"),
        ("Asia/Dhaka", "Bangladesh Standard Time"),
        (39600, "Bougainville Standard Time"),
    ],
    "BTT": [(21600, "Bhutan Time")],
    "CAST": [
        ("America/Costa_Rica", "Central America Standard Time"),
        ("Asia/Almaty", "Central Asia Standard Time"),
        ("Australia/Adelaide", "Central Australia Standard Time"),
    ],
    "CAT": [("Africa/Windhoek", "Central Africa Time"), (7200, "Central Africa Time")],
    "CBST": [("America/Campo_Grande", "Central Brazilian Standard Time")],
    "CCST": [("America/Regina", "Canada Central Standard Time")],
    "CCT": [(23400, "Cocos Islands Time")],
    "CDT": [("US/Central", "Central Daylight Time"), (-14400, "Cuba Daylight Time")],
    "CEDT": [("CET", "Central Europe Standard Time")],
    "CEST": [("CET", "Central Europe Standard Time")],
    "CET": [(3600, "Central European Time")],
    "CHADT": [(49500, "Chatham Daylight Time")],
    "CHAST": [(45900, "Chatham Standard Time")],
    "CHOST": [(32400, "Choibalsan Summer Time")],
    "CHOT": [(28800, "Choibalsan Standard Time")],
    "CHST": [("Pacific/Guam", "Chamorro Time Zone")],
    "CHUT": [(36000, "Chuuk Time")],
    "CIST": [(-28800, "Clipperton Island Standard Time")],
    "CKT": [(-36000, "Cook Island Time")],
    "CLST": [(-10800, "Chile Summer Time")],
    "CLT": [(-14400, "Chile Standard Time")],
    "COST": [(-14400, "Colombia Summer Time")],
    "COT": [(-18000, "Colombia Time")],
    "CPST": [("Pacific/Guadalcanal", "Central Pacific Standard Time")],
    "CST": [
        ("US/Central", "Central Standard Time"),
        ("Asia/Yerevan", "Caucasus Standard Time"),
        ("Asia/Shanghai", "China Standard Time"),
        ("Cuba", "Cuba Standard Time"),
    ],
    "CT": [("US/Central", "Central Standard Time")],
    "Central": [("US/Central", "Central Standard Time")],
    "CVST": [("Atlantic/Cape_Verde", "Cape Verde Standard Time")],
    "CVT": [(-3600, "Cape Verde Time")],
    "CWST": [(31500, "Central Western Standard Time (Australia) unofficial")],
    "CXT": [(25200, "Christmas Island Time")],
    "DAVT": [(25200, "Davis Time")],
    "DDUT": [(36000, "Dumont d'Urville Time")],
    "DFT": [(3600, "AIX-specific equivalent of Central European Time")],
    "DST": [("Etc/GMT+12", "Dateline Standard Time")],
    "EASST": [(-18000, "Easter Island Summer Time")],
    "EAST": [
        ("Australia/Brisbane", "E. Australia Standard Time"),
        ("Africa/Addis_Ababa", "East Africa Standard Time"),
        (-21600, "Easter Island Standard Time"),
    ],
    "EAT": [("Africa/Addis_Ababa", "East Africa Time")],
    "ECT": [(-14400, "Eastern Caribbean Time"), (-18000, "Ecuador Time")],
    "EDT": [("US/Eastern", "Eastern Daylight Time")],
    "EEDT": [("EET", "Eastern Europe Summer Time")],
    "EEST": [("EET", "Eastern European Summer Time")],
    "EET": [(7200, "Eastern European Time")],
    "EGST": [(0, "Eastern Greenland Summer Time")],
    "EGT": [(-3600, "Eastern Greenland Time")],
    "ESAST": [("America/Sao_Paulo", "Eastern South America Standard Time")],
    "EST": [
        ("US/Eastern", "Eastern Standard Time"),
        ("Africa/Cairo", "Egypt Standard Time"),
    ],
    "ET": [("US/Eastern", "Eastern Standard Time")],
    "Eastern": [("US/Eastern", "Eastern Standard Time")],
    "FDT": [("Europe/Helsinki", "FLE Standard Time")],
    "FET": [(10800, "Further-eastern European Time")],
    "FJT": [(43200, "Fiji Time")],
    "FKST": [(-10800, "Falkland Islands Summer Time")],
    "FKT": [(-14400, "Falkland Islands Time")],
    "FNT": [(-7200, "Fernando de Noronha Time")],
    "FST": [("Pacific/Fiji", "Fiji Standard Time")],
    "GALT": [(-21600, "Galápagos Time")],
    "GAMT": [(-32400, "Gambier Islands Time")],
    "GDT": [
        ("Europe/Lisbon", "GMT Standard Time"),
        ("Europe/Athens", "GTB Standard Time"),
        ("America/Godthab", "Greenland Standard Time"),
    ],
    "GET": [("Asia/Tbilisi", "Georgian Standard Time")],
    "GFT": [(-10800, "French Guiana Time")],
    "GILT": [(43200, "Gilbert Island Time")],
    "GIT": [(-32400, "Gambier Island Time")],
    "GMT": [(0, "Greenwich Mean Time")],
    "GST": [
        ("Atlantic/Reykjavik", "Greenwich Standard Time"),
        (14400, "Gulf Standard Time"),
        (-7200, "South Georgia and the South Sandwich Islands Time"),
    ],
    "GYT": [(-14400, "Guyana Time")],
    "HAEC": [(7200, "Heure Avancée d'Europe Centrale")],
    "HDT": [("US/Aleutian", "Hawaiian–Aleutian Daylight Time")],
    "HKT": [("Hongkong", "Hong Kong Time"), (28800, "Hong Kong Time")],
    "HMT": [(18000, "Heard and McDonald Islands Time")],
    "HOVST": [(28800, "Hovd Summer Time")],
    "HOVT": [(25200, "Hovd Time")],
    "HST": [("US/Hawaii", "Hawaiian Standard Time")],
    "ICT": [(25200, "Indochina Time")],
    "IDLW": [(-43200, "International Day Line West time zone")],
    "IDT": [
        ("Israel", "Israel Daylight Time"),
        ("Asia/Tehran", "Iran Standard Time"),
    ],
    "IOT": [(10800, "Indian Ocean Time")],
    "IRDT": [(16200, "Iran Daylight Time")],
    "IRKT": [(28800, "Irkutsk Time")],
    "IRST": [(12600, "Iran Standard Time")],
    "IST": [
        ("Europe/Dublin", "Irish Standard Time"),
        ("Asia/Calcutta", "India Standard Time"),
        ("Israel", "Israel Standard Time"),
    ],
    "JDT": [("Asia/Jerusalem", "Israel Standard Time")],
    "JST": [
        ("Asia/Tokyo", "Japan Standard Time"),
        ("Asia/Amman", "Jordan Standard Time"),
    ],
    "KALT": [(7200, "Kaliningrad Time")],
    "KDT": [("Asia/Kamchatka", "Kamchatka Standard Time")],
    "KGT": [(21600, "Kyrgyzstan Time")],
    "KOST": [(39600, "Kosrae Time")],
    "KRAT": [(25200, "Krasnoyarsk Time")],
    "KST": [
        ("Asia/Seoul", "Korea Standard Time"),
        ("Europe/Kaliningrad", "Kaliningrad Standard Time"),
    ],
    "LHST": [(37800, "Lord Howe Standard Time")],
    "LHDT": [(39600, "Lord Howe Summer Time")],
    "LINT": [(50400, "Line Islands Time")],
    "LST": [("Africa/Tripoli", "Libya Standard Time")],
    "MAGT": [(43200, "Magadan Time")],
    "MART": [(-3348000, "Marquesas Islands Time")],
    "MAWT": [(18000, "Mawson Station Time")],
    "MDT": [
        ("US/Mountain", "Mountain Daylight Time"),
        ("Africa/Casablanca", "Morocco Standard Time"),
    ],
    "MEDT": [("Asia/Beirut", "Middle East Standard Time")],
    "MEST": [("MET", "Middle European Summer Time")],
    "MET": [("MET", "Middle European Time"), (3600, "Middle European Time")],
    "MHT": [(43200, "Marshall Islands Time")],
    "MIST": [(39600, "Macquarie Island Station Time")],
    "MIT": [(-3348000, "Marquesas Islands Time")],
    "MMT": [(23400, "Myanmar Standard Time")],
    "MPST": [("Asia/Singapore", "Singapore Standard Time")],
    "MSK": [("Europe/Moscow", "Moscow Standard Time")],
    "MST": [
        ("US/Mountain", "Mountain Standard Time"),
        (28800, "Malaysia Standard Time"),
        ("Asia/Magadan", "Magadan Standard Time"),
        ("Indian/Mauritius", "Mauritius Standard Time"),
        ("America/Montevideo", "Montevideo Standard Time"),
        ("Asia/Rangoon", "Myanmar Standard Time"),
    ],
    "MT": [("US/Mountain", "Mountain Standard Time")],
    "Mountain": [("US/Mountain", "Mountain Standard Time")],
    "MUT": [(14400, "Mauritius Time")],
    "MVT": [(18000, "Maldives Time")],
    "MYT": [(28800, "Malaysia Time")],
    "NAEST": [("Asia/Irkutsk", "North Asia East Standard Time")],
    "NAST": [("Asia/Krasnoyarsk", "North Asia Standard Time")],
    "NCAST": [("Asia/Novosibirsk", "North Central Asia Standard Time")],
    "NCT": [(39600, "New Caledonia Time")],
    "NDT": [("Canada/Newfoundland", "Newfoundland Daylight Time")],
    "NFT": [(39600, "Norfolk Island Time")],
    "NOVT": [(25200, "Novosibirsk Time ")],
    "NPT": [(20700, "Nepal Time")],
    "NST": [
        ("Canada/Newfoundland", "Newfoundland Standard Time"),
        ("Africa/Windhoek", "Namibia Standard Time"),
        ("Asia/Kathmandu", "Nepal Standard Time"),
    ],
    "NT": [(-1188000, "Newfoundland Time")],
    "NUT": [(-39600, "Niue Time")],
    "NZDT": [("NZ", "New Zealand Daylight Time")],
    "NZST": [("NZ", "New Zealand Standard Time")],
    "OMST": [(21600, "Omsk Time")],
    "ORAT": [(18000, "Oral Time")],
    "PDT": [("US/Pacific", "Pacific Daylight Time")],
    "PET": [(-18000, "Peru Time")],
    "PETT": [(43200, "Kamchatka Time")],
    "PGT": [(36000, "Papua New Guinea Time")],
    "PHOT": [(46800, "Phoenix Island Time")],
    "PHST": [(28800, "Philippine Standard Time")],
    "PHT": [(28800, "Philippine Time")],
    "PKT": [("Asia/Karachi", "Pakistan Standard Time")],
    "PMDT": [(-7200, "Saint Pierre and Miquelon Daylight Time")],
    "PMST": [(-10800, "Saint Pierre and Miquelon Standard Time")],
    "PONT": [(39600, "Pohnpei Standard Time")],
    "PSST": [("America/Santiago", "Pacific SA Standard Time")],
    "PST": [("US/Pacific", "Pacific Standard Time")],
    "PT": [("US/Pacific", "Pacific Standard Time")],
    "Pacific": [("US/Pacific", "Pacific Standard Time")],
    "PWT": [(32400, "Palau Time")],
    "PYST": [(-10800, "Paraguay Summer Time")],
    "PYT": [("America/Asuncion", "Paraguay Standard Time")],
    "RDT": [("Europe/Brussels", "Romance Standard Time")],
    "RET": [(14400, "Réunion Time")],
    "ROTT": [(-10800, "Rothera Research Station Time")],
    "SAKT": [(39600, "Sakhalin Island Time")],
    "SAMT": [("Europe/Samara", "Samara Time")],
    "SAST": [
        ("Africa/Johannesburg", "South Africa Standard Time"),
        ("Asia/Jakarta", "SE Asia Standard Time"),
    ],
    "SBT": [(39600, "Solomon Islands Time")],
    "SCT": [(14400, "Seychelles Time")],
    "SDT": [(-36000, "Samoa Daylight Time"), ("Asia/Damascus", "Syria Standard Time")],
    "SEST": [("America/Cayenne", "SA Eastern Standard Time")],
    "SGT": [(28800, "Singapore Time")],
    "SLST": [("Asia/Colombo", "Sri Lanka Standard Time")],
    "SPST": [("America/Bogota", "South America Pacific Standard Time")],
    "SRET": [(39600, "Srednekolymsk Time")],
    "SRT": [(-10800, "Suriname Time")],
    "SST": [("US/Samoa", "Samoa Standard Time"), (28800, "Singapore Standard Time")],
    "SWST": [("America/Anguilla", "SA Western Standard Time")],
    "SYOT": [(10800, "Showa Station Time")],
    "TAHT": [(-36000, "Tahiti Time")],
    "TDT": [("Europe/Istanbul", "Turkey Standard Time")],
    "TFT": [(18000, "French Southern and Antarctic Time")],
    "THA": [(25200, "Thailand Standard Time")],
    "TJT": [(18000, "Tajikistan Time")],
    "TKT": [(46800, "Tokelau Time")],
    "TLT": [(32400, "Timor Leste Time")],
    "TMT": [(18000, "Turkmenistan Time")],
    "TOT": [(46800, "Tonga Time")],
    "TRT": [(10800, "Turkey Time")],
    "TST": [
        ("Asia/Taipei", "Taipei Standard Time"),
        ("Australia/Hobart", "Tasmania Standard Time"),
        ("Pacific/Tongatapu", "Tonga Standard Time"),
    ],
    "TVT": [(43200, "Tuvalu Time")],
    "UEDT": [("America/Indianapolis", "US Eastern Standard Time")],
    "ULAST": [(32400, "Ulaanbaatar Summer Time")],
    "ULAT": [(28800, "Ulaanbaatar Standard Time")],
    "UST": [("Asia/Ulaanbaatar", "Ulaanbaatar Standard Time")],
    "UYST": [(-7200, "Uruguay Summer Time")],
    "UYT": [(-10800, "Uruguay Standard Time")],
    "UZT": [(18000, "Uzbekistan Time")],
    "VET": [(-14400, "Venezuelan Standard Time")],
    "VLAT": [(36000, "Vladivostok Time")],
    "VOLT": [(10800, "Volgograd Time")],
    "VOST": [(21600, "Vostok Station Time")],
    "VST": [
        ("America/Caracas", "Venezuela Standard Time"),
        ("Asia/Vladivostok", "Vladivostok Standard Time"),
    ],
    "VUT": [(39600, "Vanuatu Time")],
    "WAKT": [(43200, "Wake Island Time")],
    "WAST": [
        ("Australia/Perth", "W. Australia Standard Time"),
        (7200, "West Africa Summer Time"),
        ("Asia/Tashkent", "West Asia Standard Time"),
    ],
    "WAT": [("Africa/Kinshasa", "West Africa Time")],
    "WCAST": [("Africa/Kinshasa", "West Central Africa Standard Time")],
    "WEDT": [("WET", "Western Europe Summer Time")],
    "WEST": [("WET", "Western European Summer Time")],
    "WET": [("WET", "Western European Time")],
    "WGST": [(-7200, "West Greenland Summer Time")],
    "WGT": [(-10800, "West Greenland Time")],
    "WIB": [("Asia/Jakarta", "Western Indonesia Time")],
    "WIT": [("Asia/Jayapura", "Eastern Indonesia Time")],
    "WITA": [("Asia/Makassar", "Central Indonesia Time")],
    "WPST": [("Pacific/Guam", "West Pacific Standard Time")],
    "WST": [(28800, "Western Standard Time")],
    "YAKT": [(32400, "Yakutsk Time")],
    "YEKT": [("Asia/Yekaterinburg", "Yekaterinburg Time")],
    "YST": [("Asia/Yakutsk", "Yakutsk Standard Time")],
}


class Zones:
    def __init__(self, abbrs):
        self.abbrs = {k.lower(): v for k,v in abbrs.items()}
        self._cached = {}
        self.utc_offset_re = re.compile(r"^UTC[+±-]\d\d?(:\d\d)$", re.IGNORECASE)

    def get(self, abbr):
        lower = abbr.lower()
        utc_offset_match = False
        if lower not in self.abbrs:
            utc_offset_match = self.utc_offset_re.match(abbr)
            if not utc_offset_match:
                return []

        if lower not in self._cached:
            values = []
            if utc_offset_match:
                values.append((gettz(abbr), abbr.upper()))
            else:
                for value, name in self.abbrs[lower]:
                    values.append(
                        (
                            gettz(value)
                            if isinstance(value, str)
                            else tzoffset(name, value),
                            name,
                        )
                    )

            self._cached[lower] = values

        return self._cached[lower]


zones = Zones(ALIASES)


def main():
    args = sys.argv[1:]
    if not args:
        return "No zones specified"

    for arg in args:
        for tz, name in zones.get(arg):
            print(f"{name:.<40}{tz}")


if __name__ == "__main__":
    sys.exit(main())
