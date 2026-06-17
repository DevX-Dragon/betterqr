""""betterqr CLI
============
The cleanest QR code generator in your terminal.

Basic usage:
  betterqr "https://example.com" -> qr.png
  betterqr "Hello World" out.png
  betterqr "https://example.com" out.svg

Micro QR (compact, for small labels):
  betterqr "HELLO" --type micro
  betterqr "12345" --type micro -e L
  betterqr "ABC" --type micro out.png --info

Shapes:
  betterqr "text" -s circle
  betterqr "text" -s rounded
  betterqr "text" -s diamond / star / gapped

Colors:
  betterqr "text" --fill "#6C3082" --back "#F3E8FF"
  betterqr "text" --fill "#000" --back transparent

Gradients:
  betterqr "text" --gradient "#FF6B6B" "#4ECDC4"
  betterqr "text" --gradient "#1d4ed8" "#7c3aed" --gradient-dir radial

Logo:
  betterqr "https://mysite.com" --logo logo.png
  betterqr "https://mysite.com" --logo logo.png --logo-ratio 0.3 -e H

Frame & label:
  betterqr "Scan Me!" --frame rounded --label "Visit our site"
  betterqr "Scan Me!" --frame fancy --label "WiFi Password: abc123"

Animation (saves .gif):
  betterqr "Hello" out.gif --effect shimmer
  betterqr "Hello" out.gif --effect matrix --fps 12
  betterqr "Hello" out.gif --effect wave --frames 30

Data types:
  betterqr --wifi MyNet MyPassword
  betterqr --wifi MyNet MyPassword --security WEP
  betterqr --contact "Jane Doe" --phone "+1-555-0199" --email "jane@example.com"
  betterqr --geo 51.5074 -0.1278
  betterqr --sms "+1-555-0199" "Hello!"
  betterqr --email "hi@example.com" "Subject" "Body text"
  betterqr --phone "+1-800-555-0199"

Terminal preview:
  betterqr "Hello" --print
  betterqr "Hello" --print --invert
"""
import argparse
import os
import sys


def _color(value: str) -> str:
    """V"a"l"idate a color argument."""
    if value.lower() == "transparent":
        return value
    if not value.startswith("#"):
        value = "#" + value
    value = value.lstrip("#")
    if len(value) not in (3, 6):
        raise argparse.ArgumentTypeError(
            f"Invalid color '{value}'. Use hex like #FF0000 or #F00"
        )
    return "#" + value


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="betterqr",
        description="BetterQR - Beautiful, scannable QR codes. Zero external QR dependencies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        add_help=True,
    )

    parser.add_argument("data", nargs="?", help="Data to encode (text, URL, etc.)")
    parser.add_argument(
        "output",
        nargs="?",
        default="qr.png",
        help="Output file (.png .jpg .svg .gif) [default: qr.png]",
    )

    qr_group = parser.add_argument_group("QR settings")
    qr_group.add_argument(
        "--type",
        default="standard",
        choices=["standard", "micro"],
        metavar="TYPE",
        help="QR code type: standard (v1-40) or micro (M1-M4) [default: standard]",
    )
    qr_group.add_argument(
        "-e",
        "--ecc",
        default="M",
        choices=["L", "M", "Q", "H"],
        metavar="L|M|Q|H",
        help="Error correction: L=7%% M=15%% Q=25%% H=30%% [default: M]. Use H with logos. Micro QR supports L/M/Q only.",
    )
    qr_group.add_argument(
        "-v",
        "--version",
        type=int,
        metavar="1-40",
        help="Force QR version (1-40 for standard, 1-4 for micro M1-M4; auto-selected by default)",
    )
    qr_group.add_argument("--box-size", type=int, default=10, metavar="PX", help="Pixels per module [default: 10]")
    qr_group.add_argument("--border", type=int, default=4, metavar="N", help="Quiet zone width in modules [default: 4]")

    style_group = parser.add_argument_group("Style")
    style_group.add_argument(
        "-s",
        "--shape",
        default="square",
        choices=["square", "circle", "rounded", "diamond", "star", "gapped", "vertical_bar", "horizontal_bar"],
        metavar="SHAPE",
        help="Module shape [default: square]\n  square | circle | rounded | diamond | star | gapped | vertical_bar | horizontal_bar",
    )
    style_group.add_argument("--fill", default="#000000", type=_color, metavar="COLOR", help="Dark module color [default: #000000]")
    style_group.add_argument(
        "--back",
        default="#FFFFFF",
        type=_color,
        metavar="COLOR",
        help="Background color [default: #FFFFFF] (use 'transparent' for PNG alpha)",
    )
    style_group.add_argument("--finder", type=_color, metavar="COLOR", help="Separate color for the 3 finder squares")

    gradient_group = parser.add_argument_group("Gradient")
    gradient_group.add_argument(
        "--gradient",
        nargs=2,
        metavar=("START", "END"),
        help="Two colors for a gradient fill. Example: --gradient '#FF6B6B' '#4ECDC4'",
    )
    gradient_group.add_argument(
        "--gradient-dir",
        default="diagonal",
        choices=["horizontal", "vertical", "diagonal", "radial"],
        metavar="DIR",
        help="Gradient direction [default: diagonal]\n  horizontal | vertical | diagonal | radial",
    )

    logo_group = parser.add_argument_group("Logo / image")
    logo_group.add_argument("--logo", metavar="PATH", help="Embed a logo/image in the center of the QR code (PNG/JPG)")
    logo_group.add_argument("--logo-ratio", type=float, default=0.25, metavar="0.1-0.35", help="Logo size as fraction of QR total size [default: 0.25]")
    logo_group.add_argument("--logo-shape", default="square", choices=["square", "circle", "rounded"], help="Logo background shape [default: square]")

    frame_group = parser.add_argument_group("Frame & label")
    frame_group.add_argument("--frame", metavar="STYLE", choices=["simple", "rounded", "double", "shadow", "fancy"], help="Add a decorative frame: simple | rounded | double | shadow | fancy")
    frame_group.add_argument("--frame-color", type=_color, default="#000000", metavar="COLOR", help="Frame color [default: #000000]")
    frame_group.add_argument("--label", metavar="TEXT", help="Text label to add below (or above) the QR code")
    frame_group.add_argument("--label-above", action="store_true", help="Place label above the QR instead of below")
    frame_group.add_argument("--label-color", type=_color, default="#000000", metavar="COLOR")
    frame_group.add_argument("--label-size", type=int, default=14, metavar="PX")

    animation_group = parser.add_argument_group("Animation (saves .gif)")
    animation_group.add_argument(
        "--effect",
        metavar="EFFECT",
        choices=["shimmer", "fade", "scan", "pulse", "build", "matrix", "wave", "blink", "typewriter", "rotate"],
        help="Animation effect:\n  shimmer | fade | scan | pulse | build |\n  matrix  | wave | blink | typewriter | rotate",
    )
    animation_group.add_argument("--frames", type=int, default=20, metavar="N", help="Number of animation frames [default: 20]")
    animation_group.add_argument("--fps", type=int, default=15, metavar="N", help="Animation playback speed [default: 15]")
    animation_group.add_argument("--accent", type=_color, metavar="COLOR", help="Accent color for some animation effects")

    data_group = parser.add_argument_group("Data type shortcuts")
    data_group.add_argument("--wifi", nargs="+", metavar=("SSID", "PASS"), help="Wi-Fi QR: --wifi SSID [PASSWORD]")
    data_group.add_argument("--security", default="WPA", choices=["WPA", "WEP", "nopass"], help="Wi-Fi security type [default: WPA]")
    data_group.add_argument("--contact", metavar="NAME", help="vCard contact QR (use with --phone --email --org --url)")
    data_group.add_argument("--phone", metavar="NUMBER", help="Phone number (for --contact or standalone tel: QR)")
    data_group.add_argument("--email", nargs="+", metavar=("ADDRESS", "SUBJECT"), help="Email QR: --email ADDRESS [SUBJECT] [BODY]")
    data_group.add_argument("--org", metavar="NAME", help="Organization (for --contact)")
    data_group.add_argument("--url", metavar="URL", help="URL (for --contact)")
    data_group.add_argument("--geo", nargs=2, metavar=("LAT", "LON"), help="Location QR: --geo 51.5074 -0.1278")
    data_group.add_argument("--sms", nargs=2, metavar=("PHONE", "MSG"), help="SMS QR: --sms PHONE 'Message body'")

    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--print", action="store_true", help="Print QR to terminal (works alongside file output)")
    output_group.add_argument("--invert", action="store_true", help="Invert terminal colors (for dark-background terminals)")
    output_group.add_argument(
        "--terminal-style",
        default="block",
        choices=["block", "ascii", "compact"],
        help="Terminal render style [default: block]",
    )
    output_group.add_argument("--info", action="store_true", help="Print QR code metadata (version, size, mode, etc.)")

    args = parser.parse_args()

    from .core import QR, WiFi, VCard, GeoLocation, SMS, Email, Phone

    data = None

    if args.wifi:
        ssid = args.wifi[0]
        password = args.wifi[1] if len(args.wifi) > 1 else ""
        data = WiFi(ssid, password, args.security)
    elif args.contact:
        data = VCard(
            name=args.contact,
            phone=args.phone or "",
            email=args.email[0] if args.email else "",
            org=args.org or "",
            url=args.url or "",
        )
    elif args.geo:
        data = GeoLocation(float(args.geo[0]), float(args.geo[1]))
    elif args.sms:
        data = SMS(args.sms[0], args.sms[1])
    elif args.email and not args.contact:
        address = args.email[0]
        subject = args.email[1] if len(args.email) > 1 else ""
        body = args.email[2] if len(args.email) > 2 else ""
        data = Email(address, subject, body)
    elif args.phone and not args.contact:
        data = Phone(args.phone)
    elif args.data:
        data = args.data
    else:
        parser.print_help()
        sys.exit(1)

    try:
        qr = QR(data, ecc=args.ecc, version=args.version, qr_type=args.type)
    except ValueError as error:
        print(f"✗ Error: {error}", file=sys.stderr)
        sys.exit(1)

    if args.gradient:
        qr.gradient(args.gradient[0], args.gradient[1], args.gradient_dir)
    else:
        qr.style(
            fill=args.fill,
            back=args.back,
            shape=args.shape,
            finder=args.finder,
            box_size=args.box_size,
            border=args.border,
        )

    if args.gradient:
        qr._shape = args.shape
        qr._back = args.back
        qr._box_size = args.box_size
        qr._border = args.border
        if args.finder:
            qr._finder_color = args.finder

    if args.logo:
        qr.logo(args.logo, ratio=args.logo_ratio, shape=args.logo_shape)

    if args.frame or args.label:
        qr.frame(
            style=args.frame or "simple",
            color=args.frame_color,
            label=args.label,
            label_color=args.label_color,
            label_size=args.label_size,
            label_position="top" if args.label_above else "bottom",
        )

    if args.effect:
        qr.animate(
            effect=args.effect,
            frames=args.frames,
            fps=args.fps,
            accent=args.accent,
        )
        if not args.output.lower().endswith(".gif"):
            args.output = args.output.rsplit(".", 1)[0] + ".gif"

    if args.info:
        info = qr.info()
        print("QR Code Info")
        print("─" * 30)
        for key, value in info.items():
            print(f"  {key:<14} {value}")
        print()

    if getattr(args, "print"):
        print(qr.to_terminal(style=args.terminal_style, invert=args.invert))

    if args.output:
        try:
            qr.save(args.output)
            print(
                f"✓ Saved {args.output}  "
                f"[{qr.version_label} ECC-{qr.ecc_level}  {qr.module_count}×{qr.module_count} modules]"
            )
        except Exception as error:
            print(f"✗ Failed to save: {error}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
