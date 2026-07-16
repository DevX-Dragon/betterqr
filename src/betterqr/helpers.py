import os
import re


def _escape_wifi_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,")


def wifi_string(ssid: str, password: str, security: str = "WPA", hidden: bool = False) -> str:
    """
    Generates a formatted Wi-Fi configuration string for QR codes.
    """
    if not ssid or not isinstance(ssid, str):
        raise ValueError("SSID cannot be empty.")

    security = security.upper()
    if security not in ("WPA", "WEP", "NOPASS"):
        raise ValueError("Security must be 'WPA', 'WEP', or 'nopass'.")

    if security == "WPA" and (not password or len(password) < 8):
        raise ValueError("WPA password must be at least 8 characters long.")
    _WEP_HEX_LENGTHS = (10, 26, 32, 58)
    _WEP_ASCII_LENGTHS = (5, 13, 16, 29)
    if security == "WEP" and password:
        is_valid_hex = len(password) in _WEP_HEX_LENGTHS and re.fullmatch(r"[0-9A-Fa-f]+", password)
        is_valid_ascii = len(password) in _WEP_ASCII_LENGTHS
        if not (is_valid_hex or is_valid_ascii):
            raise ValueError(
                "WEP password must be a 5/13/16/29-character passphrase "
                "or a 10/26/32/58-digit hexadecimal key."
            )
    if security == "NOPASS":
        password = ""

    ssid = _escape_wifi_value(ssid)
    password = _escape_wifi_value(password)
    security_value = "nopass" if security == "NOPASS" else security

    wifi_str = f"WIFI:S:{ssid};T:{security_value};P:{password};"
    if hidden:
        wifi_str += "H:true;"
    wifi_str += ";"
    return wifi_str


class WiFi:
    def __init__(self, ssid: str, password: str = "", security: str = "WPA", hidden: bool = False):
        if not ssid:
            raise ValueError("SSID cannot be empty")
        security = security.upper()
        if security not in ("WPA", "WEP", "NOPASS", ""):
            security = "WPA"
        self._ssid = ssid
        self._password = password
        self._security = security
        self._hidden = hidden

    def __str__(self) -> str:
        return wifi_string(self._ssid, self._password, self._security or "NOPASS", self._hidden)


class VCard:
    def __init__(self, name: str, org: str = "", phone: str = "", email: str = "", url: str = "", address: str = "", note: str = ""):
        if not name:
            raise ValueError("name is required")
        self.name = name
        self.org = org
        self.phone = phone
        self.email = email
        self.url = url
        self.address = address
        self.note = note

    def __str__(self) -> str:
        lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{self.name}", f"N:{self.name};;;;"]
        if self.org:
            lines.append(f"ORG:{self.org}")
        if self.phone:
            lines.append(f"TEL:{self.phone}")
        if self.email:
            lines.append(f"EMAIL:{self.email}")
        if self.url:
            lines.append(f"URL:{self.url}")
        if self.address:
            lines.append(f"ADR:{self.address}")
        if self.note:
            lines.append(f"NOTE:{self.note}")
        lines.append("END:VCARD")
        return "\n".join(lines)


class MeCard:
    def __init__(self, name: str, phone: str = "", email: str = "", url: str = "", birthday: str = "", note: str = ""):
        if not name:
            raise ValueError("name is required")
        self.name = name
        self.phone = phone
        self.email = email
        self.url = url
        self.birthday = birthday
        self.note = note

    def __str__(self) -> str:
        parts = [f"N:{self.name}"]
        if self.phone:
            parts.append(f"TEL:{self.phone}")
        if self.email:
            parts.append(f"EMAIL:{self.email}")
        if self.url:
            parts.append(f"URL:{self.url}")
        if self.birthday:
            parts.append(f"BDAY:{self.birthday}")
        if self.note:
            parts.append(f"MEMO:{self.note}")
        return "MECARD:" + ";".join(parts) + ";;"


class GeoLocation:
    def __init__(self, lat: float, lon: float, altitude: float | None = None):
        self.lat = lat
        self.lon = lon
        self.alt = altitude

    def __str__(self) -> str:
        value = f"geo:{self.lat},{self.lon}"
        if self.alt is not None:
            value += f",{self.alt}"
        return value


class Event:
    def __init__(self, summary: str, dtstart: str, dtend: str, location: str = "", description: str = ""):
        self.summary = summary
        self.dtstart = dtstart
        self.dtend = dtend
        self.location = location
        self.description = description

    def __str__(self) -> str:
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "BEGIN:VEVENT",
            f"SUMMARY:{self.summary}",
            f"DTSTART:{self.dtstart}",
            f"DTEND:{self.dtend}",
        ]
        if self.location:
            lines.append(f"LOCATION:{self.location}")
        if self.description:
            lines.append(f"DESCRIPTION:{self.description}")
        lines += ["END:VEVENT", "END:VCALENDAR"]
        return "\n".join(lines)


class SMS:
    def __init__(self, phone: str, body: str = ""):
        self.phone = phone
        self.body = body

    def __str__(self) -> str:
        return f"smsto:{self.phone}:{self.body}" if self.body else f"sms:{self.phone}"


class Email:
    def __init__(self, address: str, subject: str = "", body: str = ""):
        self.address = address
        self.subject = subject
        self.body = body

    def __str__(self) -> str:
        params = []
        if self.subject:
            params.append(f"subject={self.subject}")
        if self.body:
            params.append(f"body={self.body}")
        base = f"mailto:{self.address}"
        return base + ("?" + "&".join(params) if params else "")


class Phone:
    def __init__(self, number: str):
        self.number = number

    def __str__(self) -> str:
        return f"tel:{self.number}"


class Crypto:
    def __init__(self, coin: str, address: str, amount: float | None = None, label: str = "", message: str = ""):
        self.coin = coin.lower()
        self.address = address
        self.amount = amount
        self.label = label
        self.message = message

    def __str__(self) -> str:
        params = []
        if self.amount is not None:
            params.append(f"amount={self.amount}")
        if self.label:
            params.append(f"label={self.label}")
        if self.message:
            params.append(f"message={self.message}")
        base = f"{self.coin}:{self.address}"
        return base + ("?" + "&".join(params) if params else "")


def batch(items: list, output_dir: str = ".", prefix: str = "qr", **style_kwargs) -> list:
    from .core import QR

    os.makedirs(output_dir, exist_ok=True)
    results = []
    for index, item in enumerate(items):
        if isinstance(item, tuple):
            data, filename = item
        else:
            data, filename = item, f"{prefix}_{index}.png"
        qr = QR(data)
        if style_kwargs:
            qr.style(**style_kwargs)
        qr.save(os.path.join(output_dir, filename))
        results.append(qr)
    return results


__all__ = [
    "wifi_string",
    "WiFi",
    "VCard",
    "MeCard",
    "GeoLocation",
    "Event",
    "SMS",
    "Email",
    "Phone",
    "Crypto",
    "batch",
]
